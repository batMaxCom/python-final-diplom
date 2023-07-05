from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from django.utils import timezone

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from backend.serializers import CategoriesSerializer, ProductInfoSerializer, ShopSerializer, \
    OrderItemSerializer, OrderSerializer, OrderListSerializer, ProductInfoListSerializer
from backend.models import Category, Shop, ProductInfo, Product, ProductParameter, Parameter, Order, OrderItem
from backend.utils import update_state_message

import yaml
import os



class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategoriesSerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра магазинов
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class ProductView(ListAPIView):
    """
    Класс для просмотра продуктов, с возможность сортировки по магазину или категории
    TODO: Нужна ли при просмотре каталога сокращеная форма отображения? А при просмотре позиций полная?
    """
    serializer_class = ProductInfoListSerializer

    def get_queryset(self):
        queryset = ProductInfo.objects.all()
        query = Q()
        #TODO: Уменстно ли использование product_id как части пути или сделать аналогично shop_id и category_id?
        # product_id = self.request.query_params.get('product_id')
        product_id = self.kwargs.get('product_id')
        shop_id = self.request.query_params.get('shop_id')
        category_id = self.request.query_params.get('category_id')
        if product_id:
            query = query & Q(id=product_id)
            self.serializer_class = ProductInfoSerializer
        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        queryset = queryset.filter(query).prefetch_related("product__category")
        return queryset


class BasketView(APIView):
    """
    Класс для работы с корзиной покупателя
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'},
                                status=status.HTTP_403_FORBIDDEN)
        basket = Order.objects.filter(
            user_id=request.user.id, status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        # TODO:Изменить вид в котором выводится корзина, много лишней информации.
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        items = request.data.get('items')
        if type(items) != list:
            return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса. Ожидается список товаров.'})
        if not items:
            return JsonResponse({'Status': False, 'Errors': 'Список товаров пуст. Пожалуйста выберите товары из каталога'})
        order, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
        objects_created = []
        error_created = []
        for order_item in items:
            order_item.update({'order': order.id})
            serializer = OrderItemSerializer(data=order_item)
            if serializer.is_valid():
                try:
                    serializer.save()
                except IntegrityError:
                    order_item.update({'error': 'Товар уже добавлен в корзину.'})
                    error_created.append(order_item)
                except ValueError as error:
                    return JsonResponse({'Status': False, 'valuer_error': error})
                else:
                    objects_created.append(serializer.data)
            else:
                order_item.update({'error': serializer.errors})
                error_created.append(order_item)
        response = {}
        if bool(objects_created):
            response.update({'Обьекты добавленные в корзину': objects_created})
        if bool(error_created):
            response.update({'Ошибка добавления объектов': error_created})
        return JsonResponse(response)

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        items = request.data.get('items')
        if items:
            if type(items) != list:
                return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса. Ожидается список товаров.'})
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            serializer_list = []
            error_updated = []
            for order_item in items:
                order_item.update({'order': basket.id})
                serializer = OrderItemSerializer(data=order_item)
                if serializer.is_valid():
                    instance = OrderItem.objects.filter(
                        order_id=basket.id,
                        product_info_id=order_item['product_info']
                    )
                    serializer.instance = instance.first()
                    serializer_list.append(serializer)
                else:
                    order_item.update({'error': serializer.errors})
                    error_updated.append(order_item)
            if bool(error_updated):
                return JsonResponse({'Ошибка в обновлении': error_updated})
            elif len(items) == len(serializer_list):
                objects_updated = []
                for obj in serializer_list:
                    obj.is_valid()
                    obj.save()
                    objects_updated.append(obj.data)
                return JsonResponse({'Status': True, 'Обновленные объекты': objects_updated})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        items = request.data.get('items')
        if items:
            if type(items) != list:
                return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса. Ожидается список товаров.'})
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            objects_list = []
            error_deleted = []
            # TODO: Возможно в product_info следует передавать список id объектов
            for order_item in items:
                if type(order_item['product_info']) == int:
                    object = OrderItem.objects.filter(
                        order_id=basket.id,
                        product_info_id=order_item['product_info']
                    )
                    if object.exists():
                        objects_list.append(object)
                    else:
                        error_deleted.append(order_item)
                elif order_item['product_info'] == 'all':
                    OrderItem.objects.filter(
                        order_id=basket.id).delete()
                    return JsonResponse({'Status': True, 'Response': "Корзина очищена"})
                else:
                    error_deleted.append(order_item)
            if bool(error_deleted):
                return JsonResponse({'Таких товаров нет в корзине': error_deleted})
            elif len(items) == len(objects_list):
                object_deleted = [obj.delete() for obj in objects_list]
                return JsonResponse({'Status': True, 'Responce': 'Все записи были удалены'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrderView(APIView):
    """
    Класс для оформления и просмотра заказов покупателя
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        order = Order.objects.filter(
            user_id=request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        contact = request.data.get('contact_id')

        try:
            update_object = Order.objects.filter(user=request.user.id, status='basket').prefetch_related('ordered_items__product_info__shop')
        except ValueError:
            return JsonResponse({'Status': False, 'Errors': 'Неверно указаны элементы заказа.'})
        else:
            if update_object.exists():
                if update_object.first().contact or contact:
                    partner_list = [{'email': obj.product_info.shop.user.email,
                                     'data': {'product_info': obj.product_info,
                                              'quantity_basket': obj.quantity,
                                              'quantity_partner': obj.product_info.quantity}}
                                    for obj in update_object.first().ordered_items.all()]
                    # проверка наличия количества единиц товара у поставщика
                    for partner in partner_list:
                        if partner['data']['quantity_basket'] > partner['data']['quantity_partner']:
                            return JsonResponse(
                                {'Status': False, 'quantity_error': f'У поставщика больше нет такого количества товара. Вы можете заказать не более {partner["data"]["quantity_partner"]} единиц.'})
                    try:
                        update_object.update(status='new', contact=contact)
                    except IntegrityError:
                        return JsonResponse({'Status': False, 'contact_error': 'Неверно указанеы контакты пользователя.'})
                    else:
                        for partner in partner_list:
                            obj = partner['data']['product_info']
                            obj.quantity -= partner['data']['quantity_basket']
                            obj.save()
                    #TODO: Если у поставщика заказали несколько товаров,
                    # нужно отправить одно письмо на все товары, а не на каждый товар отдельно
                    # send_order_buyer(request.user.email, [data['data'] for data in partner_list])
                    # for partner in partner_list:
                        # send_order_partner(partner['email'], partner['data'])

                    return JsonResponse({'Status': True, 'Response': f'Заказ успешно подтвержден.'})
                else:
                    return JsonResponse({'Status': False, 'contact_error': 'Контакты пользователя не указаны.'})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Корзина пуста.'})


class PartnerState(APIView):
    """
    Класс для изменения статуса заказа поставщиком
    """
    # TODO: Если в заказе разные поставщики, то как может один поставщик менять статус заказа?
    #  Только владелец товара может менять статус!
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Заказы может просматривать только поставщик'}, status=403)
        order_id = kwargs.get('order_id')
        if order_id:
            try:
                status = request.data['status'] if request.data['status'] != "basket" else None
            except KeyError as error:
                return JsonResponse(
                    {'Status': False, 'Error': f'Ошибка в формате запроста. Проверьте верность поля {error}'})
            else:
                order = Order.objects.filter(
                    ordered_items__product_info__shop__user_id=request.user.id,
                    id=order_id).exclude(status='basket').prefetch_related(
                    'ordered_items__product_info__shop__user').distinct()
                serializer = OrderListSerializer(data={"id": order_id, "status": status}, instance=order.first())
                if order.exists():
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    update_state_message(order.first())
                    return JsonResponse({'Status': True,
                                         'Response': f"Заказ под номером {serializer.data['id']} переведен в статус {serializer.data['status']}."})
                else:
                    return JsonResponse({'Status': False, 'Error': f"Заказ под номером {order_id} отсутствует."})
        else:
            return JsonResponse({'Status': False, 'Error': "Не указаны все необходимы аргументы."})


class PartnerOrders(APIView):
    """
    Класс для просмотра заказов, в которых присутствуют товары поставщика
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Заказы может просматривать только поставщик'}, status=403)
        order_id = kwargs.get('order_id')
        if order_id:
            order = Order.objects.filter(
                ordered_items__product_info__shop__user_id=request.user.id, id=order_id).exclude(
                status='basket').prefetch_related(
                'ordered_items__product_info__shop__user',
                'ordered_items__product_info__product__category',
                'ordered_items__product_info__product_parameters__parameter').annotate(
                total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
            if order.exists():
                serializer = OrderSerializer(order.first())
                return Response(serializer.data)
            else:
                return JsonResponse({'Status': False, 'Errors': 'Заказ не найден. Проверьте номер заказа.'})
        else:
            order = Order.objects.filter(
                ordered_items__product_info__shop__user_id=request.user.id).exclude(status='basket').prefetch_related(
                'ordered_items__product_info__shop__user').distinct()
            serializer = OrderListSerializer(order, many=True)

            return Response(serializer.data)


class PartnerUpdate(APIView):
    """
    Класс загрузки файла с товарами и прайсом
    """

    def post(self, request):
        user = request.user
        # Проверка, что пользователь зарегистрирован
        if not user.is_authenticated:
            return JsonResponse({'Status': False, 'auth_error': 'Требуется войти в аккаунт'}, status=403)
        # Проверка, что пользователь - поставщик
        if user.type != 'shop':
            return JsonResponse({'Status': False, 'usertype_error': 'Размещать заказы могут только поставщики'}, status=403)
        url = request.data.get('url')
        filename = request.data.get('filename')
        # Проверка валидности сайта магазина
        #TODO: Нужен ли url как обязательный элемент?
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'url_error': str(e)})
        # Проверка валидности пути к файлу прайса
        if filename:
            try:
                os.stat(filename)
            except FileNotFoundError:
                return JsonResponse({'Status': False, 'url_error': 'Файл не найден'})
            # Чтение файла
            with open(request.data['filename'], encoding="utf-8") as fh:
                read_data = yaml.load(fh, Loader=yaml.SafeLoader)
                # Создаем или извлекаем магазин
                try:
                    shop, _ = Shop.objects.get_or_create(name=read_data['shop'], user_id=user.id)
                except IntegrityError:
                    return JsonResponse(
                        {'Status': False, 'file_error': 'Не указано название магазина или указано неверно'})
                shop.filename, shop.url, shop.last_update = request.data['filename'], url, timezone.now()
                shop.save()
                # Создаем или извлекаем категории
                # TODO: Что, если поставщик укажет неверный id или название (чтобы не плодились одинаковые категории)
                for category in read_data['categories']:
                    try:
                        category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    except IntegrityError:
                        return JsonResponse(
                            {'Status': False,
                             'file_error': 'Проверьте верность введенных данных в пункте Категория'})
                    except KeyError as error:
                        return JsonResponse(
                            {'Status': False,
                             'file_error': f'В одном или нескольких значениях списка Категорий отсутствует поле {error}'})
                    category_object.shops.add(shop.id)
                    category_object.save()
                # Удаляем прошлые продукты
                # TODO: Что будет с товарами в корзинах покупателей и в оформленных заказах после удаления?
                #  Они удалятся.
                #  Может их нужно обновлять?
                ProductInfo.objects.filter(shop=shop.id).delete()
                # Добавляем или извлекаем товары
                for item in read_data['goods']:
                    try:
                        product, _ = Product.objects.get_or_create(name=item['name'],
                                                                   category_id=item['category'])
                        product_info = ProductInfo.objects.create(product_id=product.id,
                                                                  external_id=item['id'],
                                                                  model=item['model'],
                                                                  price=item['price'],
                                                                  price_rrc=item['price_rrc'],
                                                                  quantity=item['quantity'],
                                                                  shop_id=shop.id)
                    except IntegrityError:
                        return JsonResponse(
                            {'Status': False,
                             'file_error': 'Проверьте верность введенных данных в пункте Товары'})
                    except KeyError as error:
                        return JsonResponse(
                            {'Status': False,
                             'file_error': f'В одном или нескольких значениях списка Товаров отсутствует поле {error}'})
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=str(value))
                return JsonResponse({'Status': True, 'Response': 'Прайс успешно обновлен'})
        return JsonResponse({'Status': False, 'field_error': 'Не указаны все необходимые аргументы'})

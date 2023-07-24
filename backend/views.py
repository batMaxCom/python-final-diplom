from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from django.utils import timezone

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.settings import api_settings


from backend.serializers import CategoriesSerializer, ProductInfoSerializer, ShopSerializer, \
    OrderItemSerializer, OrderSerializer, OrderListSerializer, ProductInfoListSerializer, StatusSerializer
from backend.models import Category, Shop, ProductInfo, Product, ProductParameter, Parameter, Order, OrderItem
from backend.tasks import update_state_message_task, send_order_buyer_task, send_order_partner_task

import yaml
import os

from users.permissions import IsShop
from users.views import serializer_error


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategoriesSerializer
    permission_classes = [AllowAny]


class ShopView(ListAPIView):
    """
    Класс для просмотра магазинов
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]


class ProductView(ListAPIView):
    """
    Класс для просмотра продуктов, с возможность сортировки по магазину или категории
    """
    serializer_class = ProductInfoListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = Q()
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
        queryset = ProductInfo.objects.filter(query).prefetch_related("product__category")
        return queryset


class BasketView(APIView):
    """
    Класс для работы с корзиной покупателя
    """

    def get(self, request, *args, **kwargs):
        basket = Order.objects.filter(
            user_id=request.user.id, status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        items = request.data.get('items')
        if type(items) != list:
            return JsonResponse({'Status': False, 'value_error': 'Неверный формат запроса. Ожидается список товаров.'}, status=status.HTTP_400_BAD_REQUEST)
        if not items:
            return JsonResponse({'Status': False, 'value_error': 'Список товаров пуст. Пожалуйста выберите товары из каталога'}, status=status.HTTP_400_BAD_REQUEST)
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
                    return JsonResponse({'Status': False, 'valuer_error': error}, status=status.HTTP_400_BAD_REQUEST)
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
        items = request.data.get('items')
        if items:
            if type(items) != list:
                return JsonResponse({'Status': False, 'value_error': 'Неверный формат запроса. Ожидается список товаров.'}, status=status.HTTP_400_BAD_REQUEST)
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
                return JsonResponse({'Status': False, 'update_error': error_updated}, status=status.HTTP_400_BAD_REQUEST)
            elif len(items) == len(serializer_list):
                objects_updated = []
                for obj in serializer_list:
                    obj.is_valid()
                    obj.save()
                    objects_updated.append(obj.data)
                return JsonResponse({'Status': True, 'Обновленные объекты': objects_updated}, status=status.HTTP_200_OK)
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        items = request.data.get('items')
        if items:
            if type(items) != list:
                return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса. Ожидается список товаров.'}, status=status.HTTP_400_BAD_REQUEST)
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            objects_list = []
            error_deleted = []
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
                    return JsonResponse({'Status': True, 'Response': "Корзина очищена"}, status=status.HTTP_200_OK)
                else:
                    error_deleted.append(order_item)
            if bool(error_deleted):
                return JsonResponse({'Status': False, 'Таких товаров нет в корзине': error_deleted}, status=status.HTTP_400_BAD_REQUEST)
            elif len(items) == len(objects_list):
                object_deleted = [obj.delete() for obj in objects_list]
                return JsonResponse({'Status': True, 'Response': 'Все записи были удалены'}, status=status.HTTP_200_OK)
        return JsonResponse({'Status': False, 'value_error': 'Не указаны все необходимые аргументы'}, status=status.HTTP_400_BAD_REQUEST)


class OrderView(APIView):
    """
    Класс для оформления и просмотра заказов покупателя
    """

    def get(self, request, *args, **kwargs):
        order = Order.objects.filter(
            user_id=request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        contact = request.data.get('contact_id')
        try:
            update_object = Order.objects.filter(user=request.user.id, status='basket').prefetch_related('ordered_items__product_info__shop')
            order = update_object.first()
        except ValueError:
            return JsonResponse({'Status': False, 'value_error': 'Неверно указаны элементы заказа.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if order:
                if order.contact or contact:
                    for obj in order.ordered_items.all():
                        if obj.quantity > obj.product_info.quantity:
                            return JsonResponse(
                                {'Status': False,
                                 'quantity_error': f'У поставщика больше нет такого количества товара. Вы можете заказать не более {obj.product_info.quantity} единиц.'}, status=status.HTTP_400_BAD_REQUEST)
                    try:
                        update_object.update(status='placed', contact=contact)
                    except IntegrityError:
                        return JsonResponse({'Status': False, 'contact_error': 'Неверно указанеы контакты пользователя.'}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        send_order_buyer_task.delay(request.user.email, order.id)
                        order.quantity_and_status_update()
                        partner_email = list(order.ordered_items.all().values_list("product_info__shop__user__email", flat=True).distinct())
                        for email in partner_email:
                            send_order_partner_task.delay(email, order.id)
                        return JsonResponse({'Status': True, 'Response': f'Заказ успешно подтвержден.'}, status=status.HTTP_200_OK)
                else:
                    return JsonResponse({'Status': False, 'contact_error': 'Контакты пользователя не указаны.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse({'Status': False, 'Errors': 'Корзина пуста.'}, status=status.HTTP_400_BAD_REQUEST)


class PartnerState(APIView):
    """
    Класс для изменения статуса заказа поставщиком
    """
    permission_classes = [*api_settings.DEFAULT_PERMISSION_CLASSES, IsShop]

    def post(self, request, *args, **kwargs):
        order_items_id = kwargs.get('order_items_id')
        if order_items_id:
            try:
                status = request.data['status']
            except KeyError as error:
                return JsonResponse(
                    {'Status': False, 'Error': f'Ошибка в формате запроста. Проверьте верность поля {error}'}, status=400)
            else:
                order_items = OrderItem.objects.filter(
                    product_info__shop__user_id=request.user.id,
                    id=order_items_id).exclude(status='basket').prefetch_related(
                    'product_info__shop__user').distinct().first()
                serializer = StatusSerializer(data={"id": order_items_id, "status": status}, instance=order_items)
                if order_items:
                    if serializer.is_valid():
                        serializer.save()
                        update_state_message_task.delay(order_items)
                        order = order_items.order
                        order.status_check()
                        return JsonResponse({'Status': True,
                                             'Response': f"Часть заказа №{order_items.order.id} под номером {order_items.id} переведен в статус {order_items.get_status_display()}."}, status=200)
                    else:
                        return serializer_error(serializer)
                else:
                    return JsonResponse({'Status': False, 'Error': f"Заказ под номером {order_items_id} отсутствует."}, status=400)
        else:
            return JsonResponse({'Status': False, 'Error': "Не указаны все необходимы аргументы."}, status=400)

class PartnerOrders(APIView):
    """
    Класс для просмотра заказов, в которых присутствуют товары поставщика
    """
    permission_classes = [*api_settings.DEFAULT_PERMISSION_CLASSES, IsShop]

    def get(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        if order_id:
            order_items = OrderItem.objects.filter(
                product_info__shop__user_id=request.user.id,
                order_id=order_id).exclude(
                order__status='basket').prefetch_related(
                'product_info__shop__user',
                'product_info__product__category',
                'product_info__product_parameters__parameter',
                'order').annotate(
                total_sum=Sum(F('quantity') * F('product_info__price')))
            if order_items.exists():
                serializer = OrderItemSerializer(order_items, many=True)
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
    permission_classes = [*api_settings.DEFAULT_PERMISSION_CLASSES, IsShop]

    def post(self, request):
        user = request.user
        url = request.data.get('url')
        filename = request.data.get('filename')
        # Проверка валидности сайта магазина
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
                return JsonResponse({'Status': False, 'url_error': 'Файл не найден'}, status=400)
            # Чтение файла
            with open(request.data['filename'], encoding="utf-8") as fh:
                read_data = yaml.load(fh, Loader=yaml.SafeLoader)
                # Создаем или извлекаем магазин
                try:
                    shop, _ = Shop.objects.get_or_create(name=read_data['shop'], user_id=user.id)
                except IntegrityError:
                    return JsonResponse(
                        {'Status': False, 'file_error': 'Не указано название магазина или указано неверно'}, status=400)
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
                             'file_error': 'Проверьте верность введенных данных в пункте Категория'}, status=400)
                    except KeyError as error:
                        return JsonResponse(
                            {'Status': False,
                             'file_error': f'В одном или нескольких значениях списка Категорий отсутствует поле {error}'}, status=400)
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
                             'file_error': 'Проверьте верность введенных данных в пункте Товары'}, status=400)
                    except KeyError as error:
                        return JsonResponse(
                            {'Status': False,
                             'file_error': f'В одном или нескольких значениях списка Товаров отсутствует поле {error}'}, status=400)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=str(value))
                return JsonResponse({'Status': True, 'Response': 'Прайс успешно обновлен'}, status=200)
        return JsonResponse({'Status': False, 'field_error': 'Не указаны все необходимые аргументы'}, status=400)

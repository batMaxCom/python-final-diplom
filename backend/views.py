from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from backend.serializers import CategoriesSerializer, ProductInfoSerializer, ShopSerializer, \
    OrderItemSerializer, OrderSerializer, OrderListSerializer
from backend.models import Category, Shop, ProductInfo, Product, ProductParameter, Parameter, Order, OrderItem
from rest_framework.response import Response
import yaml

class CategoryView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoriesSerializer


class ShopView(APIView):
    def get(self, request):
        queryset = Shop.objects.all()
        serializer = ShopSerializer(queryset, many=True)
        return Response(serializer.data)


class ProductView(APIView):
    def get(self, request, product_id=None, *args, **kwargs):
        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')
        if product_id:
            query = query & Q(id=product_id)
        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        queryset = ProductInfo.objects.filter(query).select_related('shop', 'product__category').prefetch_related('product_parameters__parameter').distinct()
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data)


class BasketView(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        items = request.data.get('items')
        if type(items) != list:
            return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса. Ожидается список товаров.'})
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
                                    product_info_id=order_item['product_info'],
                                    shop_id=order_item['shop']
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
            for order_item in items:
                if type(order_item['product_info']) == int and type(order_item['shop']) == int:
                    object = OrderItem.objects.filter(
                        order_id=basket.id,
                        product_info_id=order_item['product_info'],
                        shop_id=order_item['shop']
                        )
                    if object.exists():
                        objects_list.append(object)
                    else:
                        error_deleted.append(order_item)
                else:
                    error_deleted.append(order_item)
            if bool(error_deleted):
                return JsonResponse({'Таких товаров нет в корзине': error_deleted})
            elif len(items) == len(objects_list):
                object_deleted = [obj.delete() for obj in objects_list]
                return JsonResponse({'Status': True, 'Responce': 'Все записи были удалены'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrderView(APIView):
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
        order_id = request.data.get('order_id')
        try:
            update_object = Order.objects.filter(id=order_id, user=request.user.id, status='basket')
        except ValueError:
            return JsonResponse({'Status': False, 'Errors': 'Неверно указаны элементы заказа.'})
        else:
            if update_object.exists():
                update_object.update(status='new')
                # Отправка сообщения на почту продавцу и покупателю
                # send_message()
                return JsonResponse({'Status': True, 'Response': f'Заказ {order_id} успешно подтвержден.'})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неверно указан id заказа.'})


class PartnerState(APIView):
    """
    Класс для работы со статусом поставщика
    """
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
                return JsonResponse({'Status': False, 'Error': f'Ошибка в формате запроста. Проверьте верность поля {error}'})
            else:
                order = Order.objects.filter(
                    ordered_items__product_info__shop__user_id=request.user.id,
                    id=order_id).exclude(status='basket').prefetch_related('ordered_items__product_info__shop__user').distinct()
                serializer = OrderListSerializer(data={"id": order_id, "status": status}, instance=order.first())
                if order.exists():
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    return JsonResponse({'Status': True, 'Response': f"Заказ под номером {serializer.data['id']} переведен в статус {serializer.data['status']}."})
                else:
                    return JsonResponse({'Status': False, 'Error': f"Заказ под номером {order_id} отсутствует."})
        else:
            return JsonResponse({'Status': False, 'Error': "Не указаны все необходимы аргументы."})


class PartnerOrders(APIView):
    """
    Класс для работы с заказами, со стороны поставщика
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в аккаунт'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Заказы может просматривать только поставщик'}, status=403)
        order_id = kwargs.get('order_id')
        if order_id:
            order = Order.objects.filter(
                ordered_items__product_info__shop__user_id=request.user.id, id=order_id).exclude(status='basket').prefetch_related(
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

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        # Проверка, что пользователь - поставщик
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Размещать заказы могут только поставщики'}, status=403)
        url = request.data.get('url')
        #Проверка валидности сайта магазина
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                #Чтение файла
                with open(request.data['filename'], encoding="utf-8") as fh:
                    read_data = yaml.load(fh, Loader=yaml.SafeLoader)
                    # Создаем или извлекаем магазин
                    shop, _ = Shop.objects.get_or_create(name=read_data['shop'])
                    shop.__class__.objects.update(filename=request.data['filename'], url=url)
                    # Создаем категории
                    for category in read_data['categories']:
                        category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                        category_object.shops.add(shop.id)
                        category_object.save()
                    # Удаляем прошлые продукты
                    ProductInfo.objects.filter(shop=shop.id).delete()
                    # Добавляем или извлекаем товары
                    for item in read_data['goods']:
                        product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
                        product_info = ProductInfo.objects.create(product_id=product.id,
                                                                  name=item['model'],
                                                                  price=item['price'],
                                                                  price_rrc=item['price_rrc'],
                                                                  quantity=item['quantity'],
                                                                  shop_id=shop.id)
                        for name, value in item['parameters'].items():
                            parameter_object, _ = Parameter.objects.get_or_create(name=name)
                            ProductParameter.objects.create(product_info_id=product_info.id,
                                                            parameter_id=parameter_object.id,
                                                            value=str(value))
                    return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

class ContactView(APIView):
    pass

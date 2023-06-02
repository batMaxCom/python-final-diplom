from django.core.validators import URLValidator
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from backend.serializers import CategoriesSerializer, ProductInfoSerializer, ShopSerializer
from backend.models import Category, Shop, ProductInfo, Product, ProductParameter, Parameter
from rest_framework.response import Response
import yaml


class CategoryView(APIView):
    def get(self, request):
        queryset = Category.objects.all()
        serializer = CategoriesSerializer(queryset, many=True)
        return Response(serializer.data)


class ShopView(APIView):
    def get(self, request):
        queryset = Shop.objects.all()
        serializer = ShopSerializer(queryset, many=True)
        return Response(serializer.data)


class ProductView(APIView):
    def get(self, request):
        queryset = ProductInfo.objects.all()
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data)


class PartnerUpdate(APIView):

    def post(self, request):
        #Проверка на авторизованного пользователя
        # if not request.user.is_authenticated:
        #     return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        # Проверка, что пользователь - поставщик
        # if request.user.type != 'shop':
        #     return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
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
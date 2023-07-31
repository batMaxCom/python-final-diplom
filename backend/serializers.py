from decimal import Decimal

from django.core.validators import MinValueValidator
from rest_framework import serializers
from backend.models import Category, Shop, Product, ProductInfo, ProductParameter, Order, OrderItem
from users.serializers import ContactSerializer

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'url']
        read_only_fields = ('id',)


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ['name', 'category']


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value']


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ['id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters']
        read_only_fields = ('id',)


class ProductInfoListSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductInfo
        fields = ['id', 'product', 'shop', 'quantity', 'price', 'price_rrc']
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    order_items_id = serializers.IntegerField(source='id')
    quantity = serializers.IntegerField(min_value=1)
    product_info = ProductInfoSerializer()
    total_sum = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ['order_items_id', 'order', 'status', 'product_info', 'quantity', 'total_sum']
        read_only_fields = ('order_items_id', 'order')

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get("quantity", instance.quantity)
        instance.save()
        return instance

    def validate_quantity(self, value):
        data = self.initial_data
        try:
            max_value = ProductInfo.objects.get(id=data['product_info']).quantity
        except:
            return value
        else:
            if value > max_value:
                raise serializers.ValidationError({f'value_error': f'Вы не можете выбрать больше, чем имеется у поставщика. Максимальное значение: {max_value}'})
        return value



class OrderListSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'status', 'dt', 'contact')
        read_only_fields = ('id',)


class OrderItemCreateSerializer(OrderItemSerializer):
    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):

    ordered_items = OrderItemCreateSerializer(read_only=True, many=True)
    total_sum = serializers.IntegerField()
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'status', 'dt', 'ordered_items',  'total_sum', 'contact')
        read_only_fields = ('id',)


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['status']
        read_only_fields = ('id', 'order', 'product_info', 'quantity')

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.quantity)
        instance.save()
        return instance

from rest_framework import serializers
from backend.models import Category, Shop, Product, ProductInfo, User


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['name', 'url']


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']


class ProductSerializer(serializers.ModelSerializer):
    category = CategoriesSerializer()
    class Meta:
        model = Product
        fields = ['category']


class ProductInfoSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(read_only=True)
    product = ProductSerializer(many=False)
    class Meta:
        model = ProductInfo
        fields = ['name', 'shop', 'product', 'quantity', 'price', 'price_rrc']


class UserRegistrSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField()


    class Meta:
        model = User
        fields = ['email', 'password', 'password2']

    def save(self, *args, **kwargs):
        user = User(
            email=self.validated_data['email'],
        )
        password = self.validated_data['password']
        password2 = self.validated_data['password2']
        self.validated_data['is_staff'] = True
        self.validated_data['is_superuser'] = True
        if password != password2:
            raise serializers.ValidationError({password: "Пароль не совпадает"})
        user.set_password(password)
        user.save()
        return user


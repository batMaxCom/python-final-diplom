from django.contrib import admin


from backend.models import *

class CategoryInline(admin.TabularInline):
    model = Category


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Shop._meta.fields]

    # exclude = ['email']
    # list_filter = ['name']
    # search_fields = ['email', 'name']


class ProductInline(admin.TabularInline):
    model = ProductInfo


class ProductParameterInline(admin.TabularInline):
    model = ProductParameter


class OrderItemInline(admin.TabularInline):
    model = OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Category._meta.fields]




@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Product._meta.fields]
    inlines = [ProductInline, ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Order._meta.fields]
    inlines = [OrderItemInline, ]


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Parameter._meta.fields]
    inlines = [ProductParameterInline, ]


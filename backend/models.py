from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from users.models import User, Contact

# STATE_CHOICES = (
#     ('basket', 'Статус корзины'),
#     ('new', 'Новый'),
#     ('confirmed', 'Подтвержден'),
#     ('assembled', 'Собран'),
#     ('sent', 'Отправлен'),
#     ('delivered', 'Доставлен'),
#     ('canceled', 'Отменен'),
# )

STATE_ORDER_CHOICES = (
    ('basket', 'Статус корзины'),
    ('placed', 'Оформлен'),
    ('close', 'Закрыт'),
)

STATE_ORDERITEM_CHOICES = (
    ('new', 'Ожидает подтверждения'),
    ('confirmed', 'Подтвержден поставщиком'),
    ('assembled', 'Собран'),
    ('transferred', 'Передан в доставку'),
    ('send', 'В пути'),
    ('delivered', 'Доставлен'),
)



USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель')
)


class Shop(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название магазина')
    url = models.URLField(verbose_name='Ссылка магазина', null=True, blank=True)
    filename = models.FileField(verbose_name='Файл с прайсом', blank=True,
                                upload_to=None)  # Файл yaml с прайсом. Необходима возможность его обновления
    last_update = models.DateTimeField(verbose_name='Последнее обновление прайса', null=True, blank=True)
    # state = models.BooleanField(verbose_name='статус получения заказов', default=True) #как работает?
    user = models.OneToOneField(User, verbose_name='Поставщик', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = "Список магазинов"

    def __str__(self):
        return self.name


class Category(models.Model):
    shops = models.ManyToManyField(Shop, verbose_name='Магазин', related_name='categories')
    name = models.CharField(max_length=128, verbose_name='Название категории', unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Категория')
    name = models.CharField(max_length=128, verbose_name='Название продукта')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Список продуктов"

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Продукт', related_name='product_info')
    external_id = models.PositiveIntegerField(verbose_name='Внешний ИД')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин', related_name='product_info')
    model = models.CharField(max_length=128, verbose_name='Модель продукта')
    quantity = models.PositiveIntegerField(verbose_name='Количество продукта',)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', validators=[MinValueValidator(Decimal('0.01'))]),
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Рекомендуемая розничная цена', validators=[MinValueValidator(Decimal('0.01'))])

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = "Информативный список о продуктах"

    def __str__(self):
        return self.model

class Parameter(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название параметра')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = "Список имен параметров"


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, verbose_name='Информация о продукте',
                                     related_name='product_parameters')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, verbose_name='Параметр',
                                  related_name='product_parameters')
    value = models.CharField(max_length=128, verbose_name='Значение параметра')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = "Список параметров"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='users')
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=128, choices=STATE_ORDER_CHOICES, verbose_name='Статус заказа', default='basket')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, verbose_name='Контакты', related_name='contact', null=True, blank=True)
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказов"

    def quantity_and_status_update(self):
        for order_items in self.ordered_items.all():
            product_info = order_items.product_info
            product_info.quantity -= order_items.quantity
            product_info.save()
            order_items.status = 'new'
            order_items.save()
    def status_check(self):
        status = [order_items.status for order_items in self.ordered_items.all()]
        if status.count('delivered') == len(status):
            self.status = 'close'
            self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ', related_name='ordered_items')
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, verbose_name='Продукт', related_name='ordered_items')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    status = models.CharField(max_length=128, choices=STATE_ORDERITEM_CHOICES, verbose_name='Статус отправления товара', blank=True)
    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order'),
        ]

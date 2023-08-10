from celery import shared_task

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from backend.models import Order, OrderItem


@shared_task
def update_state_message_task(order_items_id):
    """
    Отправка сообщения об изменении статуса заказа
    """
    order = OrderItem.objects.get(id=order_items_id)
    message = f'Изменен статус заказа: {order.id}\n' \
              f'Новый статус "{order.get_status_display()}".'

    msg = EmailMultiAlternatives(
        # title:
        f"Обновление статуса заказа",
        # message:
        message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [order.order.user.email]
    )
    msg.send()


@shared_task
def send_order_buyer_task(email, order_id):
    """
        Отправка сообщения клиенту об успешном форомлении заказа
        """
    order = Order.objects.get(id=order_id)
    message = f"Успешно создан заказ под номером: {order_id}\n" \
              "Состав заказа:\n"
    for items in order.ordered_items.all():
        message += f'Магазин: {items.product_info.shop.name}\n' \
                   f'Категория: {items.product_info.product.category.name}\n' \
                   f'Модель: {items.product_info.product.name}\n' \
                   f'Количество: {items.quantity} \n\n'
    msg = EmailMultiAlternatives(
        # title:
        f"Заказ успешно оформлен",
        # message:
        message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [email]
    )
    msg.send()


@shared_task
def send_order_partner_task(email, order_id):
    """
        Отправка сообщения клиенту об успешном форомлении заказа
        """
    order = Order.objects.get(id=order_id)
    message = f"Успешно оформлен заказ №: {order.id}\n" \
              f"Клиент: {order.user.email}\n" \
              f"Контакты доставки: {order.contact}\n" \
              "Состав заказа:\n"
    for items in order.ordered_items.all().filter(product_info__shop__user__email=email):
        message += f'Категория: {items.product_info.product.category.name}\n' \
                   f'Модель: {items.product_info.product.name}\n' \
                   f'Количество: {items.quantity} \n\n'
    msg = EmailMultiAlternatives(
        # title:
        f"Вам поступил заказ",
        # message:
        message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [email]
    )
    msg.send()
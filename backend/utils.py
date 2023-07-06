from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def update_state_message(order):
    """
    Отправка сообщения об изменении статуса заказа
    """
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
        [order.user.email]
    )
    msg.send()

def send_order_buyer(email, order_id, order_items):
    """
        Отправка сообщения клиенту об успешном форомлении заказа
        """
    message = f"Успешно создан заказ под номером: {order_id}\n" \
              "Состав заказа:\n"
    for items, quantity in order_items.items():
        message += f'Магазин: {items.shop.name}\n' \
                   f'Категория: {items.product.category.name}\n' \
                   f'Модель: {items.product.name}\n' \
                   f'Количество: {quantity} \n\n'
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

def send_order_partner(email, order, order_items):
    """
        Отправка сообщения клиенту об успешном форомлении заказа
        """
    message = f"Успешно оформлен заказ №: {order.id}\n" \
              f"Клиент: {order.user.email}\n" \
              f"Контакты доставки: {order.contact}\n" \
              "Состав заказа:\n"
    for items, quantity in order_items.items():
        message += f'Категория: {items.product.category.name}\n' \
                   f'Модель: {items.product.name}\n' \
                   f'Количество: {quantity} \n\n'
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
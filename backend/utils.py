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
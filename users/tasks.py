from celery import shared_task

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


@shared_task
def adding_task(x, y):
    return x + y


@shared_task
def verifity_email_code_task(user_email, user_code):
    """
    Отправка сообщения для подтверждения почты
    """
    # send an e-mail to the user
    message = f'Код активации: {user_code}\n' \
              'Привет! Хотим убедиться, что ты не робот.\n' \
              'Введи код на странице регистрации, чтобы активировать учетную запись.'

    msg = EmailMultiAlternatives(
        # title:
        "Подтверждение почты",
        # message:
        message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user_email]
    )
    msg.send()


@shared_task
def reset_password_task(user_email, new_password):
    """
    Отправка сообщения для подтверждения почты
    """
    # send an e-mail to the user
    message = f'Ваш новый пароль: {new_password}\n' \
              'Пожалуйста не передавайте его посторонним лицам.\n' \
              'Если вы не отправляли запрос на восстановление пароля, пожалуйста проигнорируйте данное сообщение.'

    msg = EmailMultiAlternatives(
        # title:
        "Восстановление пароля",
        # message:
        message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user_email]
    )
    msg.send()


@shared_task
def reset_email_code_task(user_email, user_code):
    """
    Отправка сообщения для смены адреса почты
    """
    # send an e-mail to the user
    message = f'Код для смены электронной почты: {user_code}\n' \
              f'Введи код на странице подтверждения почты.' \
              'Пожалуйста не передавайте его посторонним лицам.\n'

    msg = EmailMultiAlternatives(
        # title:
        "Смена адреса почты",
        # message:
        message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user_email]
    )
    msg.send()

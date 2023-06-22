import smtplib
import string
import random

from django.conf import settings

email_from = settings.DEFAULT_EMAIL_BACKEND
email_from_password = settings.DEFAULT_EMAIL_BACKEND_PASSWORD

def generate_code():
    code = ''.join(random.choice(string.digits) for _ in range(4))
    return code


def send_message(email, message):
    server = smtplib.SMTP('smtp.mail.ru', 25)
    server.starttls()
    server.login(email_from, email_from_password)
    server.sendmail(email_from, email, message.encode('utf-8'))


def send_activation_email(email, code):
    context = f'Код активации: {code}\n' \
              'Привет! Хотим убедиться, что ты не робот.\n' \
              'Введи код на странице регистрации, чтобы активировать учетную запись.'
    send_message(email, context)


def send_reset_password_email(email, new_password):
    context = f'Ваш новый пароль: {new_password}\n' \
              'Пожалуйста не передавайте его посторонним лицам.\n'
    send_message(email, context)

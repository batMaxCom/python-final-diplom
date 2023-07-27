from django.http import HttpResponse

from users.utils import generate_code
from users.tasks import verifity_email_code_task


def verified_email(backend, user, response, *args, **kwargs):
    if not user.is_verified:
        user.code = generate_code()
        verifity_email_code_task.delay(user.email, user.code)

def re_login_email(backend, user, response, *args, **kwargs):
    if user:
        return HttpResponse(f'Вы уже авторизовались как {user.email}')

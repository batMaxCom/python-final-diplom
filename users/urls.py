from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from users.views import RegisterAccountView, LoginAccountView, \
    ResetPasswordView, ContactView, ChangePasswordView, AccountDetailsView, EmailVerifyView

app_name = 'backend'
urlpatterns = [
    path('user/register', RegisterAccountView.as_view(), name='user-register'),
    path('user/login', LoginAccountView.as_view(), name='user-login'),
    path('user/register/confirm', EmailVerifyView.as_view(), name='user-register-confirm'),
    path('user/details', AccountDetailsView.as_view(), name='user-details'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user/password_change', ChangePasswordView.as_view(), name='password-change'),
    path('user/password_reset', ResetPasswordView.as_view(), name='password-reset'),
    # path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),  # подтвердить смену пароля
    # path('user/email_change', ChangeEmailView.as_view(), name='email-change'),  # обновить email
]

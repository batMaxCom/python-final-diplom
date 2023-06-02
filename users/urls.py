from django.urls import path

from users.views import RegisterAccount

app_name = 'backend'
urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'), #регистрация аккаунта
    # path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'), #подтвержение аккаунта
    # path('user/details', AccountDetails.as_view(), name='user-details'), #детали аккаунта
    # path('user/contact', ContactView.as_view(), name='user-contact'), #контакты аккаунта
    # path('user/login', LoginAccount.as_view(), name='user-login'), #залогиниться
    # path('user/password_reset', reset_password_request_token, name='password-reset'), #обновить пароль
    # path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'), подтвердить пароль
]
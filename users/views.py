from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from users.permissions import IsActivated, IsOwnerEmail
from users.serializers import LoginSerializer, UserSerializer, ChangePasswordSerializer, \
    ResetPasswordSerializer, AccountDetailSerializer, ContactSerializer, EmailVerifySerializer
from users.utils import send_reset_password_email


class RegisterAccountView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors)


class EmailVerifyView(APIView):
    serializer_class = EmailVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower()
        password = serializer.validated_data['password']
        code = serializer.validated_data['code']

        user = User.objects.filter(email=email)
        if not user:
            raise ValidationError({'auth': 'Неверно указал адрес электронной почты или пароль'})
        user = user.first()
        if not user.check_password(password):
            raise ValidationError({'auth': 'Неверно указал адрес электронной почты или пароль'})
        if code == user.code:
            if not user.is_verified:
                user.is_verified = True
                user.is_active = True
                user.code = None
                user.save()
                return Response({'success': 'Почта успешна подтверждена'}, status=status.HTTP_200_OK)
        elif user.is_verified:
            raise ValidationError({email: 'Почта уже подтверждена.'})
        else:
            raise ValidationError({code: 'Вы ввели неверный код подтверждения.'})


class LoginAccountView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(email=email, password=password)
        if not user or not user.check_password(password):
            return Response(
                {'auth': 'Проверьте, верно ли введены адрес электронной почты и пароль.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif not user.is_active:
            return Response(
                {'auth': 'Пользователь неактивен.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif user.is_active and not user.is_verified:
            return Response(
                {'auth': 'Пользователь не подтвердил адрес электронной почты.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user.last_login = timezone.now()
        user.save()
        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'email': user.email, 'token': token.key}, status=status.HTTP_200_OK)


class AccountDetailsView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = AccountDetailSerializer
    permission_classes = [IsAuthenticated, IsActivated]

    def get_object(self):
        user = User.objects.filter(pk=self.request.user.pk)
        return user.first()


# Добавить возможность редактирования контактов
class ContactView(AccountDetailsView):
    serializer_class = ContactSerializer


class ChangePasswordView(CreateAPIView):
    permission_classes = [IsAuthenticated, IsActivated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data
        old_password = data['old_password']
        new_password = data['new_password']

        if not user.check_password(old_password):
            raise ValidationError({'old_password': 'Вы ввели неверный пароль.'})

        if old_password == new_password:
            raise ValidationError(
                {'new_password': 'Новый пароль не может совпадать со старым.'})

        user.set_password(new_password)
        user.changed_password_date = timezone.now()
        user.save()
        return Response({'success': 'Пароль изменен'}, status=status.HTTP_200_OK)


class ResetPasswordView(CreateAPIView):
    # throttle_scope = 'password_reset' # контроль за количеством запросов на сброс пароля
    serializer_class = ResetPasswordSerializer
    permission_classes = [IsAuthenticated, IsActivated, IsOwnerEmail]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower()
        user = User.objects.filter(email=email)
        if not user:
            raise ValidationError({'email': 'Адрес электронной почты не найден'})
        else:
            user = user.first()
        password = User.objects.make_random_password()
        user.set_password(password)
        user.changed_password_date = timezone.now()
        user.save()
        send_reset_password_email(user.email, password)
        return Response(
            {'success': 'Новый пароль отправлен на вашу почту.'},
            status=status.HTTP_200_OK
        )


"""
Разработать смену email.
"""
# class ChangeEmailView(CreateAPIView):
#     permission_classes = [IsAuthenticated, IsActivated]
#     serializer_class = ChangeEmailSerializer
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         data = serializer.validated_data
#         user = self.request.user
#         new_email = data['new_email'].lower()
#         code = data['code']
#
#         if not user.code:
#             raise ValidationError({'code': 'send change email request first'})
#
#         if code == user.code:
#             user.email = new_email
#             user.code = None
#             user.save()
#             return Response({'success': 'email changed'}, status=status.HTTP_200_OK)
#         else:
#             raise ValidationError({'code': 'wrong'})

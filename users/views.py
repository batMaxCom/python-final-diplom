from smtplib import SMTPRecipientsRefused, SMTPDataError

from django.http import JsonResponse
from django.utils import timezone

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from users.models import User, Contact
from users.serializers import LoginSerializer, UserSerializer, ChangePasswordSerializer, \
    ResetPasswordSerializer, AccountDetailSerializer, ContactSerializer, EmailVerifySerializer, ChangeEmailSerializer, \
    ChangeEmailConfirmSerializer
from users.utils import generate_code, reset_password, reset_email_code

def serializer_error(serializer):
    return JsonResponse({'Status': False, 'valid_error': serializer.errors},
                                    status=status.HTTP_400_BAD_REQUEST)


class RegisterAccountView(CreateAPIView):
    """
    Класс для регистрации.
    Основной функционал прописан в сериализаторе.
    """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_200_OK)
        else:
            return serializer_error(serializer)




class EmailVerifyView(APIView):
    """
    Класс для подтверждения почты.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = EmailVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email'].lower()
            password = serializer.validated_data['password']
            code = serializer.validated_data['code']

            user = User.objects.filter(email=email)
            if not user:
                return JsonResponse({'Status': False, 'auth_error': 'Неверно указан адрес электронной почты или пароль'}, status=status.HTTP_401_UNAUTHORIZED)
            user = user.first()
            if not user.check_password(password):
                return JsonResponse({'Status': False, 'auth_error': 'Неверно указан адрес электронной почты или пароль'}, status=status.HTTP_401_UNAUTHORIZED)
            if code == user.code:
                if not user.is_verified:
                    user.is_verified = True
                    user.is_active = True
                    user.code = None
                    user.save()
                    return Response({'Status': True, 'Response': 'Почта успешна подтверждена'}, status=status.HTTP_200_OK)
            elif user.is_verified:
                return JsonResponse({'Status': False, 'email_error': 'Почта уже подтверждена.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse({'Status': False, 'code_error': 'Вы ввели неверный код подтверждения.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return serializer_error(serializer)


class LoginAccountView(APIView):
    """
    Класс для авторизации.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = User.objects.filter(email=email).first()
            if not user or not user.check_password(password):
                return JsonResponse(
                    {'Status': False, 'auth_error': 'Проверьте, верно ли введены адрес электронной почты и пароль.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            elif not user.is_active:
                return JsonResponse(
                    {'Status': False, 'auth_error': 'Пользователь неактивен.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            elif user.is_active and not user.is_verified:
                return JsonResponse(
                    {'Status': False, 'auth_error': 'Пользователь не подтвердил адрес электронной почты.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            user.last_login = timezone.now()
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({'Status': True, 'Response': {'email': user.email, 'token': token.key}}, status=status.HTTP_200_OK)
        else:
            return serializer_error(serializer)

class AccountDetailsView(RetrieveAPIView):
    """
    Класс для просмотра деталей аккаунта пользователя.
    """
    queryset = User.objects.all()
    serializer_class = AccountDetailSerializer

    def get_object(self):
        user = self.get_queryset().filter(pk=self.request.user.pk)
        return user.first()



class ChangePasswordView(CreateAPIView):
    """
    Класс для изменения пароля.
    """
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            data = serializer.validated_data
            old_password = data['old_password']
            new_password = data['new_password']

            if not user.check_password(old_password):
                return JsonResponse({'Status': False, 'old_password_error': 'Вы ввели неверный пароль.'}, status=status.HTTP_401_UNAUTHORIZED)
            if old_password == new_password:
                return JsonResponse({'Status': False, 'new_password_error': 'Новый пароль не может совпадать со старым.'}, status=status.HTTP_401_UNAUTHORIZED)

            user.set_password(new_password)
            user.changed_password_date = timezone.now()
            user.save()
            return JsonResponse({'Status': True, 'Response': 'Пароль изменен'}, status=status.HTTP_200_OK)
        else:
            return serializer_error(serializer)

class ResetPasswordView(CreateAPIView):
    """
    Класс для сброса пароля.
    Новый пароль приходит на почту.
    """
    throttle_scope = [AnonRateThrottle]
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():

            email = serializer.validated_data['email'].lower()
            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({'Status': True, 'email_error': 'Адрес электронной почты не найден'}, status=status.HTTP_400_BAD_REQUEST)
            elif not user.is_verified:
                return JsonResponse(
                    {'Status': False, 'auth_error': 'Пользователь не подтвердил адрес электронной почты. Оправка нового пароля на почту невозможна.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            password = User.objects.make_random_password()
            user.set_password(password)
            user.changed_password_date = timezone.now()
            user.save()
            reset_password(user.email, password)
            return JsonResponse({'Status': True, 'Response': 'Новый пароль отправлен на вашу почту.'}, status=status.HTTP_200_OK)
        else:
            return serializer_error(serializer)


class ChangeEmailView(CreateAPIView):
    """
    Класс для смены электронной почты.
    """
    serializer_class = ChangeEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            new_email = request.data['new_email']
            existing_email = User.objects.filter(email=new_email)
            if user.email == new_email:
                return JsonResponse(
                    {'Status': False, 'email_error': "Вы не можете изметь адрес на текущий."}, status=status.HTTP_400_BAD_REQUEST)
            elif existing_email.exists():
                return JsonResponse(
                    {'Status': False, 'email_error': "Адрес электронной почты уже зарезервирован другим пользователем."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                code = generate_code()
                try:
                    reset_email_code(user.email, code)
                except (SMTPDataError, SMTPRecipientsRefused):
                    return JsonResponse(
                        {'Status': False, 'email_error': "Проверьте верность введеногого адреса электронной почты."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    user.code = code
                    user.new_email = new_email
                    user.save()
                    return JsonResponse({'Status': True, 'Response': f'Код активации новой почты отправлен на адрес {user.new_email}.'}, status=status.HTTP_200_OK)
        else:
            return serializer_error(serializer)

class NewEmailConfirm(APIView):
    """
    Класс для подтверждения новой электронной почты.
    """
    serializer_class = ChangeEmailConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            user = self.request.user
            new_email = data['new_email'].lower()
            code = data['code']
            if not user.code:
                return JsonResponse({'Status': False, 'code_error': 'В истории отсутствует запрос на смену почты.'}, status=status.HTTP_400_BAD_REQUEST)
            if user.new_email != new_email:
                return JsonResponse({'Status': False, 'email_error': 'Новый адрес почты не совпадает с тем, что вы отправили в запросе.'}, status=status.HTTP_400_BAD_REQUEST)
            if code == user.code:
                user.email = new_email
                user.code = None
                user.new_email = None
                user.save()
                return JsonResponse({'Status': True, 'Response': 'почта успешна обновлена', 'new_email': new_email}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'Status': False, 'code_error': 'Вы ввели неверный код подтверждения'})
        else:
            return serializer_error(serializer)


class ContactView(APIView):
    """
    Класс для просотра, создания, изменения и удаления контактов.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def get(self, request,  *args, **kwargs):
        contact_id = kwargs.get('contact_id')
        if contact_id:
            queryset = self.queryset.filter(id=contact_id, user_id=request.user.id)
            if queryset.exists():
                serializer = self.serializer_class(queryset.first())
            else:
                return JsonResponse({'Status': False, 'contact_error': 'Контакт не найден.'},
                                    status=status.HTTP_404_NOT_FOUND)
        else:
            queryset = self.queryset.filter(user_id=request.user.id)
            serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def post(self, request,  *args, **kwargs):
        request.data._mutable = True
        request.data.update({'user': request.user.id})
        phone = request.data.get('phone')
        if phone:
            try:
                int(request.data['phone'])
            except ValueError:
                return JsonResponse({'Status': False, 'phone_error': 'Пожалуйста проверте номер телефона. Он не должен содержать пробелов, букв или символов'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return serializer_error(serializer)

    def patch(self, request,  *args, **kwargs):
        request.data._mutable = True
        request.data.update({'user': request.user.id})
        contact_id = kwargs.get('contact_id')
        queryset = self.queryset.filter(id=contact_id, user_id=request.user.id)
        if queryset.exists():
            serializer = ContactSerializer(data=request.data, instance=queryset.first(), partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return serializer_error(serializer)
        else:
            return JsonResponse({'Status': False, 'contact_error': 'Контакт не найден.'},
                                status=status.HTTP_404_NOT_FOUND)

    def delete(self, request,  *args, **kwargs):
        contact_id = kwargs.get('contact_id')
        queryset = self.queryset.filter(id=contact_id, user_id=request.user.id)
        if queryset.exists():
            queryset.delete()
            return JsonResponse({'Status': True, 'Response': 'Контакт удален.'},
                         status=status.HTTP_204_NO_CONTENT)
        else:
            return JsonResponse({'Status': False, 'contact_error': 'Контакт не найден.'},
                                status=status.HTTP_404_NOT_FOUND)

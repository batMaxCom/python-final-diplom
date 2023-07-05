from smtplib import SMTPRecipientsRefused, SMTPDataError

from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework import serializers

from users.models import User, Contact
from users.utils import generate_code, verifity_email_code

error_messages = {
    "blank": "Поле не может быть пустым.",
    "required": "Это поле обязательно для заполнения.",
    "invalid": "Неверно заполненные данные."
}

class AccountSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=6,
        allow_blank=False,
        error_messages={
            "min_length": "Пароль должен состоять более чем из 6 символов.",
            **error_messages
        }
    )
    email = serializers.EmailField(
        allow_blank=False,
        error_messages=error_messages
    )
    new_email = serializers.EmailField(
        allow_blank=False,
        error_messages=error_messages
    )
    old_password = serializers.CharField(
        min_length=6,
        error_messages={
            "min_length": "Пароль должен состоять более чем из 6 символов.",
            **error_messages
        }
    )
    new_password = serializers.CharField(
        min_length=6,
        error_messages={
            "min_length": "Пароль должен состоять более чем из 6 символов.",
            **error_messages
        }
    )
    code = serializers.CharField(
        allow_blank=False,
        min_length=4,
        max_length=4,
        error_messages={
            "min_length": "Код должен состоять из 4 символов",
            "max_length": "Код должен состоять из 4 символов",
            **error_messages
        }
    )

    class Meta:
        abstract = True


class UserSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'password',
            'company',
            'position',
            'is_active',
            'is_verified',
            'type'
        ]

    def create(self, validated_data):
        email = validated_data.get('email').lower()
        user_type = validated_data.get('type')
        try:
            User.objects.get(email=email)
            raise serializers.ValidationError({'Status': False, 'email_error': "Пользователь с таким адресом уже зарегистрирован."})
        except ObjectDoesNotExist:
            user = User(email=email)
        try:
            if self.validated_data['password'] != self.initial_data['re_password']:
                raise serializers.ValidationError({'Status': False, 'password_error': "Пароли не совпадают"})
        except MultiValueDictKeyError:
            raise serializers.ValidationError({'Status': False, 'password_error': "Вы не ввели пароль повторно."})
        user.set_password(validated_data['password'])
        user.code = generate_code()
        if user_type:
            user.type = user_type
        try:
            verifity_email_code(user.email, user.code)
        except (SMTPDataError, SMTPRecipientsRefused):
            raise serializers.ValidationError({'Status': False, 'email_error': "Проверьте верность введеногого адреса электронной почты."})
        user.save()
        return user


class EmailVerifySerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['code', 'email', 'password']


class LoginSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']


class ChangePasswordSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['old_password', 'new_password']


class ResetPasswordSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['email']


class AccountDetailSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'is_active', 'is_verified']


class ContactSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="user.type", read_only=True)
    phone = serializers.CharField(
        allow_blank=False,
        min_length=10,
        max_length=10,
        error_messages={
            "min_length": "Пожалуйста введите номер телефона, состоящий из 10 цифр, без кодов +7 или 8",
            "max_length": "Пожалуйста введите номер телефона, состоящий из 10 цифр, без кодов +7 или 8",
            **error_messages
        }
    )
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = Contact
        fields = ('id', 'user', 'email', 'first_name', 'last_name', 'surname', 'type', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone')
        read_only_fields = ('id', 'type')


class ChangeEmailSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['new_email']


class ChangeEmailConfirmSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['new_email', 'code']

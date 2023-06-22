from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework import serializers

from users.models import User
from users.utils import generate_code, send_activation_email


class AccountSerializer(serializers.ModelSerializer):
    error_messages = {
        "blank": "Поле не может быть пустым.",
        "required": "Это поле обязательно для заполнения.",
        "invalid": "Неверно заполненные данные."
    }
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        allow_blank=False,
        error_messages={
            "min_length": "Пароль должен состоять более чем из 6 символов.",
            **error_messages
        }
    )
    email = serializers.CharField(
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
        email = validated_data['email'].lower()
        try:
            User.objects.get(email=email)
            raise serializers.ValidationError({'email_error': "Пользователь с таким адресом уже зарегистрирован."})
        except ObjectDoesNotExist:
            user = User(email=email)
        try:
            if self.validated_data['password'] != self.initial_data['re_password']:
                raise serializers.ValidationError({'password_error': "Пароли не совпадают"})
        except MultiValueDictKeyError:
            raise serializers.ValidationError({'password_error': "Вы не ввели пароль повторно."})
        user.set_password(validated_data['password'])
        user.code = generate_code()
        # user.type = validated_data['type'] # добавить тип аккаунта
        user.save()
        send_activation_email(user.email, user.code)
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


class ContactSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'company', 'position', 'type']


# class ChangeEmailSerializer(AccountSerializer):
#     class Meta:
#         model = User
#         fields = ['new_email']


# class ChangeEmailConfirmSerializer(AccountSerializer):
#     class Meta:
#         model = User
#         fields = ['new_email', 'code']

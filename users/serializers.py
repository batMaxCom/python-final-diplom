from smtplib import SMTPRecipientsRefused, SMTPDataError

from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework import serializers

from users.models import User, Contact
from users.utils import generate_code
from users.tasks import verifity_email_code_task



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
        read_only_fields = ('is_active', 'is_verified')

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
            verifity_email_code_task.delay(user.email, user.code)
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


    class Meta:
        model = Contact
        fields = ('id', 'user', 'first_name', 'last_name', 'surname', 'type',
                  'region', 'area', 'city', 'street',
                  'house', 'structure', 'building', 'apartment',
                  'phone')
        read_only_fields = ('id', 'type')

    # def validate(self, attrs):
    #     region_value = attrs.get('region')
    #     area_value = attrs.get('area')
    #     city_value = attrs.get('city')
    #     street_value = attrs.get('street')
    #     region_file = os.path.join(os.path.dirname(__file__), os.path.relpath("adress_base/00.json"))
    #     adress_file = ''
    #     with open(region_file, 'r', encoding='utf-8') as f:
    #         region_list = json.load(f)
    #         region = [region for region in region_list if re.match(region_value.lower()[0:3], region[1].lower())]
    #         if bool(region):
    #             if len(region) > 1:
    #                 raise serializers.ValidationError({
    #                     'area_error': 'В системе несколько вариантов населенных пунктов.'
    #                                   'Укажите один из:'
    #                                   f'{[r[1] for r in region]}'})
    #             region = region[0]
    #             attrs['region'] = ''.join(region[1])
    #             adress_file += region[0]
    #         else:
    #             raise serializers.ValidationError({'region_error': 'Данного региона не найдено'})
    #
    #     city_area_file = os.path.join(os.path.dirname(__file__), os.path.relpath(f"adress_base/{adress_file}.json"))
    #     with open(city_area_file, 'r', encoding='utf-8') as f:
    #         city_area_list = json.load(f)
    #         if area_value:
    #             area = [area for area in city_area_list if re.match(area_value.lower()[0:3], area[1].lower()) and len(area[0])==3]
    #             if bool(area):
    #                 if len(area) > 1:
    #                     raise serializers.ValidationError({
    #                         'area_error': 'В системе несколько вариантов населенных пунктов.'
    #                                       'Укажите один из:'
    #                                       f'{[a[1] for a in area]}'})
    #                 area = area[0]
    #                 attrs['area'] = ''.join(area[1])
    #                 adress_file += area[0]
    #     city_area_file = os.path.join(os.path.dirname(__file__), os.path.relpath(f"adress_base/{adress_file}.json"))
    #     with open(city_area_file, 'r', encoding='utf-8') as f:
    #         city_area_list = json.load(f)
    #         city = [city for city in city_area_list if re.match(city_value.lower()[0:3], city[1].lower()) and len(city[0])==6]
    #         if bool(city):
    #             if len(city) > 1:
    #                 raise serializers.ValidationError({
    #                     'city_error': 'В системе несколько вариантов населенных пунктов.'
    #                                     'Укажите один из:'
    #                                     f'{[c[1] for c in city]}'})
    #             city = city[0]
    #             attrs['city'] = ''.join(city[1])
    #             adress_file += city[0]
    #         else:
    #             raise serializers.ValidationError({'city_error': 'Населенный пункт не найден. Попробуйте указать Район или проверить верность ввода'})
    #     city_area_file = os.path.join(os.path.dirname(__file__), os.path.relpath(f"adress_base/{adress_file}.json"))
    #     with open(city_area_file, 'r', encoding='utf-8') as f:
    #         city_area_list = json.load(f)
    #         street = [street for street in city_area_list if
    #                 re.match(street_value.lower()[0:3], street[1].lower())]
    #         if bool(street):
    #             if len(street) > 1:
    #                 raise serializers.ValidationError({
    #                     'street_error': 'В системе несколько вариантов улицы.'
    #                                     'Укажите один из:'
    #                                     f'{[s[1] for s in street]}'})
    #             street = street[0]
    #             attrs['street'] = ''.join(street[1])
    #
    #         else:
    #             raise serializers.ValidationError({'street_error': 'Улица не найдена. Проверьте верность ввода'})
    #
    #     return attrs

    # def validate_region(self, value):
        # file_path = os.path.relpath("adress_base/00.json")
        # with open(os.path.join(os.path.dirname(__file__), file_path), 'r', encoding='utf-8') as f:
        #     region_list = json.load(f)
        #     region = [region[1] for region in region_list if re.match(value.lower()[0:3], region[1].lower())]
        #     if bool(region):
        #         return ''.join(region)
        #     else:
        #         raise serializers.ValidationError({'region_error': 'Данного региона не найдено'})

    # def validate_city(self, value):
    #     pass
    #
    # def validate_street(self, value):
    #     pass


class ChangeEmailSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['new_email']


class ChangeEmailConfirmSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ['new_email', 'code']

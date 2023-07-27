from django import forms
from django.forms import ModelForm, EmailInput, PasswordInput

from backend.models import ProductInfo
from users.models import User, USER_TYPE_CHOICES


class RegisterForm(ModelForm):
    email = forms.CharField(widget=EmailInput, label='Email')
    password = forms.CharField(widget=PasswordInput, label='Пароль')
    re_password = forms.CharField(widget=PasswordInput, label='Повторите пароль')

    class Meta:
        model = User
        fields = ["email",  "password"]


class LoginForm(ModelForm):
    email = forms.CharField(widget=EmailInput, label='Email')
    password = forms.CharField(widget=PasswordInput, label='Пароль')

    class Meta:
        model = User
        fields = ["email",  "password"]


class CodeForm(ModelForm):
    code = forms.IntegerField(label='Код подтверждения')

    class Meta:
        model = User
        fields = ["code"]


class ProductForm(ModelForm):
    quantity = forms.IntegerField(label='Количество')

    class Meta:
        model = ProductInfo
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': 1})}
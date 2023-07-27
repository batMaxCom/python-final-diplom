import requests
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
import requests
from django.urls import reverse

from backend.models import ProductInfo, Order, OrderItem
from frontend.forms import RegisterForm, ProductForm, LoginForm, CodeForm
from users.models import User, UserManager


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        re_password = request.POST.get("re_password")
        type = request.POST.get("type")
        data = {'email': email, 'password': password, 're_password': re_password, 'type': type}
        response = requests.post('http://127.0.0.1:8000/api/v1/user/register/', json=data)
        print(response)
        return HttpResponse(f"{response.text}")

    else:
        userform = RegisterForm()
        return render(request, "users/register.html", {"form": userform, "request": request})


def auth(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("frontend:products"))
        else:
            return HttpResponse(f'Ошибка логина или пароля')
    else:
        userform = LoginForm()
        return render(request, "users/login.html", {"form": userform, "request": request})


def log_out(request):
    logout(request)
    return HttpResponseRedirect(reverse("frontend:products"))


def email_verified(request):
    if request.method == "POST":
        code = request.POST.get("code")
        user = request.user
        if user.code == code:
            user.code = None
            user.is_verified = True
            user.save()
            return HttpResponseRedirect(reverse("frontend:products"))
        else:
            return HttpResponse("Ошибка")
    else:
        codeform = CodeForm()
        return render(request, "users/login.html", {"form": codeform, "request": request})


def products(request, product_id=None):
    if product_id:
        if request.method == "POST":
            quantity = request.POST.get("quantity")
            basket, _ = Order.objects.get_or_create(status='basket', user_id=request.user.id)
            OrderItem.objects.create(quantity=quantity, order=basket, product_info_id=product_id)
            return HttpResponse(f"Товар успешно добавлен в корзину")

        else:
            product = get_object_or_404(ProductInfo, id=product_id)
            form = ProductForm()
            return render(request, "backend/product.html", {'product': product, 'form': form})

    else:
        products = ProductInfo.objects.all()
        return render(request, "backend/products.html", {'products': products})


def basket(request):
        basket = OrderItem.objects.filter(order__status='basket', order__user_id=request.user.id)
        return render(request, "backend/basket.html", {'orderitem': basket, 'request': request})



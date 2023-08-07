import json

import pytest
from django.conf import settings
import os
from pytest_lazyfixture import lazy_fixture

from django.contrib.auth import authenticate

from rest_framework.authtoken.models import Token

from backend.models import ProductInfo, Order, OrderItem
from users.models import User, Contact


@pytest.fixture
def user_shop_yandex(client):
    user = User(email='yandex@mail.com', is_verified=True, is_active=True, type='shop')
    user.set_password('testpassword')
    user.save()
    return user


@pytest.fixture
def shop_yandex_token(user_shop_yandex):
    token, _ = Token.objects.get_or_create(user=user_shop_yandex)
    return f'Token {token}'


@pytest.fixture
def price_yandex(client, shop_yandex_token, user_shop_yandex):
    response = client.post(
        '/api/v1/partner/update/',
        data={
            'url': 'https://www.yandex-market.ru',
            'filename': os.path.join(settings.BASE_DIR, os.path.relpath('data/shop_yandexmarket.yaml'))
        },
        headers={'Authorization': shop_yandex_token})
    return ProductInfo.objects.filter(shop__user_id=user_shop_yandex.id)


@pytest.fixture
def user_svyaznoy_shop(client):
    user = User(email='svyaznoy@mail.com', is_verified=True, is_active=True, type='shop')
    user.set_password('testpassword')
    user.save()
    return user


@pytest.fixture
def shop_svyaznoy_token(user_svyaznoy_shop):
    token, _ = Token.objects.get_or_create(user=user_svyaznoy_shop)
    return f'Token {token}'


@pytest.fixture
def price_svyaznoy(client, shop_svyaznoy_token, user_svyaznoy_shop):
    response = client.post(
        '/api/v1/partner/update/',
        data={
            'url': 'https://www.svyaznoy.ru',
            'filename': os.path.join(settings.BASE_DIR, os.path.relpath('data/shop_svyaznoy.yaml')),
        },
        headers={'Authorization': shop_svyaznoy_token})
    return ProductInfo.objects.filter(shop__user_id=user_svyaznoy_shop.id)


@pytest.fixture
def user_buyer(client):
    user = User(email='buyer@mail.com', is_verified=True, is_active=True, type='buyer')
    user.set_password('testpassword')
    user.save()
    return user


@pytest.fixture
def buyer_token(user_buyer):
    token, _ = Token.objects.get_or_create(user=user_buyer)
    return f'Token {token}'


@pytest.fixture
def price_svyaznoy_path():
    return os.path.join(settings.BASE_DIR, os.path.relpath('data/shop_svyaznoy.yaml'))


@pytest.fixture
def basket_product(client, price_yandex, user_buyer, buyer_token):
    product_id = price_yandex.first().id
    quantity = price_yandex.first().quantity
    request = client.put(
        '/api/v1/basket/',
        data={"items": [
            {"product_info": product_id,
             "quantity": quantity}]
        }, content_type='application/json',
        headers={'Authorization': buyer_token})
    product = OrderItem.objects.get(product_info_id=product_id)
    return product

@pytest.fixture
def buyer_contact(client, buyer_token, user_buyer):
    request = client.post(
        '/api/v1/user/contact/',
        data={
            'first_name': 'first_name',
            'last_name': 'last_name',
            'region': 'region',
            'city': 'city',
            'street': 'street',
            'house': 'house',
            'phone': '9879876655'
        },
        headers={'Authorization': buyer_token}
    )
    return Contact.objects.filter(user_id=user_buyer.id).first()



@pytest.mark.django_db
def test_product_list(client, price_yandex, price_svyaznoy):
    count = ProductInfo.objects.count()
    response = client.get(
        '/api/v1/products/')
    assert response.status_code == 200
    assert len(response.json()) == count


@pytest.mark.django_db
@pytest.mark.parametrize(
    "product_id, status_code",
    [
        (lazy_fixture('price_yandex'), 200),
        (999, 404),
    ]
)
def test_product_retrieve(client, price_yandex, product_id, status_code):
    count = ProductInfo.objects.count()
    if type(product_id) == int:
        response = client.get(f'/api/v1/products/{product_id}')
    else:
        product_id = price_yandex.first().id
        response = client.get(f'/api/v1/products/{product_id}')
    assert response.status_code == status_code
    if response.status_code == 200:
        assert response.json()['id'] == product_id


@pytest.mark.parametrize(
    "url, filename, token, status_code",
    [
        (
                'https://www.svyaznoy.ru',
                lazy_fixture('price_svyaznoy_path'),
                lazy_fixture('shop_svyaznoy_token'),
                200),
        (
                'svyaznoy.ru',
                lazy_fixture('price_svyaznoy_path'),
                lazy_fixture('shop_svyaznoy_token'),
                400),
        (
                'https://www.svyaznoy.ru',
                'C:\Price\shop_svyaznoy.yaml',
                lazy_fixture('shop_svyaznoy_token'),
                400),
        (
                'https://www.svyaznoy.ru',
                lazy_fixture('price_svyaznoy_path'),
                lazy_fixture('buyer_token'),
                403),
    ]
)
@pytest.mark.django_db
def test_shop_price_update(client, url, filename, token, status_code):
    count = ProductInfo.objects.count()
    response = client.post(
        '/api/v1/partner/update/',
        data={
            'url': url,
            'filename': filename,
        },
        headers={'Authorization': token})
    assert response.status_code == status_code
    if response.status_code == 200:
        assert ProductInfo.objects.count() == count + 4
    else:
        assert ProductInfo.objects.count() == count


@pytest.mark.parametrize(
    "product_info, quantity, status_code",
    [
        (lazy_fixture('price_yandex'), 1, 200),
        (lazy_fixture('price_yandex'), 99, 400),
        (999, 1, 400),
    ]
)
@pytest.mark.django_db
def test_basket_create(client, user_buyer, buyer_token, price_svyaznoy, product_info, quantity, status_code):
    count = OrderItem.objects.filter(order__status='basket', order__user=user_buyer).count()
    if type(product_info) != int:
        product_info = product_info.first().id
    response = client.post(
        '/api/v1/basket/',
        data={"items": [
                {"product_info": product_info,
                 "quantity": quantity}]
            }, content_type='application/json',
        headers={'Authorization': buyer_token})
    assert response.status_code == status_code
    if response.status_code == 200:
        assert response.json()['Status'] == True
        assert OrderItem.objects.filter(order__status='basket', order__user=user_buyer).count() == count+1
    else:
        assert OrderItem.objects.filter(order__status='basket', order__user=user_buyer).count() == count


@pytest.mark.django_db
def test_basket_list(client, buyer_token):
    response = client.get(
        '/api/v1/basket/',
        headers={'Authorization': buyer_token})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "product_info, new_quantity, status_code",
    [
        (lazy_fixture('basket_product'), 1, 200),
        (lazy_fixture('basket_product'), 99, 400),
        (999, 1, 400),
    ]
)
@pytest.mark.django_db
def test_basket_update(client,
                       buyer_token,
                       price_svyaznoy,
                       product_info, new_quantity, status_code):
    if not type(product_info) == int:
        quantity = product_info.quantity
        product_info = product_info.product_info_id
    response = client.put(
        '/api/v1/basket/',
        data={"items": [
            {"product_info": product_info,
             "quantity": new_quantity}]
        }, content_type='application/json',
        headers={'Authorization': buyer_token})
    assert response.status_code == status_code
    if response.status_code == 200:
        assert OrderItem.objects.get(product_info_id=product_info).quantity == new_quantity
        assert OrderItem.objects.get(product_info_id=product_info).quantity != quantity

@pytest.mark.parametrize(
    "product_in_basket",
    [
        (lazy_fixture('basket_product')), (None)
    ]
)
@pytest.mark.django_db
def test_buyer_order_list(client, buyer_token, user_buyer, product_in_basket):
    if product_in_basket is None:
        response = client.get(
            '/api/v1/order/',
            headers={'Authorization': buyer_token})
        assert len(response.json()) == 0
    else:
        order = product_in_basket.order
        order.status = 'placed'
        order.save()
        count = order.ordered_items.all().count()
        response = client.get(
            '/api/v1/order/',
            headers={'Authorization': buyer_token})
        assert len(response.json()) == count
    assert response.status_code == 200


@pytest.mark.parametrize(
    "user_contact, edit_quantity_product, product_in_basket , status_code, response_text",
    [
        (lazy_fixture('buyer_contact'), False, lazy_fixture('basket_product'), 200, True),
        (999, False,  lazy_fixture('basket_product'), 400, 'contact_error'),
        (None, False, lazy_fixture('basket_product'),  400, 'contact_error'),
        (lazy_fixture('buyer_contact'), True, lazy_fixture('basket_product'), 400, 'quantity_error'),
        (lazy_fixture('buyer_contact'), False, None,  400, 'Errors'),
    ]
)
@pytest.mark.django_db
def test_buyer_order_create1(client, buyer_token, user_buyer, user_contact, product_in_basket, edit_quantity_product, status_code, response_text):
    if edit_quantity_product:
        product_in_basket.quantity = 800
        product_in_basket.save()
    if type(user_contact) == int:
        data = {'contact_id': user_contact}
    elif user_contact is None:
        data = {}
    else:
        data = {'contact_id': user_contact.id}
    response = client.post(
        '/api/v1/order/',
        content_type='application/json',
        data=data,
        headers={'Authorization': buyer_token})
    assert response.status_code == status_code
    if response.status_code == 200:
        assert Order.objects.get(user_id=user_buyer.id).status == 'placed'
        assert response.json()['Status'] == response_text
    else:
        assert response_text in response.json()


@pytest.mark.parametrize(
    "order_items, status, token, status_code",
    [
        (lazy_fixture('basket_product'), 'confirmed', lazy_fixture('shop_yandex_token'), 200),
        (lazy_fixture('basket_product'), 'another_status', lazy_fixture('shop_yandex_token'), 400),
        (999, 'confirmed', lazy_fixture('shop_yandex_token'), 400),
        (lazy_fixture('basket_product'), '', lazy_fixture('shop_yandex_token'), 400),
        (lazy_fixture('basket_product'), 'confirmed', lazy_fixture('shop_svyaznoy_token'), 400),
        ('', 'confirmed', lazy_fixture('shop_yandex_token'), 404),

    ]
)
@pytest.mark.django_db
def test_shop_order_state(client, order_items, status, token, status_code):
    try:
        order = order_items.order
    except AttributeError:
        order_items_id = order_items
    else:
        order.status = 'placed'
        order.save()
        order_items_id = order_items.id
    data = {'status': status}
    response = client.post(
        f'/api/v1/partner/status/{order_items_id}',
        content_type='application/json',
        data=data,
        headers={'Authorization': token})
    assert response.status_code == status_code


# @pytest.mark.django_db
# def test_shop_order(client):
#     pass


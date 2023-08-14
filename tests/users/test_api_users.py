import pytest
from pytest_lazyfixture import lazy_fixture

from django.contrib.auth import authenticate

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from users.models import User, Contact


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(client):
    request = client.post(
        '/api/v1/user/register/',
        data={'email': 'example@mail.com', 'password': 'testpassword', 're_password': 'testpassword'})
    user = User.objects.get(email='example@mail.com')
    return user


@pytest.fixture
def verified_user(user):
    user.is_active = True
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def user_code(user):
    return user.code

@pytest.fixture
def verified_user_code(verified_user):
    return verified_user.code


@pytest.fixture
def token(verified_user):
    token, _ = Token.objects.get_or_create(user=verified_user)
    return f'Token {token}'


@pytest.fixture
def contact(client, token, verified_user):
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
        headers={'Authorization': token}
    )
    return Contact.objects.filter(user_id=verified_user.id).first()


@pytest.mark.parametrize(
    "email, password, re_password, status_code",
    [
        ('example@mail.com', 'testpassword', 'testpassword', 201),
        ('example@mail.com', 'testpassword', 'another-password', 400),
        ('example', 'testpassword', 'testpassword', 400)
    ]
)
@pytest.mark.django_db
def test_successful_register(client, email, password, re_password, status_code):
    count = User.objects.count()
    response = client.post(
        '/api/v1/user/register/',
        data={'email': email, 'password': password, 're_password': re_password})
    assert response.status_code == status_code
    if response.status_code == 201:
        assert User.objects.count() == count + 1
    else:
        assert User.objects.count() == count


@pytest.mark.parametrize(
    "email, password, code, status_code",
    [
        ('example@mail.com', 'testpassword', lazy_fixture('user_code'), 200),
        ('example@mail.com', 'another-password', lazy_fixture('user_code'), 401),
        ('another-example@mail.com', 'testpassword', lazy_fixture('user_code'), 401),
        ('example@mail.com', 'testpassword', '', 400),
        ('example@mail.com', 'testpassword', '123456', 400),
        ('example@mail.com', 'testpassword', '123456', 400),
        ('example@mail.com', 'testpassword', '1234', 400),
    ]
)
@pytest.mark.django_db
def test_register_confirm(client, user, email, password, code, status_code):
    response = client.post(
        '/api/v1/user/register/confirm/',
        data={'email': email, 'password': password, 'code': code})
    assert response.status_code == status_code


@pytest.mark.parametrize("email, password, code, status_code", [('example@mail.com', 'testpassword', '1234', 400)])
@pytest.mark.django_db
def test_register_confirm_user_verifity(client, verified_user, email, password, code, status_code):
    response = client.post(
        '/api/v1/user/register/confirm/',
        data={'email': email, 'password': password, 'code': code})
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "email, password, is_verified, status_code",
    [
        ('example@mail.com', 'testpassword', True, 200),
        ('example@mail.com', 'another-password', True, 401),
        ('another-example@mail.com', 'testpassword', True, 401),
        ('example@mail.com', 'testpassword', False, 401),
        (None, None, True, 400),
    ]
)
@pytest.mark.django_db
def test_login(client, user, email, password, is_verified, status_code):
    if is_verified:
        user.is_active = True
        user.is_verified = True
        user.save()
    response = client.post(
        '/api/v1/user/login/',
        data={'email': email, 'password': password})
    assert response.status_code == status_code

@pytest.mark.django_db
def test_account_details(client, verified_user, token):
    response = client.get(
        '/api/v1/user/details/',
        headers={'Authorization': token})
    assert response.status_code == 200
    assert len(response.json()) != 0

@pytest.mark.parametrize(
    "old_password, new_password, status_code",
    [
        ('testpassword', 'another-password', 200),
        ('testpassword', 'testpassword', 400),
        ('another-password', 'testpassword', 401),
        (None, None, 400),
    ]
)
@pytest.mark.django_db
def test_password_change(client, verified_user, token, old_password, new_password, status_code):
    response = client.post(
        '/api/v1/user/password_change/',
        data={'old_password': old_password, 'new_password': new_password}, headers={'Authorization': token})
    assert response.status_code == status_code
    if response.status_code == 200:
        assert authenticate(email='example@mail.com', password=new_password)
    else:
        assert authenticate(email='example@mail.com', password='testpassword')


@pytest.mark.parametrize(
    "email, is_verified, status_code",
    [
        ('another-example@mail.com', True, 400),
        ('example@mail.com', False, 401),
        ('example@mail.com', True, 200),
        (None, True, 400),
    ]
)
@pytest.mark.django_db
def test_password_reset(client, user, email, is_verified, status_code):
    if is_verified:
        user.is_active = True
        user.is_verified = True
        user.save()
    response = client.post(
        '/api/v1/user/password_reset/',
        data={'email': email})
    if response.status_code == 200:
        if response.status_code == 200:
            assert authenticate(email='example@mail.com', password='testpassword') == None
        else:
            assert authenticate(email='example@mail.com', password='testpassword')
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "new_email, token_1, status_code",
    [
        ('new-example@mail.com', lazy_fixture('token'), 200),
        ('new-example', lazy_fixture('token'), 400),
        ('example@mail.com', lazy_fixture('token'), 400),
        ('new-example@mail.com', '', 401),
        (None,  lazy_fixture('token'), 400),
    ]
)
@pytest.mark.django_db
def test_email_change(client, verified_user, new_email, token_1, status_code):
    response = client.post(
        '/api/v1/user/email_change/',
        data={'new_email': new_email}, headers={'Authorization': token_1})
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "new_email, verified_user_code_1, token_1, status_code",
    [
        ('new-example@mail.com', lazy_fixture('verified_user_code'), lazy_fixture('token'), 200),
        ('new-example@mail.com', lazy_fixture('verified_user_code'), '', 401),
        ('example@mail.com', lazy_fixture('verified_user_code'), lazy_fixture('token'), 400),
        ('new-example@mail.com', '', lazy_fixture('token'), 400),
        ('new-example@mail.com', '123456', lazy_fixture('token'), 400),
        ('new-example', lazy_fixture('verified_user_code'), lazy_fixture('token'), 400),
    ]
)
@pytest.mark.django_db
def test_email_change_confirm(client, verified_user, new_email, verified_user_code_1, token_1, status_code):
    request = client.post(
        '/api/v1/user/email_change/',
        data={'new_email': 'new-example@mail.com'}, headers={'Authorization': token_1})
    response = client.post(
        '/api/v1/user/email_change/confirm/',
        data={'new_email': new_email, 'code': verified_user_code_1}, headers={'Authorization': token_1})
    assert response.status_code == status_code



@pytest.mark.parametrize(
    "first_name, last_name, region, city, street, house, phone, token_1, status_code",
    [
        ('first', 'last', 'region', 'city', 'street', 'house', '9879876655', lazy_fixture('token'), 200),
        ('first', 'last', 'region', 'city', 'street', 'house', 'aaabbbccdd', lazy_fixture('token'), 400),
        ('first', 'last', 'region', 'city', 'street', 'house', '89879876655', lazy_fixture('token'), 400),
        ('first', None, 'region', 'city', None, 'house', '9879876655', lazy_fixture('token'), 400),
        ('first', 'last', 'region', 'city', 'street', 'house', '9879876655', '', 401),
    ]
)
@pytest.mark.django_db
def test_contact_create(client, verified_user, token_1,
                        first_name, last_name, region, city, street, house, phone,
                        status_code):
    count = Contact.objects.count()
    response = client.post(
        '/api/v1/user/contact/',
        data={
            'first_name': first_name,
            'last_name': last_name,
            'region': region,
            'city': city,
            'street': street,
            'house': house,
            'phone': phone
        },
        headers={'Authorization': token_1}
    )
    assert response.status_code == status_code
    if response.status_code == 200:
        assert Contact.objects.count() == count + 1
    else:
        assert Contact.objects.count() == count


@pytest.mark.django_db
def test_contact_list(client, contact, verified_user, token):
    response = client.get(
        '/api/v1/user/contact/',
        content_type='application/json',
        headers={'Authorization': token}
    )
    assert response.status_code == 200
    assert Contact.objects.count() == 1
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_contact_retrieve(client, contact, verified_user, token):
    response_200 = client.get(
        f'/api/v1/user/contact/{contact.id}',
        headers={'Authorization': token}
    )
    response_404 = client.get(
        f'/api/v1/user/contact/{contact.id+1}',
        headers={'Authorization': token}
    )
    assert response_200.status_code == 200
    assert response_404.status_code == 404



@pytest.mark.parametrize(
    "first_name, last_name, region, city, street, house, phone, token_1, status_code",
    [
        ('new_first', 'last', 'region', 'city', 'street', 'house', '9879876655', lazy_fixture('token'), 200),
        ('first', 'last', 'region', 'city', 'street', 'house', '89879876655', lazy_fixture('token'), 400),
        ('first', None, 'region', 'city', None, 'house', '9879876655', lazy_fixture('token'), 400),
        ('first', 'last', 'region', 'city', 'street', 'house', '9879876655', '', 401),
    ]
)
@pytest.mark.django_db
def test_contact_update(client, contact, verified_user, token_1,
                        first_name, last_name, region, city, street, house, phone,
                        status_code):
    contact_id = contact.id
    response = client.patch(
        f'/api/v1/user/contact/{contact_id}',
        data={
            'first_name': first_name,
            'last_name': last_name,
            'region': region,
            'city': city,
            'street': street,
            'house': house,
            'phone': phone
        },
        headers={'Authorization': token_1}
    )
    assert response.status_code == status_code


def test_example():
    assert 1 == 1

# Создание, просмотр, редактирование и удаление контактов пользователя

[Главная страница](../README.md)


## Описание

Данный элемент приложение предназначен для работы с контактными данными пользователей, которые в дальнейшем будут использоваться как адрес доставки.

В него входит следующий функционал:
- создание контактов,
- редактирование,
- просмотр,
- удаление.

## Разделы:
В каждом разделе будут указаны HTTP-запросы необходимые для взаимодействия с API, 
указаны все обязательные и необязательные для заполнения поля и их описание.

**baseUrl** - Базовый путь приложения
### Регистрация

POST-запрос:
```
POST {{baseUrl}}/api/v1/user/contact/
Content-Type: application/json

{
  "email": email,
  "password": "password",
  "re_password": "re_password",
  "type": "type"
}
```
### Описание полей:
- Обязательные поля:
  - email - адрес электронной почты,
  - password - пароль,
  - re_password - повторное введение пароля.
- Необязательные поля:
  - type - вид пользователя: 
    - Клиент (buyer, по умолчанию),
    - Поставщик (shop).
  - **baseUrl** - Базовый URL
### Создание контактов

POST-запрос:
```
POST {{baseUrl}}/api/v1/user/register/
Content-Type: application/json
Authorization: Token "my_token"

{
  "last_name": "last_name",
  "first_name": "first_name",
  "surname": "surname",
  "city": "city",
  "street": "street",
  "house": "house",
  "structure": "structure",
  "building": "building",
  "apartment": "apartment",
  "phone": "phone"
}
```
#### Описание полей:
- Обязательные поля:
  - last_name - Имя,
  - first_name - Фамилия,
  - city - город,
  - street - улица,
  - house - дом,
  - phone - номер телефона.
- Необязательные поля:
  - surname - Отчество: 
  - structure - корпус,
  - building - строение,
  - apartment - квартира.

### Просмотр контактов

GET-запрос:
```
GET {{baseUrl}}/api/v1/user/contact/
#GET {{baseUrl}}/api/v1/user/contact/<contact_id>

Content-Type: application/json
Authorization: Token "my_token"

```
#### Описание :
-  Просмотр списка всех контактов,
-  При указании contact_id, открывается карточка контакта

### Редактирование контактов

PATCH-запрос:

```
PATCH {{baseUrl}}/api/v1/user/contact/<contact_id>
Content-Type: application/json
Authorization: Token "my_token"

{
  "last_name": "last_name",
  "first_name": "first_name",
  "surname": "surname",
  "city": "city",
  "street": "street",
  "house": "house",
  "structure": "structure",
  "building": "building",
  "apartment": "apartment",
  "phone": "phone"
}
```

#### Описание :
В запросе можно указать один или несколько полей, все они являются необязательными.
Указание **contact_id** в запросе - обязательно.

### Удаление контактов

DELETE-запрос:
```
DELETE {{baseUrl}}/api/v1/user/contact/<contact_id>

Content-Type: application/json
Authorization: Token "my_token"

```
#### Описание :
Указание **contact_id** в запросе - обязательно.
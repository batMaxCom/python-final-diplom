# Функционал клиента

[Главная страница](../README.md)

[Содержание](../project_description/info.md)

## Описание

Для клиента доступны следующие операции:
- Корзина:
  - создание корзины( первичное добавление товаров)
  - просмотр содержимого корзины,
  - редактирование состава корзины,
  - удаление обьектов корзины (в том числе, полная очистка)
- Заказ:
  - оформление заказа (товаров из корзины),
  - просмотр оформленных заказов.

## Разделы:
В каждом разделе будут указаны HTTP-запросы необходимые для взаимодействия с API, 
указаны все обязательные и необязательные для заполнения поля и их описание.

**baseUrl** - Базовый путь приложения
**my_token** - уникальный ключ авторизации
### Создание корзины

POST-запрос:
```
POST {{baseUrl}}/api/v1/basket/
Content-Type: application/json
Authorization: Token "my_token"

{"items":
    [
        {
        "product_info": product_info_1,
        "quantity": quantity
        },
        {
        "product_info": product_info_2,
        "quantity": quantity
        }
    ]
}
```
### Описание полей:
Может указываться как один, так и несколько словарей, содержащих товары.
Обязательные поля:
- items - перечисление товаров:
  - product_info - id продукта,
  - quantity - необходимое количество.

### Просмотр корзины

GET-запрос:
```
GET {{baseUrl}}/api/v1/basket/
Content-Type: application/json
Authorization: Token "my_token"

```
### Описание:
Просмотр состава корзины.

### Обновление корзины

PUT-запрос:
```
PUT {{baseUrl}}/api/v1/basket/
Content-Type: application/json
Authorization: Token "my_token"

{"items":
    [
        {
        "product_info": product_info_1,
        "quantity": quantity
        },
        {
        "product_info": product_info_2,
        "quantity": quantity
        }
    ]
}
```
### Описание полей:
Может указываться как один, так и несколько словарей, содержащих товары, ранее добавленные в корзину.
- Обязательные поля - **все**.

### Удаление товаров из корзины или ее очистка

DELETE-запрос:
```
DELETE {{baseUrl}}/api/v1/basket/
Content-Type: application/json
Authorization: Token "my_token"

{"items":
    [
        {"product_info": product_info_1},
        {"product_info": product_info_2}
        #{"product_info": "all"}
    ]
}
```
### Описание:
Удаление содержимого корзины

Обязательные поля:
- items - перечисление товаров:
  - product_info - id продукта.

При указании параметра **all** происходит полная очистка корзины.

### Создание заказа, составляющий товары из корзины

POST-запрос:
```
DELETE {{baseUrl}}/api/v1/basket/
Content-Type: application/json
Authorization: Token "my_token"

{
"contact_id":"contact_id"
}
```
### Описание:
Подтверждение заказа.

Обязательные поля:
- contact_id - id одного из ранее созданных контактов. Используется как адрес доставки.

### Просмотр заказов

GET-запрос:
```
GET {{baseUrl}}/api/v1/basket/
Content-Type: application/json
Authorization: Token "my_token"
```
### Описание:
Просмотр подтвержденных заказов.

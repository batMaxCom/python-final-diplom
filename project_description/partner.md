# Функционал поставщика

[Главная страница](../README.md)

[Содержание](../project_description/info.md)

## Описание

Для поставщика доступны следующие операции:
- обновления прайса,
- просмотр заказов, в состав которых входят товары поставщика,
- изменение статуса заказа.

## Разделы:
В каждом разделе будут указаны HTTP-запросы необходимые для взаимодействия с API, 
указаны все обязательные и необязательные для заполнения поля и их описание.

**baseUrl** - Базовый путь приложения
**my_token** - уникальный ключ авторизации
### Обновление прайса

POST-запрос:
```
POST {{baseUrl}}/api/v1/partner/update
Content-Type: application/json
Authorization: Token "my_token"

{
    "url":"url",
    "filename":"filename"
}
```
### Описание полей:
Обязательные поля:
- filename - указание пути на локальном хранилище к файлу прайса (в формате yaml).
Необязательные поля:
- url - адрес магазина.

### Просмотр заказов, в составе которых присутствуют товары поставщика

GET-запрос:
```
GET {{baseUrl}}/api/v1/partner/orders
Content-Type: application/json
Authorization: Token "my_token"
```
### Описание:
Просмотр заказов.

### Обновление статуса заказа

POST-запрос:
```
POST {{baseUrl}}/api/v1/partner/status/<order_items_id>
Content-Type: application/json
Authorization: Token "my_token"

{
    "status":"status"
}
```
Обязательно требуется order_id (id заказа).

### Описание полей:
Обязательные поля:
- status - новый статус заказа. Доступны следующие статусы:
    - new - Новый,
    - confirmed - Подтвержден,
    - assembled - Собран,
    - sent - Отправлен,
    - delivered - Доставлен,
    - canceled - Отменен.




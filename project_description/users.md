# Регистрация, авторизация и восстановление авторизационных данных

[Главная страница](../README.md)

[Содержание](../project_description/info.md)


## Описание

Данное приложение предназначено для первичноого взаимодействия с пользователем.
В него входит следующий функционал:
- регистрация (с последующим подтверждением почты):
  - как клиент (buyer),
  - как поставщик (shop).
- авторизация,
- изменение текущего пароля,
- восстановление пароля,
- изменение текущей почты (с последующим подтверждением почты),
- просмотр деталей аккаунта пользователя.

## Разделы:
В каждом разделе будут указаны HTTP-запросы необходимые для взаимодействия с API, 
указаны все обязательные и необязательные для заполнения поля и их описание.

**baseUrl** - Базовый путь приложения
### Регистрация

POST-запрос:
```
POST {{baseUrl}}/api/v1/user/register/
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

### Подтверждение электронной почты

POST-запрос:
```
POST {{baseUrl}}/api/v1/user/register/confirm
Content-Type: application/json

{
  "email": "email",
  "password": "password",
  "code":"code"
}
```
#### Описание полей:
- Обязательные поля:
  - email,
  - password,
  - code - код из письма на электронную почту, необходимый для верификации. 

### Авторизация

POST-запрос:
```
POST {{baseUrl}}/api/v1/user/login
Content-Type: application/json

{
  "email": "email",
  "password": "password"
}
```
#### Описание полей:
- Обязательные поля - **все.**
- 
В качестве ответа вы получите уникальный ключ (далее **"my_token"**), для авторизации в приложении. 


### Смена пароля

POST-запрос:
```
POST {{baseUrl}}/api/v1/user/password_change
Content-Type: application/json
Authorization: Token "my_token"
{
  "old_password": "old_password",
  "new_password": "new_password"
}
```
#### Описание полей:
- Обязательные поля:
  - old_password - действующий пароль,
  - new_password - новый пароль.

### Восстановление пароля

POST-запрос:
```
POST {{baseUrl}}/api/v1/user/password_reset
Content-Type: application/json

{
  "email": "email"
}
```
#### Описание полей:
- Обязательные поля:
  - email - зарегистрированный адрес электронной почты.

### Смена адреса электронной почты

POST-запрос:
```
POST {{baseUrl}}/api/v1/user/email_change
Content-Type: application/json
Authorization: Token "my_token"

{
  "new_email": "new_email"
}
```
#### Описание полей:
- Обязательные поля:
  - new_email - новый адрес электронной почты.

### Подтверждение нового адреса электронной почты

POST-запрос:
```
POST {{baseUrl}}/api/v1/user/email_change/confirm
Content-Type: application/json
Authorization: Token "my_token"

{
  "new_email": "new_email",
  "code": "code"
}
```
#### Описание полей:
- Обязательные поля:
  - new_email - новый адрес электронной почты,
  - code - код из письма на электронную почту, необходимый для подтверждения нового адреса. 

### Просмотр деталей аккаунта пользователя

GET-запрос:
```
GET {{baseUrl}}/api/v1/user/details
Content-Type: application/json
Authorization: Token "my_token"
```

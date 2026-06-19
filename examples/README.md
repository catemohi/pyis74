# Примеры pyis74

Каталог содержит небольшие сценарии для проверки авторизации и базовых данных аккаунта.
Все секреты передаются через переменные окружения.

## Переменные

Для авторизации по логину и паролю:

```bash
export IS74_LOGIN="login"
export IS74_PASSWORD="password"
```

Для авторизации по телефону:

```bash
export IS74_PHONE="+79123456789"
```

Опционально можно зафиксировать device id:

```bash
export IS74_DEVICE_ID="my-device-id"
```

Для запросов аккаунта можно передать уже полученный mobile token:

```bash
export IS74_MOBILE_TOKEN="token"
```

Если `IS74_MOBILE_TOKEN` не задан, примеры аккаунта попробуют авторизоваться через
`IS74_LOGIN` и `IS74_PASSWORD`.

## Запуск

```bash
uv run python examples/login_password.py
uv run python examples/phone_auth.py
uv run python examples/check_addresses.py
uv run python examples/check_balance.py
```

`phone_auth.py` выводит список адресов после подтверждения телефона и получает token
для выбранного адреса. Этот token можно сохранить в `IS74_MOBILE_TOKEN` для следующих
примеров.

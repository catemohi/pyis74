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

Для открытия домофонного реле:

```bash
export IS74_RELAY_ID="900001"
export IS74_CONFIRM_OPEN="yes"
```

## Запуск

```bash
uv run python examples/login_password.py
uv run python examples/phone_auth.py
uv run python examples/check_addresses.py
uv run python examples/check_balance.py
uv run python examples/inspect_domofon_relays.py
uv run python examples/list_domofon_relays.py
uv run python examples/open_domofon_relay.py
```

`phone_auth.py` выводит список адресов после подтверждения телефона и получает token
для выбранного адреса. Этот token можно сохранить в `IS74_MOBILE_TOKEN` для следующих
примеров.

`inspect_domofon_relays.py` печатает сырой JSON ответа `/domofon/relays`. Этот пример
нужен перед реализацией доменного API домофона, чтобы зафиксировать реальные поля ответа.

`list_domofon_relays.py` печатает типизированный список реле. `open_domofon_relay.py`
открывает реле по `IS74_RELAY_ID` и требует `IS74_CONFIRM_OPEN=yes`, чтобы случайный
запуск не отправил команду открытия.

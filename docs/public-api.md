# Публичные методы pyis74

Документ описывает публичный API библиотеки: зачем нужны методы, какие данные они
принимают и что возвращают. Все примеры данных ниже выдуманы и не относятся к реальным
аккаунтам IS74.

## Общие правила

Основная точка входа - `IS74Async`. Для простых скриптов есть синхронная обертка
`IS74`. Синхронный клиент предоставляет те же домены и методы, но без `await`.

```python
from pyis74 import IS74Async


async with IS74Async(mobile_token="mobile-token-example") as client:
    balance = await client.account.get_balance()
    print(balance.balance)
```

Если API доступен на другом домене с теми же service-prefix, задайте домен при
инициализации:

```python
async with IS74Async(base_domain="is74.example", mobile_token="mobile-token-example") as client:
    groups = await client.cameras.get_groups()
```

При `base_domain="is74.example"` клиент строит URL вида
`https://api.is74.example`, `https://cams.is74.example`,
`https://td-crm.is74.example`.

```python
from pyis74 import IS74


client = IS74(mobile_token="mobile-token-example")
balance = client.account.get_balance()
print(balance.balance)
```

Модели возвращают нормализованные поля и сохраняют исходный JSON в поле `raw`. Поле
`raw` полезно, когда API вернул новые поля, которые библиотека еще не типизировала.
Не логируйте `raw` без анонимизации: там могут быть адреса, id, token и подписанные
media URL.

## Клиенты

### `IS74Async(...)`

Асинхронный клиент верхнего уровня. Создает HTTP transport, хранит mobile token и LK
token, открывает доступ к доменам `auth`, `account`, `domofon`, `history`, `cameras`.

Принимает:

- `transport: IS74Transport | None` - готовый transport для тестов или особой сетевой
  конфигурации.
- `timeout: float` - таймаут запроса в секундах.
- `max_retries: int` - количество повторных попыток после первого запроса.
- `backoff_factor: float` - базовая задержка между повторами.
- `base_domain: str` - корневой домен IS74. По умолчанию `is74.ru`.
- `mobile_token: str | None` - уже полученный mobile access token.

Возвращает экземпляр клиента. Клиент поддерживает async context manager и метод
`aclose()`.

### `IS74(...)`

Синхронная обертка над `IS74Async`. Подходит для CLI-скриптов и простых интеграций без
собственного event loop.

Принимает:

- `timeout: float`
- `max_retries: int`
- `backoff_factor: float`
- `base_domain: str`
- `mobile_token: str | None`
- `lk_token: str | None`

Возвращает экземпляр клиента. Если вызвать синхронный клиент внутри уже работающего
event loop, будет поднят `IS74Error`; в таком коде нужно использовать `IS74Async`.

### Token helpers

`mobile_token`, `set_mobile_token(token)`, `clear_mobile_token()` управляют token для
mobile API и camera API текущего домена клиента.

`lk_token`, `set_lk_token(token)`, `clear_lk_token()` управляют token для CRM/LK API.
Если LK token нужен, но еще не задан, методы `request_lk`, `history.get_events()` и
CRM-открытие домофона попробуют получить его через текущий mobile token.

### URL configuration

`IS74Async(..., base_domain="...")` и `IS74(..., base_domain="...")` задают корневой
домен для high-level методов и low-level запросов с `BaseUrl.*`.

```python
from pyis74 import BaseUrl, ClientRequestOptions, IS74Async


async with IS74Async(base_domain="is74.example") as client:
    payload = await client.request(
        "GET",
        "/api/self-cams-with-group",
        ClientRequestOptions(base_url=BaseUrl.CAMS),
    )
```

Этот пример отправит запрос на `https://cams.is74.example/api/self-cams-with-group`.
Если в `target` передан абсолютный URL, клиент использует его без пересборки. Это
нужно для ссылок `LINKS.open` и signed media URL, которые API возвращает уже готовыми.

`client.urls` возвращает `IS74ServiceUrls` - frozen-объект с вычисленными URL сервисов
и endpoint:

```python
print(client.urls.api)
print(client.urls.crm_history)
```

### Low-level requests

Методы `request`, `request_mobile`, `request_lk` нужны для экспериментов с еще не
типизированными endpoint.

```python
from pyis74.options import ClientRequestOptions


payload = await client.request_mobile(
    "GET",
    "/user/info",
    ClientRequestOptions(headers={"Accept": "application/json"}),
)
```

Принимают:

- `method: str` - HTTP-метод.
- `target: str` - относительный endpoint или абсолютный URL.
- `options: ClientRequestOptions | None`.

`ClientRequestOptions` принимает:

- `base_url: BaseUrl | str`
- `auth_token: str | None`
- `headers: dict[str, str] | None`
- `params: dict[str, str | int | float | bool | None] | None`
- `json_body: JsonValue | None`
- `form: dict[str, str] | None`
- `content: str | bytes | None`
- `max_retries: int | None` - request-level override для retry. Если `None`,
  используется настройка transport.

Возвращают `JsonValue`: `str`, `int`, `float`, `bool`, `None`, список или словарь с
такими значениями.

## Авторизация: `client.auth`

### `login_with_password(username, password)`

Авторизуется по логину и паролю и сохраняет mobile token внутри клиента.

Принимает:

- `username: str` - логин учетной записи.
- `password: str` - пароль.

Возвращает `MobileToken`.

```python
token = await client.auth.login_with_password("demo-login", "demo-password")
print(token.token)
```

Пример данных `MobileToken`:

```json
{
  "token": "mobile-token-example",
  "expires_at": "2026-12-31T23:59:59+00:00",
  "raw": {
    "TOKEN": "mobile-token-example",
    "ACCESS_END": "2026-12-31T23:59:59Z"
  }
}
```

### `request_phone_confirmation(phone, device_id=None)`

Начинает авторизацию по телефону. API отправляет код подтверждения или инициирует
другой сценарий подтверждения, зависящий от текущего приложения IS74.

Принимает:

- `phone: str` - номер телефона в виде `+79990000000`, `79990000000` или
  `89990000000`.
- `device_id: str | None` - идентификатор устройства. Если не передан, библиотека
  сгенерирует UUID-like строку.

Возвращает `PhoneConfirmationStart`.

```python
start = await client.auth.request_phone_confirmation("+79990000000")
print(start.device_id)
```

Пример данных:

```json
{
  "device_id": "00000000000040008000000000000001",
  "auth_id": "auth-session-example",
  "raw": {
    "authId": "auth-session-example"
  }
}
```

### `check_phone_confirmation(phone, code, device_id=...)`

Проверяет код подтверждения и возвращает список адресов, доступных для выбора.

Принимает:

- `phone: str` - тот же номер телефона.
- `code: str` - код подтверждения.
- `device_id: str` - идентификатор устройства из `request_phone_confirmation`.

Возвращает `PhoneConfirmationCheck`.

```python
check = await client.auth.check_phone_confirmation(
    "+79990000000",
    "1234",
    device_id=start.device_id,
)
for address in check.addresses:
    print(address.user_id, address.address)
```

Пример данных:

```json
{
  "auth_id": "auth-session-example",
  "addresses": [
    {
      "user_id": 900001,
      "address": "Тестоград, ул. Примерная, д. 10",
      "raw": {
        "USER_ID": 900001,
        "ADDRESS": "Тестоград, ул. Примерная, д. 10"
      }
    }
  ],
  "raw": {
    "authId": "auth-session-example",
    "addresses": [
      {
        "USER_ID": 900001,
        "ADDRESS": "Тестоград, ул. Примерная, д. 10"
      }
    ]
  }
}
```

### `get_token_for_user(auth_id=..., user_id=..., device_id=None)`

Получает mobile token для выбранного адреса после телефонной авторизации и сохраняет
его внутри клиента.

Принимает:

- `auth_id: str` - auth-сессия из `check_phone_confirmation`.
- `user_id: int` - `USER_ID` выбранного адреса.
- `device_id: str | None` - оставлен для совместимости; текущий endpoint token не
  требует его в payload.

Возвращает `MobileToken`.

### `get_lk_token(buyer_id=1)`

Получает CRM/LK token по текущему mobile token и сохраняет его внутри клиента. Нужен
для CRM endpoints: история событий и часть ссылок открытия домофона.

Принимает:

- `buyer_id: int` - значение `buyerId` для CRM auth endpoint.

Возвращает `LkToken`.

```python
lk_token = await client.auth.get_lk_token()
print(lk_token.expires_at)
```

Пример данных:

```json
{
  "token": "lk-token-example",
  "expires_at": "2026-12-31T23:59:59+00:00",
  "raw": {
    "token": "lk-token-example",
    "ACCESS_END": "2026-12-31T23:59:59Z"
  }
}
```

### `generate_device_id()` и `normalize_phone(phone)`

Вспомогательные публичные функции из `pyis74.auth`.

`generate_device_id()` возвращает случайный идентификатор устройства.

`normalize_phone(phone)` нормализует российский номер к формату `7XXXXXXXXXX`.

```python
from pyis74.auth import generate_device_id, normalize_phone


device_id = generate_device_id()
phone = normalize_phone("+79990000000")
```

## Аккаунт: `client.account`

Все методы аккаунта требуют mobile token.

### `get_service_status()`

Возвращает статус сервисов текущего пользователя.

Принимает: нет аргументов.

Возвращает `ServiceStatus`.

Пример данных:

```json
{
  "status": "active",
  "description": "Услуги активны",
  "title": "Работает",
  "deep_link": null,
  "deep_link_text": null,
  "type_button": null
}
```

### `get_user()`

Возвращает информацию о текущем пользователе.

Принимает: нет аргументов.

Возвращает `UserInfo`.

```json
{
  "user_id": 900001,
  "full_name": "Иванов Иван Иванович",
  "short_name": "Иван И.",
  "login": "demo-login",
  "account_number": 700001,
  "birth_date": "1990-01-01"
}
```

### `get_address()`

Возвращает идентификаторы адреса установки услуг.

Принимает: нет аргументов.

Возвращает `Address`.

```json
{
  "user_id": 900001,
  "flat_id": 910001,
  "building_id": 920001,
  "street_id": 930001,
  "city_id": 940001,
  "entrance_id": 950001
}
```

### `get_balance()`

Возвращает баланс лицевого счета.

Принимает: нет аргументов.

Возвращает `Balance`.

```json
{
  "balance": "150.25",
  "next_payment": {
    "amount": "900.00",
    "text": "Оплатите до 1 июля"
  },
  "debt": null,
  "blocked": null,
  "date_delay_lock": null
}
```

Числовые денежные значения представлены как `Decimal | None`.

### `get_summary()`

Возвращает сводку аккаунта: `ServiceStatus`, `UserInfo`, `Address`, `Balance`.

Принимает: нет аргументов.

Возвращает `AccountSummary`.

```python
summary = await client.account.get_summary()
print(summary.user.full_name)
print(summary.address.building_id)
print(summary.balance.balance)
```

## Домофоны: `client.domofon`

Все методы домофона требуют mobile token. CRM-реле дополнительно используют LK token,
который клиент может получить автоматически.

### `get_relays()`

Возвращает все реле, доступные текущему пользователю.

Принимает: нет аргументов.

Возвращает `tuple[DomofonRelay, ...]`.

```python
relays = await client.domofon.get_relays()
for relay in relays:
    print(relay.relay_id, relay.relay_type, relay.opener.type if relay.opener else None)
```

Пример одного `DomofonRelay`:

```json
{
  "relay_id": 900101,
  "relay_descr": "Калитка тестовая",
  "relay_type": "Калитка",
  "address": "Тестоград, ул. Примерная, д. 10",
  "building_id": 920001,
  "entrance_uid": "00000000-0000-4000-8000-000000000001",
  "has_video": true,
  "image_url": "https://example.invalid/snapshot.jpg",
  "is_main": false,
  "smart_intercom": false,
  "mac_addr": "02:00:00:00:01:01",
  "porch_num": "1",
  "status_code": "0",
  "status_text": "OK",
  "links": {
    "open_url": "https://api.is74.ru/domofon/relays/900101/open"
  },
  "opener": {
    "mac": "02:00:00:00:01:01",
    "relay_id": 900101,
    "relay_num": 1,
    "type": "api"
  }
}
```

### `get_relay(relay_id)`

Возвращает одно реле по `RELAY_ID`.

Принимает:

- `relay_id: int`

Возвращает `DomofonRelay`.

### `open_relay(relay, from_app=True)`

Открывает уже загруженный объект `DomofonRelay`.

Зачем нужен этот метод: разные реле могут открываться через разные backend. Если у
реле есть `LINKS.open`, метод использует именно эту ссылку. Для mobile API текущего
домена будет выполнен mobile `POST`; для CRM API текущего домена будет получен LK token
и выполнен CRM `GET`.

Принимает:

- `relay: DomofonRelay`
- `from_app: bool` - добавлять `from=app` для mobile API-open.

Возвращает `DomofonOpenResult`.

Запросы открытия являются side-effect операциями, поэтому библиотека принудительно
отключает retry для HTTP-запроса открытия. Успешный HTTP-статус означает только то, что
backend принял запрос; физическое открытие реле нужно проверять отдельно.

```python
relay = (await client.domofon.get_relays())[0]
result = await client.domofon.open_relay(relay)
print(result.status_code)
```

Пример результата:

```json
{
  "status_code": 204,
  "payload": null,
  "response_text": ""
}
```

### `open_relay_by_id(relay_id, from_app=True)`

Основной метод открытия по id. Сначала загружает список реле, находит объект по
`RELAY_ID`, затем делегирует открытие в `open_relay()`. Это сохраняет различие между
API-реле и CRM-реле.

Принимает:

- `relay_id: int`
- `from_app: bool`

Возвращает `DomofonOpenResult`.

### `open_relay_by_api_id(relay_id, from_app=True)`

Диагностический метод. Не читает `LINKS.open` и всегда вызывает прямой endpoint
`/domofon/relays/{relay_id}/open`.

Принимает:

- `relay_id: int`
- `from_app: bool`

Возвращает `DomofonOpenResult`.

Используйте его для проверки direct mobile API. Для CRM-реле основной путь -
`open_relay_by_id()`.

### `get_relay_cameras()`

Возвращает домофонные реле вместе с камерами, найденными по `ENTRANCE_UID`.

Зачем нужен этот метод: `limited-info-by-uuid` возвращает камеры по UUID подъезда, но
batch-ответ не содержит исходный UUID запроса. Поэтому high-level метод сохраняет
связку `relay -> cameras` сам и делает отдельный limited-info запрос для каждого
уникального `ENTRANCE_UID`.

Принимает: нет аргументов.

Возвращает `tuple[DomofonRelayCameras, ...]`.

```python
relay_cameras = await client.domofon.get_relay_cameras()
for item in relay_cameras:
    print(item.relay.relay_id, len(item.cameras))
```

Пример данных `DomofonRelayCameras`:

```json
{
  "relay": {
    "relay_id": 900101,
    "relay_type": "Калитка",
    "entrance_uid": "00000000-0000-4000-8000-000000000001"
  },
  "cameras": [
    {
      "camera_id": 910201,
      "uuid": "00000000-0000-4000-8000-000000000201",
      "name": "Домофонная камера"
    }
  ]
}
```

### `get_cameras_for_relays(relays)`

То же, что `get_relay_cameras()`, но принимает уже загруженные реле. Метод полезен,
если список реле уже получен раньше и не нужно повторять `GET /domofon/relays`.

Принимает:

- `relays: Iterable[DomofonRelay]`

Возвращает `tuple[DomofonRelayCameras, ...]`.

## История: `client.history`

### `get_events(from_date=None, to_date=None, page=None, per_page=None)`

Возвращает страницу истории событий из CRM API. Метод использует LK token; если его нет,
клиент попробует получить LK token через текущий mobile token.

Принимает:

- `from_date: date | str | None` - начальная дата в формате `YYYY-MM-DD` или `date`.
- `to_date: date | str | None` - конечная дата.
- `page: int | None` - номер страницы.
- `per_page: int | None` - размер страницы.

Возвращает `HistoryResponse`.

```python
events = await client.history.get_events(
    from_date="2026-06-01",
    to_date="2026-06-19",
    page=1,
    per_page=20,
)
for event in events.events:
    print(event.kind, event.event_type, event.created_at)
```

Пример данных:

```json
{
  "events": [
    {
      "create_date": "2026-06-19T10:15:00Z",
      "created_at": "2026-06-19T10:15:00+00:00",
      "event_type": "OPEN_API",
      "kind": "open",
      "params": {
        "mac": "02:00:00:00:01:01",
        "address": "Тестоград, ул. Примерная, д. 10",
        "entrance_title": "Подъезд 1"
      },
      "image_link": "https://example.invalid/history/snapshot.jpg"
    }
  ],
  "page": 1,
  "per_page": 20,
  "count": 1
}
```

`HistoryEvent.kind` нормализует исходный `event_type` в одну из категорий:

- `HistoryEventKind.OPEN` / `"open"` - события открытия;
- `HistoryEventKind.CALL` / `"call"` - звонки;
- `HistoryEventKind.OTHER` / `"other"` - остальные события.

Также доступны быстрые признаки `event.is_open` и `event.is_call`.

### `get_events_until_limit(limit, from_date=None, to_date=None, start_page=1, per_page=20)`

Последовательно читает страницы истории через `get_events()` и останавливается, когда
собрано `limit` событий, API вернул пустую страницу или по данным `count`/размеру
страницы видно, что следующей страницы нет.

Принимает:

- `limit: int` - максимальное количество событий.
- `from_date: date | str | None`
- `to_date: date | str | None`
- `start_page: int`
- `per_page: int`

Возвращает `tuple[HistoryEvent, ...]`.

```python
events = await client.history.get_events_until_limit(limit=50, per_page=20)
for event in events:
    print(event.kind.value, event.created_at)
```

Если `limit`, `start_page` или `per_page` меньше `1`, будет поднят `ValueError`.

### `get_recent_activity(...)`

Возвращает события текущей страницы, отфильтрованные как последние открытия и звонки.
Метод получает страницу через `get_events()`, затем локально применяет
`HistoryResponse.filter_events()`.

Принимает те же параметры страницы и дат, что `get_events()`, плюс:

- `event_types: Iterable[str]` - точные типы API, например `OPEN_API`.
- `kinds: Iterable[HistoryEventKind | str]` - категории `open`, `call`, `other`.
  По умолчанию `open` и `call`.
- `with_images: bool | None` - если задано, фильтровать по наличию `image_link`.

Возвращает `tuple[HistoryEvent, ...]`.

```python
activity = await client.history.get_recent_activity(per_page=20)
for event in activity:
    print(event.kind.value, event.event_type, event.create_date)
```

### `HistoryResponse.filter_events(...)`

Фильтрует уже полученные события страницы без дополнительного HTTP-запроса.

```python
history = await client.history.get_events(per_page=50)
open_events = history.filter_events(kinds=("open",))
events_with_snapshots = history.filter_events(with_images=True)
```

## Камеры: `client.cameras`

Все методы камер требуют mobile token. Media-ссылки из camera API могут быть
подписанными ссылками прямого доступа к live, архиву или snapshot. Не сохраняйте их в
публичные логи и документацию.

Подписанные stream/snapshot URL нужно считать временными credential-like значениями.
Точный срок жизни URL задает backend и библиотека его не гарантирует. Если плеер или
загрузчик получает ошибку доступа, истечения срока или недоступности media, запросите
свежие данные camera API и используйте новый URL.

### `get_self_cams_with_group()`

Возвращает группы камер, доступные текущему пользователю.

Принимает: нет аргументов.

Возвращает `tuple[SelfCameraGroup, ...]`.

```python
groups = await client.cameras.get_self_cams_with_group()
for group in groups:
    print(group.group_id, len(group.cameras))
```

Пример `SelfCameraGroup`:

```json
{
  "group_id": "920001",
  "group_name": "Тестовый дом",
  "is_management_company_owns": true,
  "cameras": [
    {
      "camera_id": 910101,
      "uuid": "00000000-0000-4000-8000-000000000101",
      "name": "Тестовая камера 1",
      "object_type": "CAMERA"
    }
  ]
}
```

### `get_groups(self_cams=False)`

Возвращает список групп camera API.

Принимает:

- `self_cams: bool` - если `True`, добавляет `selfCams=true` и включает служебную
  группу собственных камер, если API ее возвращает.

Возвращает `tuple[CameraGroup, ...]`.

```json
[
  {
    "group_id": "own",
    "name": "Свои камеры",
    "object_type": "GROUP"
  },
  {
    "group_id": "920001",
    "name": "Тестовый дом",
    "object_type": "GROUP"
  }
]
```

### `get_group(group_id)`

Возвращает содержимое группы камер. Endpoint может вернуть смешанный список дочерних
групп и камер, поэтому библиотека разделяет их.

Принимает:

- `group_id: int | str` - id из `get_groups()` или `get_self_cams_with_group()`.

Возвращает `CameraGroupContent`.

```python
content = await client.cameras.get_group("920001")
print(len(content.groups), len(content.cameras))
```

Пример данных:

```json
{
  "groups": [
    {
      "group_id": "920002",
      "name": "Подгруппа",
      "object_type": "GROUP"
    }
  ],
  "cameras": [
    {
      "camera_id": 910101,
      "uuid": "00000000-0000-4000-8000-000000000101",
      "name": "Тестовая камера 1",
      "address": "Тестоград, ул. Примерная, д. 10",
      "access": {
        "live": {
          "status": true,
          "reason": "",
          "audio": null
        },
        "archive": {
          "status": true,
          "reason": "",
          "audio": false
        }
      },
      "media": {
        "hls": {
          "live": {
            "main": "https://example.invalid/hls/live.m3u8?token=stream-token-example",
            "low_latency": "https://example.invalid/hls/live.m3u8?realtime=1&token=stream-token-example"
          },
          "archive": "https://example.invalid/hls/archive.m3u8?token=stream-token-example"
        },
        "mse": {
          "live": "wss://example.invalid/ws/mse?token=stream-token-example"
        },
        "snapshot": {
          "live": {
            "main": "https://example.invalid/snapshot.jpg?token=stream-token-example",
            "lossy": "https://example.invalid/snapshot_lossy.jpg?token=stream-token-example"
          }
        }
      },
      "supported_features": {
        "doorbell": false,
        "ptz": false,
        "setup_motion_detect": true,
        "voice": false,
        "zoom": false
      }
    }
  ]
}
```

### `Camera.streams`

У каждой модели `Camera` есть свойство `streams`, которое собирает разбросанные по
ответу API stream URL в один объект `CameraStreams`.

`CameraStreams` содержит поля:

- `hls_live_main`
- `hls_live_low_latency`
- `hls_archive`
- `mse_live`
- `snapshot_live_main`
- `snapshot_live_lossy`
- `realtime_ws_combined`
- `realtime_ws_main`
- `realtime_ws_sub`

Метод `items()` возвращает только непустые URL с устойчивыми именами полей. Свойство
`has_any` показывает, есть ли хотя бы один URL.

```python
camera = content.cameras[0]
for name, url in camera.streams.items():
    print(name, url)
```

Пример данных:

```json
{
  "hls_live_main": "https://example.invalid/hls/live.m3u8?token=stream-token-example",
  "hls_live_low_latency": "https://example.invalid/hls/live.m3u8?realtime=1&token=stream-token-example",
  "hls_archive": "https://example.invalid/hls/archive.m3u8?token=stream-token-example",
  "mse_live": "wss://example.invalid/ws/mse?token=stream-token-example",
  "snapshot_live_main": "https://example.invalid/snapshot.jpg?token=stream-token-example",
  "snapshot_live_lossy": "https://example.invalid/snapshot_lossy.jpg?token=stream-token-example",
  "realtime_ws_combined": "wss://example.invalid/ws/mse?token=stream-token-example",
  "realtime_ws_main": "wss://example.invalid/ws/mse?token=stream-token-example&quality=main",
  "realtime_ws_sub": "wss://example.invalid/ws/mse?token=stream-token-example&quality=sub"
}
```

### `get_limited_info_by_uuid(camera_uuid)`

Возвращает limited camera info по одному UUID. Практический сценарий - взять
`ENTRANCE_UID` из `DomofonRelay` и получить связанную домофонную камеру.

Принимает:

- `camera_uuid: str`

Возвращает `CameraLimitedInfo`.

```python
info = await client.cameras.get_limited_info_by_uuid(
    "00000000-0000-4000-8000-000000000001"
)
print(len(info.cameras))
```

### `get_limited_info_by_uuids(camera_uuids)`

Batch-вариант limited-info запроса. Отправляет form-urlencoded payload с повторяющимся
ключом `CAMERA_UUIDS[]`.

Принимает:

- `camera_uuids: Iterable[str]`

Возвращает `CameraLimitedInfo`. Если передан пустой набор UUID, возвращает пустой
результат без HTTP-запроса.

```python
relays = await client.domofon.get_relays()
uuids = [relay.entrance_uid for relay in relays if relay.entrance_uid]
info = await client.cameras.get_limited_info_by_uuids(uuids)
```

Пример `CameraLimitedInfo`:

```json
{
  "cameras": [
    {
      "camera_id": 910201,
      "uuid": "00000000-0000-4000-8000-000000000201",
      "name": "Домофонная камера",
      "hls": "/live/cam910201-master.m3u8",
      "realtime_hls": "/live/cam910201-realtime-master.m3u8"
    }
  ],
  "raw": {
    "910201": {
      "ID": 910201,
      "UUID": "00000000-0000-4000-8000-000000000201",
      "OBJECT": "CAMERA",
      "NAME": "Домофонная камера"
    }
  }
}
```

## Исключения

Основные исключения находятся в `pyis74.exceptions`:

- `IS74Error` - базовая ошибка библиотеки.
- `IS74TransportError` - ошибка transport или некорректный JSON.
- `IS74HTTPError` - API вернул HTTP-ошибку.
- `IS74AuthError` - API вернул `401` или `403`.
- `IS74AuthRequiredError` - метод требует token, которого нет в клиенте.
- `IS74APIError` - ответ API имеет неожиданную структуру.

## Что считается публичным API

Стабильной пользовательской поверхностью считаются:

- `IS74Async`, `IS74`;
- домены `auth`, `account`, `domofon`, `history`, `cameras`;
- модели из `pyis74.models`;
- `ClientRequestOptions`;
- `BaseUrl` и `IS74ServiceUrls`;
- исключения из `pyis74.exceptions`;
- типы `JsonValue`, `JsonObject`, `QueryParams`.

Функции парсинга и построения URL внутри доменных модулей могут использоваться в тестах,
но до версии `1.0.0` не считаются стабильным пользовательским контрактом.

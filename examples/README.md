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

Для интерактивной отладки можно использовать короткий alias:

```bash
export RELAY_ID="900001"
```

`IS74_RELAY_ID` имеет приоритет над `RELAY_ID`.

Для direct API открытия можно отключить query-параметр `from=app`:

```bash
export IS74_FROM_APP="no"
```

Для истории событий можно задать фильтр и пагинацию:

```bash
export IS74_HISTORY_FROM="2026-06-01"
export IS74_HISTORY_TO="2026-06-19"
export IS74_HISTORY_PAGE="1"
export IS74_HISTORY_PER_PAGE="20"
```

Для диагностики камер можно ограничить детальный обход групп или указать конкретные
значения:

```bash
export IS74_CAMERA_GROUP_LIMIT="5"
export IS74_CAMERA_GROUP_ID="1000"
export IS74_CAMERA_UUIDS="00000000-0000-4000-8000-000000000001"
```

`IS74_CAMERA_UUIDS` принимает несколько UUID через запятую.

Диагностические inspect-примеры по умолчанию печатают безопасную структурную сводку.
Для вывода сырого JSON нужно явно включить raw-режим:

```bash
export IS74_RAW_JSON="yes"
```

Raw-вывод может содержать адреса, UUID, MAC-адреса, id устройств, подписанные media URL
и token-подобные значения. Его нельзя сохранять в публичные документы, тесты или
fixtures без анонимизации.

Для проверки альтернативного CRM user-device endpoint можно задать:

```bash
export IS74_USER_DEVICE_ENDPOINT="https://td-crm.is74.ru/api/example-device-path"
```

Для обычных camera-примеров приватные поля скрыты по умолчанию. Если нужно увидеть id,
UUID, названия и адреса в runtime-выводе, включите:

```bash
export IS74_SHOW_PRIVATE_CAMERA_FIELDS="yes"
```

Для вывода подписанных stream/snapshot URL нужно отдельное подтверждение:

```bash
export IS74_CONFIRM_PRINT_CAMERA_STREAMS="yes"
```

Опционально можно ограничить количество камер в stream-примере:

```bash
export IS74_CAMERA_LIMIT="3"
```

## Запуск

```bash
uv run python examples/login_password.py
uv run python examples/login_lk.py
uv run python examples/phone_auth.py
uv run python examples/check_addresses.py
uv run python examples/check_balance.py
uv run python examples/get_intercom_cameras.py
uv run python examples/inspect_domofon_relays.py
uv run python examples/inspect_domofon_relay.py
uv run python examples/inspect_cameras.py
uv run python examples/inspect_user_device.py
uv run python examples/list_camera_groups.py
uv run python examples/list_cameras.py
uv run python examples/list_domofon_relays.py
uv run python examples/list_history.py
uv run python examples/list_recent_activity.py
uv run python examples/open_domofon_relay.py
uv run python examples/open_domofon_relay_api.py
uv run python examples/print_camera_streams.py
```

`phone_auth.py` выводит список адресов после подтверждения телефона и получает token
для выбранного адреса. Этот token можно сохранить в `IS74_MOBILE_TOKEN` для следующих
примеров.

`login_lk.py` получает CRM/LK token через текущий mobile token. Он нужен для части
`td-crm.is74.ru` методов, включая CRM-ссылки открытия из домофонного API.

`list_history.py` получает историю событий через CRM/LK API
`GET https://td-crm.is74.ru/api/user/history`. Пример поддерживает фильтры
`IS74_HISTORY_FROM`, `IS74_HISTORY_TO`, `IS74_HISTORY_PAGE` и
`IS74_HISTORY_PER_PAGE`. Если LK token еще не получен, клиент получает его через
текущий mobile token.

`list_recent_activity.py` получает страницу истории и локально фильтрует последние
открытия и звонки. По умолчанию используются категории `open,call`. Для точных типов
API задайте `IS74_HISTORY_EVENT_TYPES`, например `OPEN_API,HANDSET_CALL`. Для
нормализованных категорий задайте `IS74_HISTORY_EVENT_KINDS`, например `open,call`.
Фильтр по наличию snapshot включается через `IS74_HISTORY_WITH_IMAGES=yes` или
`IS74_HISTORY_WITH_IMAGES=no`.

`inspect_domofon_relays.py` печатает сырой JSON ответа `/domofon/relays`. Этот пример
нужен перед реализацией доменного API домофона, чтобы зафиксировать реальные поля ответа.

`inspect_user_device.py` проверяет известные кандидаты CRM user-device endpoints через
CRM/LK token и не падает, если endpoint возвращает `404`. Текущий
`GET https://td-crm.is74.ru/api/user-device` может быть недоступен для аккаунта или
не совпадать с endpoint, который использует актуальное приложение. Для проверки нового
пути используйте `IS74_USER_DEVICE_ENDPOINT`.

`inspect_cameras.py` читает camera endpoints и по умолчанию печатает только безопасную
сводку: количество объектов, наборы полей, доступность media-ссылок и access-флаги.
Сырые ответы доступны только при `IS74_RAW_JSON=yes`. Проверяемые endpoints:

- `GET https://cams.is74.ru/api/self-cams-with-group`;
- `GET https://cams.is74.ru/api/get-group/`;
- `GET https://cams.is74.ru/api/get-group/?selfCams=true`;
- `GET https://cams.is74.ru/api/get-group/{group_id}`;
- `POST https://cams.is74.ru/api/limited-info-by-uuid`.

Для `/limited-info-by-uuid` пример автоматически берет `ENTRANCE_UID` из
`/domofon/relays` и дополнительно использует UUID из `IS74_CAMERA_UUIDS`. Автообход
групп берет только объекты с `OBJECT=GROUP` и группы из `/self-cams-with-group`, чтобы
не принимать camera `ID` за group id.

`list_camera_groups.py` использует типизированный `client.cameras.get_groups()` и
`client.cameras.get_groups(self_cams=True)`. По умолчанию выводит только счетчики и
тип объекта. Id и названия групп печатаются только при
`IS74_SHOW_PRIVATE_CAMERA_FIELDS=yes`.

`list_cameras.py` использует `client.cameras.get_self_cams_with_group()` и печатает
безопасную сводку по доступности live/archive/movement и наличию HLS/MSE/snapshot.
Названия, UUID, id и адреса скрыты без `IS74_SHOW_PRIVATE_CAMERA_FIELDS=yes`.

`get_intercom_cameras.py` использует `client.domofon.get_relay_cameras()` и печатает
связку `relay -> cameras`. По умолчанию выводит только счетчики и безопасные флаги.
Названия, UUID, id и адреса скрыты без `IS74_SHOW_PRIVATE_CAMERA_FIELDS=yes`.

`print_camera_streams.py` печатает подписанные stream/snapshot URL из camera API.
Этот пример требует `IS74_CONFIRM_PRINT_CAMERA_STREAMS=yes`, потому что ссылки могут
давать прямой доступ к live-видео, архиву или snapshot.
Ссылки нужно считать временными credential-like значениями: при ошибках доступа или
истечении срока действия запрашивайте свежие данные camera API, а не переиспользуйте
старую сохраненную ссылку.

## Открытие домофонных реле

В библиотеке есть два разных сценария открытия. Они похожи по названию, но проверяют
разные HTTP-пути.

### `open_domofon_relay.py`

Это основной пользовательский пример. Он повторяет логику метода
`DomofonAPI.open_relay_by_id()`:

1. Авторизуется и получает mobile token.
2. Запрашивает `GET https://api.is74.ru/domofon/relays`.
3. Находит объект реле по `RELAY_ID`.
4. Берет из объекта поле `LINKS.open`.
5. Выбирает способ открытия по типу ссылки:
   - для `https://api.is74.ru/domofon/relays/.../open` делает mobile `POST`;
   - для `https://td-crm.is74.ru/api/open/...` получает LK token через
     `POST https://td-crm.is74.ru/api/auth-lk`, затем делает CRM `GET`.

Этот путь нужен потому, что разные реле в одном аккаунте могут открываться через разные
backend-сервисы. Для реле с opener `crm` нельзя надежно восстановить корректный URL
только по `RELAY_ID`: нужен `LINKS.open` из списка реле.

Пример дополнительно печатает безопасную сводку фактического запроса:

```text
Opening RELAY_ID=900001 from RELAY_ID with opener=crm, link=crm.
Open request status: 204
```

В сводку не выводятся адрес, MAC-адрес контроллера, полный URL и token.

### `open_domofon_relay_api.py`

Это диагностический и fallback-пример. Он не загружает список реле и не использует
`LINKS.open`. Вместо этого он всегда строит canonical API endpoint:

```text
POST https://api.is74.ru/domofon/relays/{relay_id}/open
```

По умолчанию добавляется query-параметр `from=app`, то есть итоговый запрос выглядит
так:

```text
POST https://api.is74.ru/domofon/relays/{relay_id}/open?from=app
```

Для проверки варианта без query-параметра задайте:

```bash
export IS74_FROM_APP="no"
```

Этот пример полезен, когда нужно отделить проблемы `LINKS.open`/CRM/LK-авторизации от
проблем самого direct API. Он может вернуть успешный HTTP-статус, но это не доказывает,
что физическое устройство открылось: финальное подтверждение всегда нужно проверять на
реальном реле.

### Какой пример использовать

Для обычного открытия используйте `open_domofon_relay.py`. Он уважает `LINKS.open` и
умеет выбирать между API и CRM backend.

Для отладки используйте `open_domofon_relay_api.py`. Он проверяет только прямой
`/domofon/relays/{relay_id}/open` endpoint и не подходит как единственный основной путь
для CRM-реле.

Перед live-проверкой лучше сбросить старое значение `IS74_RELAY_ID`, если дальше
используется короткий alias `RELAY_ID`:

```bash
unset IS74_RELAY_ID
export RELAY_ID="900001"
export IS74_CONFIRM_OPEN="yes"
uv run python examples/open_domofon_relay.py
```

`IS74_RELAY_ID` имеет приоритет над `RELAY_ID`, поэтому старое значение
`IS74_RELAY_ID` может привести к тому, что пример откроет не тот relay, который указан
в `RELAY_ID`.

`inspect_domofon_relay.py` печатает сырой JSON ответа `/domofon/relays/{relay_id}`.

# pyis74

[![PyPI version](https://img.shields.io/pypi/v/pyis74.svg)](https://pypi.org/project/pyis74/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyis74.svg)](https://pypi.org/project/pyis74/)
[![CI](https://github.com/catemohi/pyis74/actions/workflows/ci.yml/badge.svg)](https://github.com/catemohi/pyis74/actions/workflows/ci.yml)
[![Release](https://github.com/catemohi/pyis74/actions/workflows/release.yml/badge.svg)](https://github.com/catemohi/pyis74/actions/workflows/release.yml)

`pyis74` - Python-библиотека для работы с API IS74/Интерсвязь.

Проект находится на раннем этапе разработки. Цель библиотеки - предоставить современный,
типизированный и проверяемый клиент для сценариев:

- авторизация в API IS74;
- работа с домофонами;
- открытие двери;
- получение камер и ссылок на видеопотоки;
- получение данных личного кабинета;
- история событий.

## Установка

Пакет опубликован в PyPI: [`pyis74`](https://pypi.org/project/pyis74/).
Стабильные сборки и исходные архивы также доступны в
[GitHub Releases](https://github.com/catemohi/pyis74/releases).

```bash
pip install pyis74
```

Для воспроизводимой установки конкретного релиза:

```bash
pip install pyis74==0.5.1
```

## Требования

- Python `3.14+`.
- Runtime-зависимости минимальны.
- Публичный API будет типизирован.

## Пример

```python
import asyncio

from pyis74 import IS74Async


async def main() -> None:
    async with IS74Async(base_domain="is74.ru") as client:
        await client.auth.login_with_password("login", "password")
        summary = await client.account.get_summary()
        print(summary.user.full_name)
        print(summary.balance.balance)


asyncio.run(main())
```

Синхронный клиент хранит полученный mobile token внутри экземпляра:

```python
from pyis74 import IS74


client = IS74()
client.auth.login_with_password("login", "password")
balance = client.account.get_balance()
print(balance.balance)
```

Больше сценариев есть в каталоге [`examples`](examples/): авторизация через логин/пароль,
phone auth, проверка адреса, проверка баланса, история событий и camera API.

Документация публичных методов находится в [`docs/public-api.md`](docs/public-api.md):
там описаны входные параметры, возвращаемые модели и безопасные примеры данных.
История изменений ведется в [`CHANGELOG.md`](CHANGELOG.md).

Домофонные примеры разделены на два пути:

- `examples/open_domofon_relay.py` - основной путь через `LINKS.open` из списка реле;
- `examples/open_domofon_relay_api.py` - диагностический прямой вызов
  `/domofon/relays/{relay_id}/open`.

Подробное описание различий есть в [`examples/README.md`](examples/README.md).

История событий доступна через `client.history.get_events(...)`. Метод использует
CRM/LK API и при необходимости получает LK token через текущий mobile token.
Для частого сценария последних открытий и звонков есть
`client.history.get_recent_activity(...)`. Для добора нескольких страниц до нужного
количества событий есть `client.history.get_events_until_limit(...)`.

Camera API доступен через `client.cameras`:

- `get_self_cams_with_group()`;
- `get_groups(self_cams=False)`;
- `get_group(group_id)`;
- `get_limited_info_by_uuid(uuid)`;
- `get_limited_info_by_uuids(uuids)`.

У каждой `Camera` есть свойство `streams`, которое собирает HLS, MSE, snapshot и
WebSocket URL в одну модель `CameraStreams`.
Подписанные stream/snapshot URL считаются временными credential-like значениями: не
сохраняйте их в публичных логах, документации и fixtures.

По умолчанию клиент использует домен `is74.ru`. Если совместимый API расположен на
другом домене, передайте `base_domain` в `IS74Async` или `IS74`; high-level методы и
`ClientRequestOptions(base_url=BaseUrl.*)` будут строить URL от этого домена.

Диагностические примеры `examples/inspect_cameras.py` и
`examples/inspect_user_device.py` по умолчанию печатают безопасную сводку без адресов,
UUID, MAC-адресов и подписанных URL. Сырой JSON включается только явным
`IS74_RAW_JSON=yes`.

## Благодарности

Спасибо авторам открытых проектов, по которым мы сверяли известные endpoint и
поведение API:

- [@hoolea](https://github.com/hoolea) и проект
  [`intersvyaz_hass`](https://github.com/hoolea/intersvyaz_hass);
- [@alexmorbo](https://github.com/alexmorbo) и проект
  [`domru`](https://github.com/alexmorbo/domru).

Эти проекты помогли быстрее проверить гипотезы по авторизации, аккаунту и домофонным
сценариям. `pyis74` остается самостоятельной библиотекой с собственным публичным API,
типизацией и тестами.

## Разработка

```bash
uv sync --all-groups
uv run ruff format
uv run ruff check
uv run mypy
uv run pytest
uv run python scripts/privacy_scan.py
uv build
```

## Статус API

До версии `1.0.0` публичный API может изменяться. Breaking changes будут отражаться
в minor-релизах серии `0.x`.

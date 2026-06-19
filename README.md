# pyis74

`pyis74` - Python-библиотека для работы с API IS74/Интерсвязь.

Проект находится на раннем этапе разработки. Цель библиотеки - предоставить современный,
типизированный и проверяемый клиент для сценариев:

- авторизация в API IS74;
- работа с домофонами;
- открытие двери;
- получение камер и ссылок на видеопотоки;
- получение данных личного кабинета;
- история событий;
- SIP и FCM в последующих версиях.

## Требования

- Python `3.14+`.
- Runtime-зависимости минимальны.
- Публичный API будет типизирован.

## Пример

```python
import asyncio

from pyis74 import IS74Async


async def main() -> None:
    async with IS74Async() as client:
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

Домофонные примеры разделены на два пути:

- `examples/open_domofon_relay.py` - основной путь через `LINKS.open` из списка реле;
- `examples/open_domofon_relay_api.py` - диагностический прямой вызов
  `/domofon/relays/{relay_id}/open`.

Подробное описание различий есть в [`examples/README.md`](examples/README.md).

История событий доступна через `client.history.get_events(...)`. Метод использует
CRM/LK API и при необходимости получает LK token через текущий mobile token.

Camera API доступен через `client.cameras`:

- `get_self_cams_with_group()`;
- `get_groups(self_cams=False)`;
- `get_group(group_id)`;
- `get_limited_info_by_uuid(uuid)`;
- `get_limited_info_by_uuids(uuids)`.

Диагностические примеры `examples/inspect_cameras.py` и
`examples/inspect_user_device.py` по умолчанию печатают безопасную сводку без адресов,
UUID, MAC-адресов и подписанных URL. Сырой JSON включается только явным
`IS74_RAW_JSON=yes`.

## Разработка

```bash
uv sync --all-groups
uv run ruff format
uv run ruff check
uv run mypy src tests
uv run pytest
```

## Статус API

До версии `1.0.0` публичный API может изменяться. Breaking changes будут отражаться
в minor-релизах серии `0.x`.

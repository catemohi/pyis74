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
phone auth, проверка адреса и проверка баланса.

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

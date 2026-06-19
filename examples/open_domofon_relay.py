"""Пример открытия домофонного реле IS74 по `RELAY_ID`."""

from __future__ import annotations

import asyncio

from _common import authorize_client, require_env

from pyis74 import IS74Async


async def main() -> None:
    """Авторизуется и открывает реле из `IS74_RELAY_ID`."""
    relay_id = read_relay_id()
    require_open_confirmation()

    async with IS74Async() as client:
        await authorize_client(client)
        result = await client.domofon.open_relay_by_id(relay_id)

    print(f"Open request status: {result.status_code}")
    if result.response_text:
        print(result.response_text)


def read_relay_id() -> int:
    """Возвращает `RELAY_ID` из переменной окружения.

    Returns:
        Идентификатор реле.

    Raises:
        RuntimeError: Значение `IS74_RELAY_ID` не является целым числом.
    """
    value = require_env("IS74_RELAY_ID")
    try:
        return int(value)
    except ValueError as error:
        msg = f"IS74_RELAY_ID must be an integer: {value!r}."
        raise RuntimeError(msg) from error


def require_open_confirmation() -> None:
    """Проверяет явное подтверждение открытия реле.

    Raises:
        RuntimeError: `IS74_CONFIRM_OPEN` не равен `yes`.
    """
    value = require_env("IS74_CONFIRM_OPEN")
    if value.lower() == "yes":
        return

    msg = "Set IS74_CONFIRM_OPEN=yes to confirm relay opening."
    raise RuntimeError(msg)


if __name__ == "__main__":
    asyncio.run(main())

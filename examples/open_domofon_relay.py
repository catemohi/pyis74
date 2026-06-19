"""Пример открытия домофонного реле IS74 по `RELAY_ID`."""

from __future__ import annotations

import asyncio

from _common import authorize_client, read_named_int_env, require_env_value

from pyis74 import IS74Async
from pyis74.models import DomofonRelay


async def main() -> None:
    """Авторизуется и открывает реле из `IS74_RELAY_ID`."""
    relay_id_env, relay_id = read_relay_id()
    require_open_confirmation()

    async with IS74Async() as client:
        await authorize_client(client)
        relays = await client.domofon.get_relays()
        relay = find_relay(relays, relay_id)
        print_relay_summary(relay, relay_id_env)
        result = await client.domofon.open_relay(relay)

    print(f"Open request status: {result.status_code}")
    if result.response_text:
        print(result.response_text)


def read_relay_id() -> tuple[str, int]:
    """Возвращает `RELAY_ID` из переменной окружения.

    Returns:
        Имя переменной окружения и идентификатор реле.

    Raises:
        RuntimeError: Значение `IS74_RELAY_ID` или `RELAY_ID` не является целым числом.
    """
    return read_named_int_env("IS74_RELAY_ID", "RELAY_ID")


def find_relay(relays: tuple[DomofonRelay, ...], relay_id: int) -> DomofonRelay:
    """Находит реле в списке доступных реле.

    Args:
        relays: Список реле текущего пользователя.
        relay_id: Искомый `RELAY_ID`.

    Returns:
        Найденное реле.

    Raises:
        RuntimeError: Реле с указанным id не найдено.
    """
    for relay in relays:
        if relay.relay_id == relay_id:
            return relay

    msg = f"RELAY_ID={relay_id} was not found in current account relays."
    raise RuntimeError(msg)


def print_relay_summary(relay: DomofonRelay, relay_id_env: str) -> None:
    """Печатает безопасную сводку фактического open-запроса.

    Args:
        relay: Реле, которое будет открываться.
        relay_id_env: Имя переменной окружения, из которой взят `RELAY_ID`.
    """
    opener_type = relay.opener.type if relay.opener is not None else "unknown"
    link_type = "crm" if relay.open_url and "td-crm.is74.ru" in relay.open_url else "api"
    print(
        "Opening "
        f"RELAY_ID={relay.relay_id} "
        f"from {relay_id_env} "
        f"with opener={opener_type}, link={link_type}."
    )


def require_open_confirmation() -> None:
    """Проверяет явное подтверждение открытия реле.

    Raises:
        RuntimeError: `IS74_CONFIRM_OPEN` не равен `yes`.
    """
    require_env_value("IS74_CONFIRM_OPEN", "yes")


if __name__ == "__main__":
    asyncio.run(main())

"""Пример вывода домофонных реле текущего аккаунта IS74."""

from __future__ import annotations

import asyncio

from _common import authorize_client
from pyis74 import IS74Async
from pyis74.models import DomofonRelay


async def main() -> None:
    """Авторизуется и печатает список доступных реле."""
    async with IS74Async() as client:
        await authorize_client(client)
        relays = await client.domofon.get_relays()

    if not relays:
        print("Реле не найдены.")
        return

    for index, relay in enumerate(relays, start=1):
        print(format_relay(index, relay))


def format_relay(index: int, relay: DomofonRelay) -> str:
    """Форматирует реле для консольного вывода.

    Args:
        index: Порядковый номер в списке.
        relay: Домофонное реле.

    Returns:
        Строка с основными параметрами реле.
    """
    relay_id = relay.relay_id if relay.relay_id is not None else "unknown"
    relay_name = relay.relay_descr or relay.relay_type or "без названия"
    opener_type = relay.opener.type if relay.opener is not None else "unknown"
    has_video = "video" if relay.has_video else "no-video"
    address = relay.address or "адрес не указан"
    return f"{index}. RELAY_ID={relay_id} [{opener_type}, {has_video}] {relay_name}: {address}"


if __name__ == "__main__":
    asyncio.run(main())

"""Диагностический пример чтения сырого домофонного реле по `RELAY_ID`."""

from __future__ import annotations

import asyncio
import json

from _common import authorize_client, read_int_env
from pyis74 import IS74Async
from pyis74.endpoints import DOMOFON_RELAY_TEMPLATE


async def main() -> None:
    """Авторизуется и печатает сырой ответ `/domofon/relays/{relay_id}`."""
    relay_id = read_int_env("IS74_RELAY_ID")

    async with IS74Async() as client:
        await authorize_client(client)
        payload = await client.request_mobile(
            "GET",
            DOMOFON_RELAY_TEMPLATE.format(relay_id=relay_id),
        )

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())

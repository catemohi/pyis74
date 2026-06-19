"""Диагностический пример чтения сырых реле домофона IS74."""

from __future__ import annotations

import asyncio
import json

from _common import authorize_client
from pyis74 import IS74Async
from pyis74.endpoints import DOMOFON_RELAYS


async def main() -> None:
    """Авторизуется и печатает сырой ответ `/domofon/relays`."""
    async with IS74Async() as client:
        await authorize_client(client)
        payload = await client.request_mobile("GET", DOMOFON_RELAYS)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())

"""Диагностический пример чтения CRM user-device IS74."""

from __future__ import annotations

import asyncio
import json

from _common import authorize_client

from pyis74 import IS74Async
from pyis74.endpoints import CRM_USER_DEVICE


async def main() -> None:
    """Авторизуется и печатает сырой ответ `td-crm.is74.ru/api/user-device`."""
    async with IS74Async() as client:
        await authorize_client(client)
        payload = await client.request_lk("GET", CRM_USER_DEVICE)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())

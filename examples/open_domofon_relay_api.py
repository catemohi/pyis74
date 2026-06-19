"""Пример прямого открытия домофонного реле через API path."""

from __future__ import annotations

import asyncio

from _common import authorize_client, read_int_env, require_env_value

from pyis74 import IS74Async


async def main() -> None:
    """Открывает `/domofon/relays/{relay_id}/open?from=app`."""
    relay_id = read_int_env("IS74_RELAY_ID")
    require_env_value("IS74_CONFIRM_OPEN", "yes")

    async with IS74Async() as client:
        await authorize_client(client)
        result = await client.domofon.open_relay_by_api_id(relay_id)

    print(f"Open request status: {result.status_code}")
    if result.response_text:
        print(result.response_text)


if __name__ == "__main__":
    asyncio.run(main())

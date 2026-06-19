"""Пример получения CRM/LK token через mobile access token."""

from __future__ import annotations

import asyncio

from _common import authorize_client, mask_secret

from pyis74 import IS74Async


async def main() -> None:
    """Авторизуется в mobile API и получает CRM/LK token."""
    async with IS74Async() as client:
        await authorize_client(client)
        token = await client.auth.get_lk_token()

    print(f"LK token: {mask_secret(token.token)}")
    print(f"Expires at: {token.expires_at}")


if __name__ == "__main__":
    asyncio.run(main())

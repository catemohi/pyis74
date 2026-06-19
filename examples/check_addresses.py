"""Пример проверки адреса текущего аккаунта IS74."""

from __future__ import annotations

import asyncio

from _common import authorize_client, print_account_address

from pyis74 import IS74Async


async def main() -> None:
    """Авторизуется и печатает адрес установки услуг."""
    async with IS74Async() as client:
        await authorize_client(client)
        address = await client.account.get_address()

    print_account_address(address)


if __name__ == "__main__":
    asyncio.run(main())

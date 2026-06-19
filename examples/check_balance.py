"""Пример проверки баланса текущего аккаунта IS74."""

from __future__ import annotations

import asyncio

from _common import authorize_client

from pyis74 import IS74Async


async def main() -> None:
    """Авторизуется и печатает баланс лицевого счета."""
    async with IS74Async() as client:
        await authorize_client(client)
        balance = await client.account.get_balance()

    print(f"Balance: {balance.balance}")
    if balance.next_payment is not None:
        print(f"Next payment: {balance.next_payment.amount}")
        print(f"Next payment text: {balance.next_payment.text}")
    print(f"Debt: {balance.debt}")
    print(f"Blocked: {balance.blocked}")
    print(f"Date delay lock: {balance.date_delay_lock}")


if __name__ == "__main__":
    asyncio.run(main())

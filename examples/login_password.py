"""Пример авторизации IS74 через логин и пароль."""

from __future__ import annotations

import asyncio

from _common import mask_secret, require_env

from pyis74 import IS74Async


async def main() -> None:
    """Выполняет password-login и печатает сведения о token."""
    login = require_env("IS74_LOGIN")
    password = require_env("IS74_PASSWORD")

    async with IS74Async() as client:
        token = await client.auth.login_with_password(login, password)

    print(f"Mobile token: {mask_secret(token.token)}")
    print(f"Expires at: {token.expires_at}")


if __name__ == "__main__":
    asyncio.run(main())

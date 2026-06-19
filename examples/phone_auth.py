"""Пример авторизации IS74 через телефон и выбора адреса."""

from __future__ import annotations

import asyncio

from _common import (
    optional_env,
    print_address_candidates,
    read_address_index,
    require_env,
)

from pyis74 import IS74Async


async def main() -> None:
    """Выполняет phone auth flow и получает token для выбранного адреса."""
    phone = require_env("IS74_PHONE")
    device_id = optional_env("IS74_DEVICE_ID")

    async with IS74Async() as client:
        started = await client.auth.request_phone_confirmation(phone, device_id=device_id)
        print(f"Device id: {started.device_id}")
        if started.auth_id is not None:
            print(f"Initial auth id: {started.auth_id}")

        code = require_confirmation_code()
        checked = await client.auth.check_phone_confirmation(
            phone,
            code,
            auth_id=started.auth_id or "",
        )

        print("Доступные адреса:")
        print_address_candidates(checked.addresses)
        if not checked.addresses:
            return

        selected_address = checked.addresses[read_address_index(checked.addresses)]
        if selected_address.user_id is None:
            msg = "Selected address does not contain USER_ID."
            raise RuntimeError(msg)

        token = await client.auth.get_token_for_user(
            auth_id=checked.auth_id,
            user_id=selected_address.user_id,
            device_id=started.device_id,
        )

    print(f"Selected USER_ID: {selected_address.user_id}")
    print(f"Mobile token: {token.token}")
    print("Для следующих примеров можно сохранить token в IS74_MOBILE_TOKEN.")


def require_confirmation_code() -> str:
    """Возвращает код подтверждения из env или stdin.

    Returns:
        Код подтверждения.

    Raises:
        RuntimeError: Код не задан.
    """
    code = optional_env("IS74_CONFIRM_CODE") or input("Код подтверждения: ").strip()
    if code:
        return code

    msg = "Confirmation code is required."
    raise RuntimeError(msg)


if __name__ == "__main__":
    asyncio.run(main())

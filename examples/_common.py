"""Общие функции для примеров pyis74."""

from __future__ import annotations

import os
from collections.abc import Sequence

from pyis74 import IS74Async
from pyis74.models import Address, AddressCandidate

MIN_ADDRESS_INDEX = 1


def require_env(name: str) -> str:
    """Возвращает обязательную переменную окружения.

    Args:
        name: Имя переменной окружения.

    Returns:
        Значение переменной окружения.

    Raises:
        RuntimeError: Переменная не задана или содержит пустую строку.
    """
    value = os.getenv(name)
    if value:
        return value

    msg = f"Set {name} environment variable."
    raise RuntimeError(msg)


def optional_env(name: str) -> str | None:
    """Возвращает непустую переменную окружения или `None`.

    Args:
        name: Имя переменной окружения.

    Returns:
        Значение переменной или `None`.
    """
    value = os.getenv(name)
    if value:
        return value
    return None


def mask_secret(value: str) -> str:
    """Маскирует секрет для вывода в консоль.

    Args:
        value: Секретное значение.

    Returns:
        Маскированная строка.
    """
    visible_prefix_length = 8
    if len(value) <= visible_prefix_length:
        return "***"
    return f"{value[:visible_prefix_length]}...***"


async def authorize_client(client: IS74Async) -> None:
    """Добавляет mobile token в клиент.

    Если задан `IS74_MOBILE_TOKEN`, используется он. Иначе выполняется авторизация
    по `IS74_LOGIN` и `IS74_PASSWORD`.

    Args:
        client: Асинхронный клиент IS74.

    Raises:
        RuntimeError: Нет token и нет пары login/password.
    """
    token = optional_env("IS74_MOBILE_TOKEN")
    if token is not None:
        client.set_mobile_token(token)
        return

    login = optional_env("IS74_LOGIN")
    password = optional_env("IS74_PASSWORD")
    if login is not None and password is not None:
        await client.auth.login_with_password(login, password)
        return

    msg = "Set IS74_MOBILE_TOKEN or both IS74_LOGIN and IS74_PASSWORD."
    raise RuntimeError(msg)


def print_address_candidates(addresses: Sequence[AddressCandidate]) -> None:
    """Печатает список адресов, доступных после phone auth.

    Args:
        addresses: Адреса-кандидаты из API.
    """
    if not addresses:
        print("Адреса не найдены.")
        return

    for index, address in enumerate(addresses, start=MIN_ADDRESS_INDEX):
        user_id = address.user_id if address.user_id is not None else "unknown"
        address_text = address.address or "адрес не указан"
        print(f"{index}. USER_ID={user_id}: {address_text}")


def print_account_address(address: Address) -> None:
    """Печатает адрес установки услуг текущего аккаунта.

    Args:
        address: Адрес текущего аккаунта.
    """
    print(f"USER_ID: {address.user_id}")
    print(f"CITY_ID: {address.city_id}")
    print(f"STREET_ID: {address.street_id}")
    print(f"BUILDING_ID: {address.building_id}")
    print(f"FLAT_ID: {address.flat_id}")
    print(f"PODJEZD_ID: {address.entrance_id}")


def read_address_index(addresses: Sequence[AddressCandidate]) -> int:
    """Считывает номер адреса из `IS74_ADDRESS_INDEX` или stdin.

    Args:
        addresses: Адреса-кандидаты из API.

    Returns:
        Номер выбранного адреса в zero-based формате.

    Raises:
        RuntimeError: Индекс вне диапазона или не является числом.
    """
    raw_index = optional_env("IS74_ADDRESS_INDEX") or input("Выберите номер адреса: ").strip()
    try:
        selected_index = int(raw_index)
    except ValueError as error:
        msg = f"Address index must be an integer: {raw_index!r}."
        raise RuntimeError(msg) from error

    if selected_index < MIN_ADDRESS_INDEX or selected_index > len(addresses):
        msg = f"Address index must be between {MIN_ADDRESS_INDEX} and {len(addresses)}."
        raise RuntimeError(msg)
    return selected_index - MIN_ADDRESS_INDEX

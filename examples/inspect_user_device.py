"""Диагностический пример чтения CRM user-device IS74."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterable, Iterator

from _common import authorize_client, optional_env, read_bool_env
from pyis74 import IS74Async, IS74Error, IS74HTTPError
from pyis74.endpoints import CRM_USER_DEVICE, BaseUrl, join_url
from pyis74.types import JsonObject, JsonValue

RAW_JSON_ENV = "IS74_RAW_JSON"
USER_DEVICE_ENDPOINT_ENV = "IS74_USER_DEVICE_ENDPOINT"
USER_DEVICE_CANDIDATES: tuple[str, ...] = (
    CRM_USER_DEVICE,
    join_url(BaseUrl.CRM, "/api/user/device"),
    join_url(BaseUrl.CRM, "/api/user/devices"),
    join_url(BaseUrl.CRM, "/api/devices"),
)


async def main() -> None:
    """Авторизуется и проверяет известные кандидаты user-device endpoints."""
    raw_json = read_bool_env(RAW_JSON_ENV, default=False)

    if raw_json:
        print(
            f"WARNING: {RAW_JSON_ENV}=yes prints raw API payloads with private "
            "device identifiers and push-related fields."
        )
    else:
        print(f"Safe summary mode. Set {RAW_JSON_ENV}=yes to print raw JSON.")

    async with IS74Async() as client:
        await authorize_client(client)

        found = False
        for index, endpoint in enumerate(read_candidate_endpoints(), start=1):
            found = (
                await fetch_user_device_endpoint(
                    client,
                    endpoint,
                    index=index,
                    raw_json=raw_json,
                )
                or found
            )

    if not found:
        print("\nNo user-device endpoint returned a successful JSON response.")
        print(f"To test another path, set {USER_DEVICE_ENDPOINT_ENV}.")


async def fetch_user_device_endpoint(
    client: IS74Async,
    endpoint: str,
    *,
    index: int,
    raw_json: bool,
) -> bool:
    """Выполняет один диагностический запрос user-device.

    Args:
        client: Асинхронный клиент IS74.
        endpoint: Проверяемый endpoint.
        index: Порядковый номер кандидата.
        raw_json: Печатать сырой JSON вместо безопасной сводки.

    Returns:
        `True`, если endpoint вернул успешный JSON.
    """
    print(f"\n## GET user-device candidate #{index}: {endpoint}")
    try:
        payload = await client.request_lk("GET", endpoint)
    except IS74HTTPError as error:
        print(f"HTTP {error.context.status_code}: endpoint did not return JSON data.")
        return False
    except IS74Error as error:
        print(f"ERROR: {error}")
        return False

    print_payload(payload, raw_json=raw_json)
    return True


def read_candidate_endpoints() -> tuple[str, ...]:
    """Возвращает endpoints для проверки user-device.

    Returns:
        Явно заданный endpoint или встроенный набор кандидатов.
    """
    custom_endpoint = optional_env(USER_DEVICE_ENDPOINT_ENV)
    if custom_endpoint is not None:
        return (custom_endpoint,)
    return USER_DEVICE_CANDIDATES


def print_payload(payload: JsonValue, *, raw_json: bool) -> None:
    """Печатает JSON payload в сыром или безопасном виде.

    Args:
        payload: JSON-ответ API.
        raw_json: Печатать сырой JSON вместо безопасной сводки.
    """
    if raw_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return

    print_safe_summary(payload)


def print_safe_summary(payload: JsonValue) -> None:
    """Печатает безопасную структурную сводку JSON-ответа.

    Args:
        payload: JSON-ответ API.
    """
    print(f"JSON shape: {describe_json_shape(payload)}")
    if isinstance(payload, dict):
        print(f"Top-level keys: {format_object_keys(payload)}")
    elif isinstance(payload, list):
        objects = [item for item in payload if isinstance(item, dict)]
        if objects:
            print(f"Top-level object keys: {format_union_keys(objects)}")

    nested_objects = list(iter_json_objects(payload))
    print(f"JSON objects: {len(nested_objects)}")
    if nested_objects:
        print(f"Object keys observed: {format_union_keys(nested_objects)}")


def describe_json_shape(payload: JsonValue) -> str:
    """Возвращает краткое описание формы JSON-значения.

    Args:
        payload: JSON-значение.

    Returns:
        Строковое описание формы.
    """
    if isinstance(payload, list):
        return f"list[{len(payload)}]"
    if isinstance(payload, dict):
        return f"object[{len(payload)} keys]"
    return type(payload).__name__


def format_object_keys(payload: JsonObject) -> str:
    """Форматирует ключи JSON-объекта без печати значений.

    Args:
        payload: JSON-объект.

    Returns:
        Строка с именами ключей.
    """
    if not payload:
        return "<empty>"
    if all(key.isdigit() for key in payload):
        return "<numeric object ids redacted>"
    return ", ".join(sorted(payload))


def format_union_keys(objects: Iterable[JsonObject]) -> str:
    """Форматирует объединение ключей набора JSON-объектов.

    Args:
        objects: JSON-объекты.

    Returns:
        Строка с именами ключей.
    """
    keys: set[str] = set()
    for item in objects:
        keys.update(item)
    if not keys:
        return "<empty>"
    return ", ".join(sorted(keys))


def iter_json_objects(payload: JsonValue) -> Iterator[JsonObject]:
    """Итерирует все JSON-объекты внутри значения.

    Args:
        payload: JSON-значение.

    Yields:
        Найденные JSON-объекты.
    """
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            if isinstance(value, list | dict):
                yield from iter_json_objects(value)
        return

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, list | dict):
                yield from iter_json_objects(item)


if __name__ == "__main__":
    asyncio.run(main())

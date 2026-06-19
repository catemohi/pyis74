"""Диагностический пример чтения camera API IS74."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Iterable
from urllib.parse import urlencode

from _common import authorize_client, optional_env

from pyis74 import IS74Async, IS74Error
from pyis74.endpoints import (
    CAMS_GET_GROUP,
    CAMS_LIMITED_INFO_BY_UUID,
    CAMS_SELF_WITH_GROUP,
    DOMOFON_RELAYS,
)
from pyis74.options import ClientRequestOptions
from pyis74.types import JsonObject, JsonValue

FORM_HEADERS: dict[str, str] = {"Content-Type": "application/x-www-form-urlencoded"}
DEFAULT_GROUP_LIMIT = 10


async def main() -> None:
    """Авторизуется и печатает сырые ответы camera endpoints."""
    group_limit = read_optional_int_env("IS74_CAMERA_GROUP_LIMIT") or DEFAULT_GROUP_LIMIT

    async with IS74Async() as client:
        await authorize_client(client)

        self_cams = await fetch_section(
            "GET cams.is74.ru/api/self-cams-with-group",
            client.request_mobile("GET", CAMS_SELF_WITH_GROUP),
        )
        groups = await fetch_section(
            "GET cams.is74.ru/api/get-group/",
            client.request_mobile("GET", CAMS_GET_GROUP),
        )
        self_groups = await fetch_section(
            "GET cams.is74.ru/api/get-group/?selfCams=true",
            client.request_mobile(
                "GET",
                CAMS_GET_GROUP,
                ClientRequestOptions(params={"selfCams": True}),
            ),
        )

        for group_id in choose_group_ids(
            explicit_group_id=optional_env("IS74_CAMERA_GROUP_ID"),
            payloads=(groups, self_groups, self_cams),
            limit=group_limit,
        ):
            await fetch_section(
                f"GET cams.is74.ru/api/get-group/{group_id}",
                client.request_mobile(
                    "GET",
                    build_group_url(group_id),
                ),
            )

        relays = await fetch_section(
            "GET api.is74.ru/domofon/relays for ENTRANCE_UID discovery",
            client.request_mobile("GET", DOMOFON_RELAYS),
        )
        for camera_uuid in choose_camera_uuids(relays):
            await fetch_section(
                f"POST cams.is74.ru/api/limited-info-by-uuid for UUID {camera_uuid}",
                request_limited_info_by_uuid(
                    client,
                    camera_uuid,
                ),
            )


async def fetch_section(
    title: str,
    request: Awaitable[JsonValue],
) -> JsonValue | None:
    """Выполняет диагностический запрос и печатает результат.

    Args:
        title: Заголовок секции.
        request: Awaitable, выполняющий HTTP-запрос.

    Returns:
        JSON-ответ или `None`, если endpoint вернул ошибку pyis74.
    """
    print(f"\n## {title}")
    try:
        payload = await request
    except IS74Error as error:
        print(f"ERROR: {error}")
        return None

    print_json(payload)
    return payload


async def request_limited_info_by_uuid(client: IS74Async, camera_uuid: str) -> JsonValue:
    """Получает информацию о камере по UUID подъезда или камеры.

    Args:
        client: Асинхронный клиент IS74.
        camera_uuid: UUID для `CAMERA_UUIDS[]`.

    Returns:
        JSON-ответ camera API.
    """
    return await client.request_mobile(
        "POST",
        CAMS_LIMITED_INFO_BY_UUID,
        ClientRequestOptions(
            headers=FORM_HEADERS,
            content=urlencode({"CAMERA_UUIDS[]": camera_uuid}),
        ),
    )


def choose_group_ids(
    *,
    explicit_group_id: str | None,
    payloads: Iterable[JsonValue | None],
    limit: int,
) -> tuple[str, ...]:
    """Выбирает group id для детального inspect.

    Args:
        explicit_group_id: Явно заданный `IS74_CAMERA_GROUP_ID`.
        payloads: Ответы endpoints, где могут быть группы.
        limit: Максимальное количество групп для авто-inspect.

    Returns:
        Кортеж group id.
    """
    if explicit_group_id:
        return (explicit_group_id,)

    group_ids: list[str] = []
    for payload in payloads:
        collect_group_ids(payload, group_ids)

    unique_group_ids = tuple(dict.fromkeys(group_ids))
    return unique_group_ids[:limit]


def collect_group_ids(payload: JsonValue | None, group_ids: list[str]) -> None:
    """Собирает group id из JSON-ответа camera API.

    Args:
        payload: JSON-ответ endpoint.
        group_ids: Изменяемый список найденных group id.
    """
    if isinstance(payload, list):
        for item in payload:
            collect_group_ids(item, group_ids)
        return

    if not isinstance(payload, dict):
        return

    append_json_id(payload, "ID", group_ids)
    append_json_id(payload, "id", group_ids)

    for value in payload.values():
        if isinstance(value, list | dict):
            collect_group_ids(value, group_ids)


def append_json_id(payload: JsonObject, key: str, result: list[str]) -> None:
    """Добавляет JSON id в список, если поле есть.

    Args:
        payload: JSON-объект.
        key: Имя поля id.
        result: Изменяемый список id.
    """
    value = payload.get(key)
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | str):
        result.append(str(value))


def choose_camera_uuids(relays_payload: JsonValue | None) -> tuple[str, ...]:
    """Возвращает UUID для проверки `/limited-info-by-uuid`.

    Args:
        relays_payload: Ответ `/domofon/relays`.

    Returns:
        UUID из `IS74_CAMERA_UUIDS` и `ENTRANCE_UID` домофонных реле.
    """
    camera_uuids = list(read_camera_uuid_env())
    collect_entrance_uids(relays_payload, camera_uuids)
    return tuple(dict.fromkeys(camera_uuids))


def read_camera_uuid_env() -> tuple[str, ...]:
    """Возвращает UUID из `IS74_CAMERA_UUIDS`.

    Returns:
        Кортеж UUID из comma-separated переменной окружения.
    """
    raw_value = optional_env("IS74_CAMERA_UUIDS")
    if raw_value is None:
        return ()

    return tuple(part.strip() for part in raw_value.split(",") if part.strip())


def collect_entrance_uids(payload: JsonValue | None, result: list[str]) -> None:
    """Собирает `ENTRANCE_UID` из ответа `/domofon/relays`.

    Args:
        payload: JSON-ответ `/domofon/relays`.
        result: Изменяемый список UUID.
    """
    if not isinstance(payload, list):
        return

    for item in payload:
        if not isinstance(item, dict):
            continue
        entrance_uid = item.get("ENTRANCE_UID")
        if isinstance(entrance_uid, str) and entrance_uid:
            result.append(entrance_uid)


def build_group_url(group_id: str) -> str:
    """Собирает URL детального просмотра группы камер.

    Args:
        group_id: ID группы.

    Returns:
        Абсолютный URL `cams.is74.ru/api/get-group/{group_id}`.
    """
    return f"{CAMS_GET_GROUP.rstrip('/')}/{group_id}"


def read_optional_int_env(name: str) -> int | None:
    """Возвращает опциональное целое число из переменной окружения.

    Args:
        name: Имя переменной окружения.

    Returns:
        Целое число или `None`.

    Raises:
        RuntimeError: Значение переменной не является целым числом.
    """
    value = optional_env(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as error:
        msg = f"{name} must be an integer: {value!r}."
        raise RuntimeError(msg) from error


def print_json(payload: JsonValue) -> None:
    """Печатает JSON-значение.

    Args:
        payload: JSON-значение.
    """
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())

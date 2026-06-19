"""Диагностический пример чтения camera API IS74."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Iterable, Iterator
from urllib.parse import urlencode

from _common import authorize_client, optional_env, read_bool_env
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
DEFAULT_GROUP_LIMIT = 5
RAW_JSON_ENV = "IS74_RAW_JSON"


async def main() -> None:
    """Авторизуется и печатает безопасную сводку camera endpoints."""
    group_limit = read_optional_int_env("IS74_CAMERA_GROUP_LIMIT") or DEFAULT_GROUP_LIMIT
    raw_json = read_bool_env(RAW_JSON_ENV, default=False)

    if raw_json:
        print(
            f"WARNING: {RAW_JSON_ENV}=yes prints raw API payloads with private "
            "addresses, identifiers and signed media URLs."
        )
    else:
        print(f"Safe summary mode. Set {RAW_JSON_ENV}=yes to print raw JSON.")

    async with IS74Async() as client:
        await authorize_client(client)

        self_cams = await fetch_section(
            "GET cams.is74.ru/api/self-cams-with-group",
            client.request_mobile("GET", CAMS_SELF_WITH_GROUP),
            raw_json=raw_json,
        )
        groups = await fetch_section(
            "GET cams.is74.ru/api/get-group/",
            client.request_mobile("GET", CAMS_GET_GROUP),
            raw_json=raw_json,
        )
        self_groups = await fetch_section(
            "GET cams.is74.ru/api/get-group/?selfCams=true",
            client.request_mobile(
                "GET",
                CAMS_GET_GROUP,
                ClientRequestOptions(params={"selfCams": True}),
            ),
            raw_json=raw_json,
        )

        for index, group_id in enumerate(
            choose_group_ids(
                explicit_group_id=optional_env("IS74_CAMERA_GROUP_ID"),
                payloads=(groups, self_groups, self_cams),
                limit=group_limit,
            ),
            start=1,
        ):
            await fetch_section(
                raw_or_safe_title(
                    raw_json=raw_json,
                    raw_title=f"GET cams.is74.ru/api/get-group/{group_id}",
                    safe_title=f"GET cams.is74.ru/api/get-group/<selected-group #{index}>",
                ),
                client.request_mobile("GET", build_group_url(group_id)),
                raw_json=raw_json,
            )

        relays = await fetch_section(
            "GET api.is74.ru/domofon/relays for ENTRANCE_UID discovery",
            client.request_mobile("GET", DOMOFON_RELAYS),
            raw_json=raw_json,
        )
        for index, camera_uuid in enumerate(choose_camera_uuids(relays), start=1):
            await fetch_section(
                raw_or_safe_title(
                    raw_json=raw_json,
                    raw_title=(
                        f"POST cams.is74.ru/api/limited-info-by-uuid for UUID {camera_uuid}"
                    ),
                    safe_title=(
                        f"POST cams.is74.ru/api/limited-info-by-uuid for selected UUID #{index}"
                    ),
                ),
                request_limited_info_by_uuid(client, camera_uuid),
                raw_json=raw_json,
            )


async def fetch_section(
    title: str,
    request: Awaitable[JsonValue],
    *,
    raw_json: bool,
) -> JsonValue | None:
    """Выполняет диагностический запрос и печатает результат.

    Args:
        title: Заголовок секции.
        request: Awaitable, выполняющий HTTP-запрос.
        raw_json: Печатать сырой JSON вместо безопасной сводки.

    Returns:
        JSON-ответ или `None`, если endpoint вернул ошибку pyis74.
    """
    print(f"\n## {title}")
    try:
        payload = await request
    except IS74Error as error:
        print(f"ERROR: {error}")
        return None

    print_payload(payload, raw_json=raw_json)
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


def raw_or_safe_title(*, raw_json: bool, raw_title: str, safe_title: str) -> str:
    """Возвращает заголовок секции с учетом режима вывода.

    Args:
        raw_json: Включен ли сырой вывод.
        raw_title: Полный диагностический заголовок.
        safe_title: Обезличенный заголовок.

    Returns:
        Заголовок для печати.
    """
    if raw_json:
        return raw_title
    return safe_title


def print_payload(payload: JsonValue, *, raw_json: bool) -> None:
    """Печатает JSON payload в сыром или безопасном виде.

    Args:
        payload: JSON-ответ API.
        raw_json: Печатать сырой JSON вместо безопасной сводки.
    """
    if raw_json:
        print_json(payload)
        return

    print_safe_summary(payload)


def print_safe_summary(payload: JsonValue) -> None:
    """Печатает безопасную структурную сводку JSON-ответа.

    Args:
        payload: JSON-ответ API.
    """
    print(f"JSON shape: {describe_json_shape(payload)}")
    print_top_level_keys(payload)

    groups = collect_group_objects(payload)
    self_camera_groups = collect_self_camera_groups(payload)
    cameras = collect_camera_objects(payload)
    relays = collect_relay_objects(payload)

    if groups:
        print(f"Groups: {len(groups)}")
        print(f"Group object keys: {format_union_keys(groups)}")
    if self_camera_groups:
        print(f"Self camera groups: {len(self_camera_groups)}")
    if cameras:
        print_camera_summary(cameras)
    if relays:
        print_relay_summary(relays)


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


def print_top_level_keys(payload: JsonValue) -> None:
    """Печатает безопасные имена верхнеуровневых ключей.

    Args:
        payload: JSON-ответ API.
    """
    if isinstance(payload, dict):
        print(f"Top-level keys: {format_object_keys(payload)}")
        return

    if not isinstance(payload, list):
        return

    objects = [item for item in payload if isinstance(item, dict)]
    if objects:
        print(f"Top-level object keys: {format_union_keys(objects)}")


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


def collect_camera_objects(payload: JsonValue) -> list[JsonObject]:
    """Собирает объекты камер из JSON-ответа.

    Args:
        payload: JSON-ответ API.

    Returns:
        Список объектов с `OBJECT=CAMERA`.
    """
    return [item for item in iter_json_objects(payload) if item.get("OBJECT") == "CAMERA"]


def collect_group_objects(payload: JsonValue) -> list[JsonObject]:
    """Собирает объекты групп из JSON-ответа.

    Args:
        payload: JSON-ответ API.

    Returns:
        Список объектов с `OBJECT=GROUP`.
    """
    return [item for item in iter_json_objects(payload) if item.get("OBJECT") == "GROUP"]


def collect_relay_objects(payload: JsonValue) -> list[JsonObject]:
    """Собирает объекты домофонных реле из JSON-ответа.

    Args:
        payload: JSON-ответ API.

    Returns:
        Список объектов реле.
    """
    return [
        item for item in iter_json_objects(payload) if "RELAY_ID" in item and "MAC_ADDR" in item
    ]


def collect_self_camera_groups(payload: JsonValue) -> list[JsonObject]:
    """Собирает группы из `/self-cams-with-group`.

    Args:
        payload: JSON-ответ API.

    Returns:
        Список объектов групп с массивом `cameras`.
    """
    return [
        item
        for item in iter_json_objects(payload)
        if isinstance(item.get("cameras"), list) and "groupName" in item
    ]


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


def print_camera_summary(cameras: list[JsonObject]) -> None:
    """Печатает обезличенную сводку по камерам.

    Args:
        cameras: Объекты камер.
    """
    print(f"Cameras: {len(cameras)}")
    print(f"Camera object keys: {format_union_keys(cameras)}")
    print(
        "Camera access: "
        f"live={count_nested_bool(cameras, ('ACCESS', 'LIVE', 'STATUS'))}, "
        f"archive={count_nested_bool(cameras, ('ACCESS', 'ARCHIVE', 'STATUS'))}, "
        f"movement={count_nested_bool(cameras, ('ACCESS', 'MOVEMENT', 'STATUS'))}, "
        f"download={count_nested_bool(cameras, ('ACCESS', 'DOWNLOAD', 'STATUS'))}, "
        f"ptz={count_nested_bool(cameras, ('ACCESS', 'PTZ', 'STATUS'))}"
    )
    print(
        "Camera media fields: "
        f"hls_live_main={count_json_path(cameras, ('MEDIA', 'HLS', 'LIVE', 'MAIN'))}, "
        f"hls_live_low_latency="
        f"{count_json_path(cameras, ('MEDIA', 'HLS', 'LIVE', 'LOW_LATENCY'))}, "
        f"hls_archive={count_json_path(cameras, ('MEDIA', 'HLS', 'ARCHIVE'))}, "
        f"mse_live={count_json_path(cameras, ('MEDIA', 'MSE', 'LIVE'))}, "
        f"snapshot_main={count_json_path(cameras, ('MEDIA', 'SNAPSHOT', 'LIVE', 'MAIN'))}"
    )
    print(
        "Camera supported features: "
        f"doorbell={count_nested_bool(cameras, ('SUPPORTED_FEATURES', 'doorbell'))}, "
        f"ptz={count_nested_bool(cameras, ('SUPPORTED_FEATURES', 'ptz'))}, "
        f"voice={count_nested_bool(cameras, ('SUPPORTED_FEATURES', 'voice'))}, "
        f"zoom={count_nested_bool(cameras, ('SUPPORTED_FEATURES', 'zoom'))}, "
        f"motion_setup="
        f"{count_nested_bool(cameras, ('SUPPORTED_FEATURES', 'setup_motion_detect'))}"
    )


def print_relay_summary(relays: list[JsonObject]) -> None:
    """Печатает обезличенную сводку по реле.

    Args:
        relays: Объекты реле.
    """
    print(f"Relays: {len(relays)}")
    print(f"Relay object keys: {format_union_keys(relays)}")
    print(
        "Relay flags: "
        f"with_entrance_uid={count_non_empty_string(relays, 'ENTRANCE_UID')}, "
        f"has_video={count_string_flag(relays, 'HAS_VIDEO')}, "
        f"smart_intercom={count_string_flag(relays, 'SMART_INTERCOM')}, "
        f"with_qr_options={count_non_null(relays, 'QR_OPTIONS')}"
    )
    print(f"Relay opener types: {format_counts(count_opener_types(relays))}")


def count_json_path(items: Iterable[JsonObject], path: tuple[str, ...]) -> int:
    """Считает объекты, где есть JSON-путь.

    Args:
        items: JSON-объекты.
        path: Путь ключей.

    Returns:
        Количество объектов с таким путем.
    """
    return sum(1 for item in items if has_json_path(item, path))


def count_nested_bool(items: Iterable[JsonObject], path: tuple[str, ...]) -> int:
    """Считает объекты, где вложенное boolean-поле равно `True`.

    Args:
        items: JSON-объекты.
        path: Путь ключей.

    Returns:
        Количество объектов с `True` в указанном поле.
    """
    return sum(1 for item in items if read_nested_bool(item, path) is True)


def count_non_empty_string(items: Iterable[JsonObject], key: str) -> int:
    """Считает объекты с непустой строкой в поле.

    Args:
        items: JSON-объекты.
        key: Имя поля.

    Returns:
        Количество объектов с непустой строкой.
    """
    count = 0
    for item in items:
        value = item.get(key)
        if isinstance(value, str) and value:
            count += 1
    return count


def count_non_null(items: Iterable[JsonObject], key: str) -> int:
    """Считает объекты, где поле не равно `null`.

    Args:
        items: JSON-объекты.
        key: Имя поля.

    Returns:
        Количество объектов с ненулевым значением.
    """
    return sum(1 for item in items if item.get(key) is not None)


def count_string_flag(items: Iterable[JsonObject], key: str) -> int:
    """Считает строковые флаги API со значением `1`.

    Args:
        items: JSON-объекты.
        key: Имя поля.

    Returns:
        Количество объектов со строковым флагом `1`.
    """
    return sum(1 for item in items if item.get(key) == "1")


def count_opener_types(relays: Iterable[JsonObject]) -> dict[str, int]:
    """Считает типы opener у домофонных реле.

    Args:
        relays: Объекты реле.

    Returns:
        Счетчик типов opener.
    """
    result: dict[str, int] = {}
    for relay in relays:
        opener = relay.get("OPENER")
        if not isinstance(opener, dict):
            continue
        opener_type = opener.get("type")
        if not isinstance(opener_type, str) or not opener_type:
            continue
        result[opener_type] = result.get(opener_type, 0) + 1
    return result


def format_counts(counts: dict[str, int]) -> str:
    """Форматирует счетчик.

    Args:
        counts: Счетчик.

    Returns:
        Строковое представление счетчика.
    """
    if not counts:
        return "<empty>"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def has_json_path(payload: JsonObject, path: tuple[str, ...]) -> bool:
    """Проверяет наличие вложенного JSON-пути.

    Args:
        payload: JSON-объект.
        path: Путь ключей.

    Returns:
        `True`, если путь существует и конечное значение не `null`.
    """
    current: JsonValue = payload
    for key in path:
        if not isinstance(current, dict):
            return False
        if key not in current:
            return False
        current = current[key]
    return current is not None


def read_nested_bool(payload: JsonObject, path: tuple[str, ...]) -> bool | None:
    """Читает вложенное boolean-поле.

    Args:
        payload: JSON-объект.
        path: Путь ключей.

    Returns:
        Boolean-значение или `None`.
    """
    current: JsonValue = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if isinstance(current, bool):
        return current
    return None


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
    """Собирает group id только из объектов групп camera API.

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

    if payload.get("OBJECT") == "GROUP":
        append_json_id(payload, "ID", group_ids)
        return

    if isinstance(payload.get("cameras"), list):
        append_json_id(payload, "id", group_ids)


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

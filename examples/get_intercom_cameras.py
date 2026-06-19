"""Пример получения камер домофонных реле через `ENTRANCE_UID`."""

from __future__ import annotations

import asyncio

from _common import authorize_client, read_bool_env
from pyis74 import IS74Async
from pyis74.models import Camera, DomofonRelayCameras

SHOW_PRIVATE_FIELDS_ENV = "IS74_SHOW_PRIVATE_CAMERA_FIELDS"


async def main() -> None:
    """Авторизуется и печатает безопасную сводку домофонных камер."""
    show_private_fields = read_bool_env(SHOW_PRIVATE_FIELDS_ENV, default=False)

    async with IS74Async() as client:
        await authorize_client(client)
        relay_cameras = await client.domofon.get_relay_cameras()

    print(f"Relays: {len(relay_cameras)}")
    print(f"Relays with cameras: {count_relays_with_cameras(relay_cameras)}")
    print(f"Intercom cameras: {count_cameras(relay_cameras)}")
    for index, relay_cameras_item in enumerate(relay_cameras, start=1):
        print(
            format_relay_cameras(index, relay_cameras_item, show_private_fields=show_private_fields)
        )
        for camera_index, camera in enumerate(relay_cameras_item.cameras, start=1):
            print(
                "  " + format_camera(camera_index, camera, show_private_fields=show_private_fields)
            )


def count_relays_with_cameras(relay_cameras: tuple[DomofonRelayCameras, ...]) -> int:
    """Считает реле, для которых найдена хотя бы одна камера.

    Args:
        relay_cameras: Связки реле и камер.

    Returns:
        Количество реле с камерами.
    """
    return sum(1 for item in relay_cameras if item.cameras)


def count_cameras(relay_cameras: tuple[DomofonRelayCameras, ...]) -> int:
    """Считает общее количество найденных камер.

    Args:
        relay_cameras: Связки реле и камер.

    Returns:
        Количество камер.
    """
    return sum(len(item.cameras) for item in relay_cameras)


def format_relay_cameras(
    index: int,
    relay_cameras: DomofonRelayCameras,
    *,
    show_private_fields: bool,
) -> str:
    """Форматирует реле и количество найденных камер.

    Args:
        index: Порядковый номер реле.
        relay_cameras: Связка реле и камер.
        show_private_fields: Печатать приватные поля вроде id, названия и адреса.

    Returns:
        Строка реле.
    """
    relay = relay_cameras.relay
    fields = [
        f"Relay #{index}",
        f"cameras={len(relay_cameras.cameras)}",
        f"has_video={format_bool(value=relay.has_video)}",
        f"smart_intercom={format_bool(value=relay.smart_intercom)}",
    ]
    if show_private_fields:
        fields.extend(
            (
                f"relay_id={relay.relay_id if relay.relay_id is not None else 'unknown'}",
                f"type={relay.relay_type or 'тип не указан'}",
                f"description={relay.relay_descr or 'описание не указано'}",
                f"address={relay.address or 'адрес не указан'}",
            )
        )
    return ", ".join(fields)


def format_camera(
    index: int,
    camera: Camera,
    *,
    show_private_fields: bool,
) -> str:
    """Форматирует домофонную камеру без stream URL и token.

    Args:
        index: Порядковый номер камеры.
        camera: Камера.
        show_private_fields: Печатать приватные поля вроде id, UUID, названия и адреса.

    Returns:
        Строка камеры.
    """
    live = "unknown"
    archive = "unknown"
    if camera.access is not None and camera.access.live is not None:
        live = "yes" if camera.access.live.status else "no"
    if camera.access is not None and camera.access.archive is not None:
        archive = "yes" if camera.access.archive.status else "no"

    fields = [
        f"Camera #{index}",
        f"live={live}",
        f"archive={archive}",
        f"streams={'yes' if camera.streams.has_any else 'no'}",
    ]
    if show_private_fields:
        fields.extend(
            (
                f"id={camera.camera_id if camera.camera_id is not None else 'unknown'}",
                f"uuid={camera.uuid or 'unknown'}",
                f"name={camera.name or 'без названия'}",
                f"address={camera.address or 'адрес не указан'}",
            )
        )
    return ", ".join(fields)


def format_bool(*, value: bool | None) -> str:
    """Форматирует трехзначный boolean для консоли.

    Args:
        value: `True`, `False` или `None`.

    Returns:
        `yes`, `no` или `unknown`.
    """
    if value is None:
        return "unknown"
    return "yes" if value else "no"


if __name__ == "__main__":
    asyncio.run(main())

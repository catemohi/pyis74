"""Пример получения камер домофонных реле через `ENTRANCE_UID`."""

from __future__ import annotations

import asyncio

from _common import authorize_client, read_bool_env

from pyis74 import IS74Async
from pyis74.models import Camera, DomofonRelay

SHOW_PRIVATE_FIELDS_ENV = "IS74_SHOW_PRIVATE_CAMERA_FIELDS"


async def main() -> None:
    """Авторизуется и печатает безопасную сводку домофонных камер."""
    show_private_fields = read_bool_env(SHOW_PRIVATE_FIELDS_ENV, default=False)

    async with IS74Async() as client:
        await authorize_client(client)
        relays = await client.domofon.get_relays()
        entrance_uids = collect_entrance_uids(relays)
        limited_info = await client.cameras.get_limited_info_by_uuids(entrance_uids)

    print(f"Relays: {len(relays)}")
    print(f"Relays with ENTRANCE_UID: {len(entrance_uids)}")
    print(f"Intercom cameras: {len(limited_info.cameras)}")
    for index, camera in enumerate(limited_info.cameras, start=1):
        print(format_camera(index, camera, show_private_fields=show_private_fields))


def collect_entrance_uids(relays: tuple[DomofonRelay, ...]) -> tuple[str, ...]:
    """Собирает непустые `ENTRANCE_UID` из домофонных реле.

    Args:
        relays: Домофонные реле.

    Returns:
        Кортеж уникальных UUID подъездов.
    """
    entrance_uids = [relay.entrance_uid for relay in relays if relay.entrance_uid is not None]
    return tuple(dict.fromkeys(entrance_uids))


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
        f"hls={'yes' if camera.media is not None and camera.media.hls is not None else 'no'}",
        f"mse={'yes' if camera.media is not None and camera.media.mse is not None else 'no'}",
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


if __name__ == "__main__":
    asyncio.run(main())

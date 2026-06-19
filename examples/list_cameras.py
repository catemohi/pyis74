"""Пример безопасного вывода камер текущего аккаунта IS74."""

from __future__ import annotations

import asyncio
from typing import Literal

from _common import authorize_client, read_bool_env

from pyis74 import IS74Async
from pyis74.models import Camera, SelfCameraGroup

SHOW_PRIVATE_FIELDS_ENV = "IS74_SHOW_PRIVATE_CAMERA_FIELDS"


async def main() -> None:
    """Авторизуется и печатает безопасную сводку камер."""
    show_private_fields = read_bool_env(SHOW_PRIVATE_FIELDS_ENV, default=False)

    async with IS74Async() as client:
        await authorize_client(client)
        groups = await client.cameras.get_self_cams_with_group()

    if not groups:
        print("Камеры не найдены.")
        return

    for group_index, group in enumerate(groups, start=1):
        print(format_group(group_index, group, show_private_fields=show_private_fields))
        for camera_index, camera in enumerate(group.cameras, start=1):
            print(
                f"  {format_camera(camera_index, camera, show_private_fields=show_private_fields)}"
            )


def format_group(
    index: int,
    group: SelfCameraGroup,
    *,
    show_private_fields: bool,
) -> str:
    """Форматирует группу камер.

    Args:
        index: Порядковый номер группы.
        group: Группа камер пользователя.
        show_private_fields: Печатать приватные поля вроде id и названия.

    Returns:
        Строка группы.
    """
    owns = "yes" if group.is_management_company_owns else "no"
    if show_private_fields:
        group_id = group.group_id or "unknown"
        group_name = group.group_name or "без названия"
        return (
            f"Group #{index}: id={group_id}, name={group_name}, "
            f"cameras={len(group.cameras)}, owns={owns}"
        )
    return f"Group #{index}: cameras={len(group.cameras)}, owns={owns}"


def format_camera(
    index: int,
    camera: Camera,
    *,
    show_private_fields: bool,
) -> str:
    """Форматирует камеру без stream URL и token.

    Args:
        index: Порядковый номер камеры в группе.
        camera: Камера.
        show_private_fields: Печатать приватные поля вроде id, UUID, названия и адреса.

    Returns:
        Строка камеры.
    """
    live = has_access(camera, "live")
    archive = has_access(camera, "archive")
    movement = has_access(camera, "movement")
    hls = "yes" if camera.media is not None and camera.media.hls is not None else "no"
    mse = "yes" if camera.media is not None and camera.media.mse is not None else "no"
    snapshot = "yes" if camera.media is not None and camera.media.snapshot is not None else "no"
    fields = [
        f"Camera #{index}",
        f"live={live}",
        f"archive={archive}",
        f"movement={movement}",
        f"hls={hls}",
        f"mse={mse}",
        f"snapshot={snapshot}",
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


def has_access(
    camera: Camera,
    field_name: Literal["live", "archive", "movement"],
) -> str:
    """Возвращает человекочитаемый статус доступа.

    Args:
        camera: Камера.
        field_name: Имя поля `CameraAccess`.

    Returns:
        `yes`, `no` или `unknown`.
    """
    if camera.access is None:
        return "unknown"

    if field_name == "live":
        access_status = camera.access.live
    elif field_name == "archive":
        access_status = camera.access.archive
    else:
        access_status = camera.access.movement
    if access_status is None or access_status.status is None:
        return "unknown"
    return "yes" if access_status.status else "no"


if __name__ == "__main__":
    asyncio.run(main())

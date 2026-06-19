"""Пример вывода подписанных stream URL камер IS74."""

from __future__ import annotations

import asyncio

from _common import authorize_client, optional_env, read_bool_env, require_env_value

from pyis74 import IS74Async
from pyis74.models import Camera

CONFIRM_ENV = "IS74_CONFIRM_PRINT_CAMERA_STREAMS"
SHOW_PRIVATE_FIELDS_ENV = "IS74_SHOW_PRIVATE_CAMERA_FIELDS"


async def main() -> None:
    """Авторизуется и печатает stream URL камер после явного подтверждения."""
    require_env_value(CONFIRM_ENV, "yes")
    show_private_fields = read_bool_env(SHOW_PRIVATE_FIELDS_ENV, default=False)
    camera_limit = read_optional_int_env("IS74_CAMERA_LIMIT")

    async with IS74Async() as client:
        await authorize_client(client)
        groups = await client.cameras.get_self_cams_with_group()

    cameras = [camera for group in groups for camera in group.cameras]
    if camera_limit is not None:
        cameras = cameras[:camera_limit]

    if not cameras:
        print("Камеры не найдены.")
        return

    for index, camera in enumerate(cameras, start=1):
        print_camera_streams(index, camera, show_private_fields=show_private_fields)


def print_camera_streams(
    index: int,
    camera: Camera,
    *,
    show_private_fields: bool,
) -> None:
    """Печатает stream URL одной камеры.

    Args:
        index: Порядковый номер камеры.
        camera: Камера.
        show_private_fields: Печатать приватные поля вроде id, UUID, названия и адреса.
    """
    print(format_camera_header(index, camera, show_private_fields=show_private_fields))
    for name, value in iter_stream_fields(camera):
        print(f"  {name}: {value}")


def format_camera_header(
    index: int,
    camera: Camera,
    *,
    show_private_fields: bool,
) -> str:
    """Форматирует заголовок камеры.

    Args:
        index: Порядковый номер камеры.
        camera: Камера.
        show_private_fields: Печатать приватные поля вроде id, UUID, названия и адреса.

    Returns:
        Заголовок камеры.
    """
    if not show_private_fields:
        return f"Camera #{index}"

    return (
        f"Camera #{index}: "
        f"id={camera.camera_id if camera.camera_id is not None else 'unknown'}, "
        f"uuid={camera.uuid or 'unknown'}, "
        f"name={camera.name or 'без названия'}, "
        f"address={camera.address or 'адрес не указан'}"
    )


def iter_stream_fields(camera: Camera) -> tuple[tuple[str, str], ...]:
    """Возвращает stream-поля камеры.

    Args:
        camera: Камера.

    Returns:
        Кортеж пар `имя поля`, `URL`.
    """
    fields: list[tuple[str, str]] = []
    if camera.media is not None:
        if camera.media.hls is not None:
            hls = camera.media.hls
            if hls.live is not None:
                append_stream_field(fields, "hls.live.main", hls.live.main)
                append_stream_field(fields, "hls.live.low_latency", hls.live.low_latency)
            append_stream_field(fields, "hls.archive", hls.archive)
        if camera.media.mse is not None:
            append_stream_field(fields, "mse.live", camera.media.mse.live)
        if camera.media.snapshot is not None and camera.media.snapshot.live is not None:
            snapshot = camera.media.snapshot.live
            append_stream_field(fields, "snapshot.live.main", snapshot.main)
            append_stream_field(fields, "snapshot.live.lossy", snapshot.lossy)

    if camera.realtime_ws is not None:
        append_stream_field(fields, "realtime_ws.combined", camera.realtime_ws.combined)
        append_stream_field(fields, "realtime_ws.main", camera.realtime_ws.main)
        append_stream_field(fields, "realtime_ws.sub", camera.realtime_ws.sub)

    return tuple(fields)


def append_stream_field(
    fields: list[tuple[str, str]],
    name: str,
    value: str | None,
) -> None:
    """Добавляет stream-поле, если оно не пустое.

    Args:
        fields: Изменяемый список полей.
        name: Имя stream-поля.
        value: URL или `None`.
    """
    if value:
        fields.append((name, value))


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


if __name__ == "__main__":
    asyncio.run(main())

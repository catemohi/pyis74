"""Пример вывода групп camera API IS74."""

from __future__ import annotations

import asyncio

from _common import authorize_client, read_bool_env
from pyis74 import IS74Async
from pyis74.models import CameraGroup

SHOW_PRIVATE_FIELDS_ENV = "IS74_SHOW_PRIVATE_CAMERA_FIELDS"


async def main() -> None:
    """Авторизуется и печатает группы камер."""
    show_private_fields = read_bool_env(SHOW_PRIVATE_FIELDS_ENV, default=False)

    async with IS74Async() as client:
        await authorize_client(client)
        groups = await client.cameras.get_groups()
        self_groups = await client.cameras.get_groups(self_cams=True)

    print_group_set("Groups", groups, show_private_fields=show_private_fields)
    print_group_set(
        "Groups with selfCams=true", self_groups, show_private_fields=show_private_fields
    )


def print_group_set(
    title: str,
    groups: tuple[CameraGroup, ...],
    *,
    show_private_fields: bool,
) -> None:
    """Печатает набор групп.

    Args:
        title: Заголовок набора.
        groups: Группы камер.
        show_private_fields: Печатать приватные поля вроде id и названия.
    """
    print(f"{title}: count={len(groups)}")
    for index, group in enumerate(groups, start=1):
        print(f"  {format_group(index, group, show_private_fields=show_private_fields)}")


def format_group(
    index: int,
    group: CameraGroup,
    *,
    show_private_fields: bool,
) -> str:
    """Форматирует группу камер.

    Args:
        index: Порядковый номер группы.
        group: Группа камер.
        show_private_fields: Печатать приватные поля вроде id и названия.

    Returns:
        Строка группы.
    """
    object_type = group.object_type or "unknown"
    if show_private_fields:
        group_id = group.group_id or "unknown"
        name = group.name or "без названия"
        return f"Group #{index}: id={group_id}, name={name}, object={object_type}"
    return f"Group #{index}: object={object_type}"


if __name__ == "__main__":
    asyncio.run(main())

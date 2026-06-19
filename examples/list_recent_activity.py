"""Пример вывода последних открытий и звонков из истории IS74."""

from __future__ import annotations

import asyncio

from _common import authorize_client, optional_env, read_bool_env

from pyis74 import IS74Async
from pyis74.models import HistoryEvent

DEFAULT_EVENT_KINDS: tuple[str, ...] = ("open", "call")


async def main() -> None:
    """Авторизуется и печатает последние открытия и звонки."""
    event_types = read_csv_env("IS74_HISTORY_EVENT_TYPES")
    event_kinds = read_csv_env("IS74_HISTORY_EVENT_KINDS")
    kinds = event_kinds if event_kinds else (() if event_types else DEFAULT_EVENT_KINDS)

    async with IS74Async() as client:
        await authorize_client(client)
        events = await client.history.get_recent_activity(
            from_date=optional_env("IS74_HISTORY_FROM"),
            to_date=optional_env("IS74_HISTORY_TO"),
            page=read_optional_int_env("IS74_HISTORY_PAGE"),
            per_page=read_optional_int_env("IS74_HISTORY_PER_PAGE"),
            event_types=event_types,
            kinds=kinds,
            with_images=read_optional_bool_env("IS74_HISTORY_WITH_IMAGES"),
        )

    if not events:
        print("Событий не найдено.")
        return

    for index, event in enumerate(events, start=1):
        print(format_activity_event(index, event))


def read_csv_env(name: str) -> tuple[str, ...]:
    """Возвращает CSV-значения из переменной окружения.

    Args:
        name: Имя переменной окружения.

    Returns:
        Кортеж непустых значений.
    """
    value = optional_env(name)
    if value is None:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def read_optional_bool_env(name: str) -> bool | None:
    """Возвращает опциональный boolean из переменной окружения.

    Args:
        name: Имя переменной окружения.

    Returns:
        `True`, `False` или `None`.
    """
    if optional_env(name) is None:
        return None
    return read_bool_env(name, default=False)


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


def format_activity_event(index: int, event: HistoryEvent) -> str:
    """Форматирует событие активности для консольного вывода.

    Args:
        index: Номер события в текущем выводе.
        event: Событие истории.

    Returns:
        Короткая строка события.
    """
    created = event.create_date or "unknown-date"
    event_type = event.event_type or "unknown-type"
    entrance = "unknown-entrance"
    if event.params is not None and event.params.entrance_title is not None:
        entrance = event.params.entrance_title
    image = "image" if event.image_link else "no-image"
    return f"{index}. {created} [{event.kind.value}/{event_type}] {entrance} ({image})"


if __name__ == "__main__":
    asyncio.run(main())

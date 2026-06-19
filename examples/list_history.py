"""Пример получения истории событий IS74."""

from __future__ import annotations

import asyncio

from _common import authorize_client, optional_env

from pyis74 import IS74Async
from pyis74.models import HistoryEvent


async def main() -> None:
    """Авторизуется и печатает страницу истории событий."""
    async with IS74Async() as client:
        await authorize_client(client)
        history = await client.history.get_events(
            from_date=optional_env("IS74_HISTORY_FROM"),
            to_date=optional_env("IS74_HISTORY_TO"),
            page=read_optional_int_env("IS74_HISTORY_PAGE"),
            per_page=read_optional_int_env("IS74_HISTORY_PER_PAGE"),
        )

    page = history.page if history.page is not None else "unknown"
    per_page = history.per_page if history.per_page is not None else "unknown"
    count = history.count if history.count is not None else "unknown"
    print(f"History page={page}, per_page={per_page}, count={count}")

    if not history.events:
        print("Событий не найдено.")
        return

    for index, event in enumerate(history.events, start=1):
        print(format_event(index, event))


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


def format_event(index: int, event: HistoryEvent) -> str:
    """Форматирует событие истории для консольного вывода.

    Args:
        index: Номер события в текущем выводе.
        event: Событие истории.

    Returns:
        Короткая строка события.
    """
    created = event.create_date or "unknown-date"
    event_type = event.event_type or "unknown-type"
    if event.params is None:
        return f"{index}. {created} [{event_type}]"

    entrance = event.params.entrance_title or "unknown-entrance"
    address = event.params.address or "unknown-address"
    image = "image" if event.image_link else "no-image"
    return f"{index}. {created} [{event_type}] {entrance}: {address} ({image})"


if __name__ == "__main__":
    asyncio.run(main())

"""Методы получения истории событий IS74."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import TYPE_CHECKING, Final

from pyis74 import endpoints
from pyis74.models import HistoryEvent, HistoryEventKind, HistoryResponse
from pyis74.options import ClientRequestOptions
from pyis74.types import QueryParams, normalize_json_object

if TYPE_CHECKING:
    from pyis74.client import IS74, IS74Async

DEFAULT_ACTIVITY_KINDS: Final[tuple[HistoryEventKind, ...]] = (
    HistoryEventKind.OPEN,
    HistoryEventKind.CALL,
)


class HistoryAPI:
    """Асинхронный домен истории событий IS74."""

    def __init__(self, client: IS74Async) -> None:
        """Создает домен истории.

        Args:
            client: Асинхронный клиент верхнего уровня.
        """
        self._client = client

    async def get_events(
        self,
        *,
        from_date: date | str | None = None,
        to_date: date | str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> HistoryResponse:
        """Возвращает страницу истории событий.

        История находится в CRM API `td-crm.is74.ru`, поэтому метод использует LK
        token. Если LK token еще не получен, клиент попробует получить его через
        текущий mobile token.

        Args:
            from_date: Начальная дата фильтра в формате `YYYY-MM-DD` или `date`.
            to_date: Конечная дата фильтра в формате `YYYY-MM-DD` или `date`.
            page: Номер страницы.
            per_page: Количество записей на странице.

        Returns:
            Страница истории событий и данные пагинации.
        """
        payload = await self._client.request_lk(
            "GET",
            endpoints.CRM_HISTORY,
            ClientRequestOptions(
                params=build_history_params(
                    from_date=from_date,
                    to_date=to_date,
                    page=page,
                    per_page=per_page,
                )
            ),
        )
        return HistoryResponse.from_json_object(normalize_json_object(payload))

    async def get_recent_activity(  # noqa: PLR0913
        self,
        *,
        from_date: date | str | None = None,
        to_date: date | str | None = None,
        page: int | None = None,
        per_page: int | None = None,
        event_types: Iterable[str] = (),
        kinds: Iterable[HistoryEventKind | str] = DEFAULT_ACTIVITY_KINDS,
        with_images: bool | None = None,
    ) -> tuple[HistoryEvent, ...]:
        """Возвращает отфильтрованные события открытий и звонков.

        Метод получает страницу истории через `get_events()`, затем локально фильтрует
        ее через `HistoryResponse.filter_events()`.

        Args:
            from_date: Начальная дата фильтра в формате `YYYY-MM-DD` или `date`.
            to_date: Конечная дата фильтра в формате `YYYY-MM-DD` или `date`.
            page: Номер страницы.
            per_page: Количество записей на странице.
            event_types: Точные типы событий из API.
            kinds: Нормализованные категории событий. По умолчанию `open` и `call`.
            with_images: Если задано, фильтровать по наличию snapshot-ссылки.

        Returns:
            Кортеж событий текущей страницы, подходящих под фильтры.
        """
        history = await self.get_events(
            from_date=from_date,
            to_date=to_date,
            page=page,
            per_page=per_page,
        )
        return history.filter_events(
            event_types=event_types,
            kinds=kinds,
            with_images=with_images,
        )


class SyncHistoryAPI:
    """Синхронная обертка домена истории событий IS74."""

    def __init__(self, client: IS74) -> None:
        """Создает синхронный домен истории.

        Args:
            client: Синхронный клиент верхнего уровня.
        """
        self._client = client

    def get_events(
        self,
        *,
        from_date: date | str | None = None,
        to_date: date | str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> HistoryResponse:
        """Возвращает страницу истории событий.

        Args:
            from_date: Начальная дата фильтра в формате `YYYY-MM-DD` или `date`.
            to_date: Конечная дата фильтра в формате `YYYY-MM-DD` или `date`.
            page: Номер страницы.
            per_page: Количество записей на странице.

        Returns:
            Страница истории событий и данные пагинации.
        """
        return self._client._run(
            lambda client: client.history.get_events(
                from_date=from_date,
                to_date=to_date,
                page=page,
                per_page=per_page,
            )
        )

    def get_recent_activity(  # noqa: PLR0913
        self,
        *,
        from_date: date | str | None = None,
        to_date: date | str | None = None,
        page: int | None = None,
        per_page: int | None = None,
        event_types: Iterable[str] = (),
        kinds: Iterable[HistoryEventKind | str] = DEFAULT_ACTIVITY_KINDS,
        with_images: bool | None = None,
    ) -> tuple[HistoryEvent, ...]:
        """Возвращает отфильтрованные события открытий и звонков.

        Args:
            from_date: Начальная дата фильтра в формате `YYYY-MM-DD` или `date`.
            to_date: Конечная дата фильтра в формате `YYYY-MM-DD` или `date`.
            page: Номер страницы.
            per_page: Количество записей на странице.
            event_types: Точные типы событий из API.
            kinds: Нормализованные категории событий. По умолчанию `open` и `call`.
            with_images: Если задано, фильтровать по наличию snapshot-ссылки.

        Returns:
            Кортеж событий текущей страницы, подходящих под фильтры.
        """
        kinds_tuple = tuple(kinds)
        event_types_tuple = tuple(event_types)
        return self._client._run(
            lambda client: client.history.get_recent_activity(
                from_date=from_date,
                to_date=to_date,
                page=page,
                per_page=per_page,
                event_types=event_types_tuple,
                kinds=kinds_tuple,
                with_images=with_images,
            )
        )


def build_history_params(
    *,
    from_date: date | str | None,
    to_date: date | str | None,
    page: int | None,
    per_page: int | None,
) -> QueryParams:
    """Собирает query-параметры истории в формате CRM API.

    Args:
        from_date: Начальная дата фильтра.
        to_date: Конечная дата фильтра.
        page: Номер страницы.
        per_page: Количество записей на странице.

    Returns:
        Query-параметры `from`, `to`, `page` и `perPage`.
    """
    return {
        "from": format_history_date(from_date),
        "to": format_history_date(to_date),
        "page": page,
        "perPage": per_page,
    }


def format_history_date(value: date | str | None) -> str | None:
    """Форматирует дату для query-параметров истории.

    Args:
        value: `date`, строка в формате API или `None`.

    Returns:
        Строка даты или `None`.
    """
    if isinstance(value, date):
        return value.isoformat()
    return value

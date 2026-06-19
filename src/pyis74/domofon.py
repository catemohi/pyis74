"""Методы работы с домофонами IS74."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pyis74 import endpoints
from pyis74.exceptions import IS74APIError
from pyis74.models import DomofonOpenResult, DomofonRelay
from pyis74.options import ClientRequestOptions
from pyis74.types import JsonValue, normalize_json_object, normalize_json_value

if TYPE_CHECKING:
    from pyis74.client import IS74, IS74Async


class DomofonAPI:
    """Асинхронный домен домофонов IS74."""

    def __init__(self, client: IS74Async) -> None:
        """Создает домен домофонов.

        Args:
            client: Асинхронный клиент верхнего уровня.
        """
        self._client = client

    async def get_relays(self) -> tuple[DomofonRelay, ...]:
        """Возвращает домофонные реле текущего пользователя.

        Returns:
            Кортеж доступных реле.

        Raises:
            IS74APIError: API вернул не список реле или список содержит не объект.
        """
        payload = await self._client.request_mobile("GET", endpoints.DOMOFON_RELAYS)
        if not isinstance(payload, list):
            msg = "IS74 domofon relays response is not a list."
            raise IS74APIError(msg, payload)

        relays: list[DomofonRelay] = []
        for item in payload:
            try:
                relay_payload = normalize_json_object(item)
            except TypeError as error:
                msg = "IS74 domofon relays response contains non-object item."
                raise IS74APIError(msg, payload) from error
            relays.append(DomofonRelay.from_json_object(relay_payload))
        return tuple(relays)

    async def get_relay(self, relay_id: int) -> DomofonRelay:
        """Возвращает домофонное реле по `RELAY_ID`.

        Args:
            relay_id: Идентификатор реле.

        Returns:
            Домофонное реле.

        Raises:
            IS74APIError: API вернул не JSON-объект.
        """
        payload = await self._client.request_mobile(
            "GET",
            endpoints.DOMOFON_RELAY_TEMPLATE.format(relay_id=relay_id),
        )
        try:
            relay_payload = normalize_json_object(payload)
        except TypeError as error:
            msg = "IS74 domofon relay response is not an object."
            raise IS74APIError(msg, payload) from error
        return DomofonRelay.from_json_object(relay_payload)

    async def open_relay(
        self,
        relay: DomofonRelay,
        *,
        from_app: bool = True,
    ) -> DomofonOpenResult:
        """Открывает домофонное реле.

        Метод использует `LINKS.open`, потому что разные реле могут открываться через
        разные сервисы: `api.is74.ru` или `td-crm.is74.ru`.

        Args:
            relay: Реле из `get_relays()`.
            from_app: Добавлять query-параметр `from=app` для `api.is74.ru`.

        Returns:
            Результат успешного HTTP-запроса открытия.

        Raises:
            IS74APIError: У реле нет ссылки открытия и нет `RELAY_ID`.
        """
        target = relay.open_url or build_domofon_open_url(relay)
        options = ClientRequestOptions(
            params={"from": "app"} if should_add_from_app(target, from_app=from_app) else None
        )
        response = await self._client._request_mobile_response("POST", target, options)
        return build_open_result(response.status_code, response.text, response.content)

    async def open_relay_by_id(
        self,
        relay_id: int,
        *,
        from_app: bool = True,
    ) -> DomofonOpenResult:
        """Открывает домофонное реле по `RELAY_ID`.

        Метод сначала загружает список реле и открывает найденный объект через его
        `LINKS.open`. Это нужно для CRM-реле, где URL нельзя корректно восстановить
        только по `RELAY_ID`.

        Args:
            relay_id: Идентификатор реле.
            from_app: Добавлять query-параметр `from=app` для `api.is74.ru`.

        Returns:
            Результат успешного HTTP-запроса открытия.

        Raises:
            IS74APIError: Реле с указанным id не найдено.
        """
        for relay in await self.get_relays():
            if relay.relay_id == relay_id:
                return await self.open_relay(relay, from_app=from_app)

        msg = f"IS74 domofon relay {relay_id} was not found."
        raise IS74APIError(msg, {"relay_id": relay_id})

    async def open_relay_by_api_id(
        self,
        relay_id: int,
        *,
        from_app: bool = True,
    ) -> DomofonOpenResult:
        """Открывает реле прямым API-запросом по `RELAY_ID`.

        В отличие от `open_relay_by_id()`, метод не использует `LINKS.open` из списка
        реле и всегда обращается к `/domofon/relays/{relay_id}/open`.

        Args:
            relay_id: Идентификатор реле.
            from_app: Добавлять query-параметр `from=app`.

        Returns:
            Результат успешного HTTP-запроса открытия.
        """
        target = endpoints.DOMOFON_RELAY_OPEN_TEMPLATE.format(relay_id=relay_id)
        options = ClientRequestOptions(params={"from": "app"} if from_app else None)
        response = await self._client._request_mobile_response("POST", target, options)
        return build_open_result(response.status_code, response.text, response.content)


class SyncDomofonAPI:
    """Синхронная обертка домена домофонов IS74."""

    def __init__(self, client: IS74) -> None:
        """Создает синхронный домен домофонов.

        Args:
            client: Синхронный клиент верхнего уровня.
        """
        self._client = client

    def get_relays(self) -> tuple[DomofonRelay, ...]:
        """Возвращает домофонные реле текущего пользователя.

        Returns:
            Кортеж доступных реле.
        """
        return self._client._run(lambda client: client.domofon.get_relays())

    def get_relay(self, relay_id: int) -> DomofonRelay:
        """Возвращает домофонное реле по `RELAY_ID`.

        Args:
            relay_id: Идентификатор реле.

        Returns:
            Домофонное реле.
        """
        return self._client._run(lambda client: client.domofon.get_relay(relay_id))

    def open_relay(
        self,
        relay: DomofonRelay,
        *,
        from_app: bool = True,
    ) -> DomofonOpenResult:
        """Открывает домофонное реле.

        Args:
            relay: Реле из `get_relays()`.
            from_app: Добавлять query-параметр `from=app` для `api.is74.ru`.

        Returns:
            Результат успешного HTTP-запроса открытия.
        """
        return self._client._run(lambda client: client.domofon.open_relay(relay, from_app=from_app))

    def open_relay_by_id(
        self,
        relay_id: int,
        *,
        from_app: bool = True,
    ) -> DomofonOpenResult:
        """Открывает домофонное реле по `RELAY_ID`.

        Args:
            relay_id: Идентификатор реле.
            from_app: Добавлять query-параметр `from=app` для `api.is74.ru`.

        Returns:
            Результат успешного HTTP-запроса открытия.
        """
        return self._client._run(
            lambda client: client.domofon.open_relay_by_id(relay_id, from_app=from_app)
        )

    def open_relay_by_api_id(
        self,
        relay_id: int,
        *,
        from_app: bool = True,
    ) -> DomofonOpenResult:
        """Открывает реле прямым API-запросом по `RELAY_ID`.

        Args:
            relay_id: Идентификатор реле.
            from_app: Добавлять query-параметр `from=app`.

        Returns:
            Результат успешного HTTP-запроса открытия.
        """
        return self._client._run(
            lambda client: client.domofon.open_relay_by_api_id(relay_id, from_app=from_app)
        )


def build_domofon_open_url(relay: DomofonRelay) -> str:
    """Возвращает fallback URL открытия реле.

    Args:
        relay: Домофонное реле.

    Returns:
        URL открытия через `api.is74.ru`.

    Raises:
        IS74APIError: У реле нет `RELAY_ID`.
    """
    if relay.relay_id is None:
        msg = "IS74 domofon relay does not contain open URL or RELAY_ID."
        raise IS74APIError(msg, relay.raw)
    return endpoints.DOMOFON_RELAY_OPEN_TEMPLATE.format(relay_id=relay.relay_id)


def should_add_from_app(target: str, *, from_app: bool) -> bool:
    """Проверяет, нужно ли добавить query-параметр `from=app`.

    Args:
        target: URL открытия реле.
        from_app: Пользовательское разрешение добавлять параметр.

    Returns:
        `True`, если параметр нужно добавить.
    """
    return from_app and target.startswith(str(endpoints.BaseUrl.API))


def build_open_result(status_code: int, response_text: str, content: bytes) -> DomofonOpenResult:
    """Создает результат открытия из HTTP-ответа.

    Args:
        status_code: HTTP-код ответа.
        response_text: Текст ответа.
        content: Бинарное тело ответа.

    Returns:
        Результат открытия реле.
    """
    payload: JsonValue | None = None
    if content:
        try:
            parsed: object = json.loads(response_text)
        except ValueError:
            payload = None
        else:
            payload = normalize_json_value(parsed)
    return DomofonOpenResult(status_code=status_code, payload=payload, response_text=response_text)

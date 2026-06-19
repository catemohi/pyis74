"""Методы работы с домофонами IS74."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import TYPE_CHECKING

from pyis74.endpoints import IS74ServiceUrls
from pyis74.exceptions import IS74APIError
from pyis74.models import Camera, DomofonOpenResult, DomofonRelay, DomofonRelayCameras
from pyis74.options import ClientRequestOptions
from pyis74.types import JsonValue, normalize_json_object, normalize_json_value

if TYPE_CHECKING:
    from pyis74.client import IS74, IS74Async

JSON_HEADERS: dict[str, str] = {"Content-Type": "application/json"}
NO_RETRY_MAX_RETRIES = 0


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
        payload = await self._client.request_mobile("GET", self._client.urls.domofon_relays)
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
            self._client.urls.domofon_relay_template.format(relay_id=relay_id),
        )
        try:
            relay_payload = normalize_json_object(payload)
        except TypeError as error:
            msg = "IS74 domofon relay response is not an object."
            raise IS74APIError(msg, payload) from error
        return DomofonRelay.from_json_object(relay_payload)

    async def get_relay_cameras(self) -> tuple[DomofonRelayCameras, ...]:
        """Возвращает домофонные реле вместе с найденными камерами.

        Метод сначала получает список реле через `get_relays()`, затем для каждого
        уникального `ENTRANCE_UID` делает limited-info запрос camera API. Batch-ответ
        camera API не содержит исходный UUID запроса, поэтому для сохранения связи
        `relay -> cameras` используются отдельные запросы по уникальным UID.

        Returns:
            Кортеж связок реле и камер. Реле без `ENTRANCE_UID` тоже попадают в ответ,
            но с пустым списком камер.
        """
        return await self.get_cameras_for_relays(await self.get_relays())

    async def get_cameras_for_relays(
        self,
        relays: Iterable[DomofonRelay],
    ) -> tuple[DomofonRelayCameras, ...]:
        """Возвращает камеры для уже загруженных домофонных реле.

        Args:
            relays: Реле из `get_relays()` или другого источника.

        Returns:
            Кортеж связок реле и камер.
        """
        relays_tuple = tuple(relays)
        cameras_by_entrance_uid: dict[str, tuple[Camera, ...]] = {}
        for entrance_uid in collect_unique_entrance_uids(relays_tuple):
            limited_info = await self._client.cameras.get_limited_info_by_uuid(entrance_uid)
            cameras_by_entrance_uid[entrance_uid] = limited_info.cameras

        return tuple(
            DomofonRelayCameras(
                relay=relay,
                cameras=cameras_by_entrance_uid.get(relay.entrance_uid or "", ()),
            )
            for relay in relays_tuple
        )

    async def open_relay(
        self,
        relay: DomofonRelay,
        *,
        from_app: bool = True,
    ) -> DomofonOpenResult:
        """Открывает домофонное реле.

        Метод открывает уже загруженный объект `DomofonRelay` и использует его
        `LINKS.open`, если ссылка есть в ответе API. Это основной путь для открытия,
        потому что разные реле могут обслуживаться разными backend-сервисами.

        Если `LINKS.open` указывает на mobile API текущего домена, клиент выполняет
        mobile `POST` на URL открытия. Для таких запросов добавляется `Content-Type:
        application/json`; query-параметр `from=app` добавляется только когда
        `from_app=True`.

        Если `LINKS.open` указывает на CRM API текущего домена, клиент получает LK
        token через `AuthAPI.get_lk_token()` и выполняет CRM `GET` с этим token. В
        этом режиме `from_app` не используется.

        Если `LINKS.open` отсутствует, метод строит fallback URL
        `/domofon/relays/{relay_id}/open` по `RELAY_ID` и использует mobile `POST`.

        Args:
            relay: Реле из `get_relays()`.
            from_app: Добавлять query-параметр `from=app` для mobile API-open.

        Returns:
            Результат успешного HTTP-запроса открытия.

        Raises:
            IS74APIError: У реле нет ссылки открытия и нет `RELAY_ID`.
        """
        target = relay.open_url or build_domofon_open_url(relay, self._client.urls)
        if is_crm_open_url(target, self._client.urls):
            response = await self._client._request_lk_response(
                "GET",
                target,
                ClientRequestOptions(max_retries=NO_RETRY_MAX_RETRIES),
            )
            return build_open_result(response.status_code, response.text, response.content)

        options = ClientRequestOptions(
            headers=JSON_HEADERS,
            params={"from": "app"}
            if should_add_from_app(target, from_app=from_app, urls=self._client.urls)
            else None,
            max_retries=NO_RETRY_MAX_RETRIES,
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
        `LINKS.open`. Это основной высокоуровневый метод для пользовательского кода:
        он сохраняет различие между реле, которые открываются через mobile API, и
        реле, которые открываются через CRM/LK API.

        Для CRM-реле URL нельзя надежно восстановить только по `RELAY_ID`, потому что
        ссылка открытия содержит параметры контроллера из `LINKS.open`. Поэтому метод
        всегда делает предварительный `GET /domofon/relays`, находит объект реле и
        затем делегирует открытие в `open_relay()`.

        Args:
            relay_id: Идентификатор реле.
            from_app: Добавлять query-параметр `from=app` для mobile API-open.

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

        Это диагностический или fallback-метод. Он полезен, когда нужно проверить
        canonical mobile API endpoint отдельно от CRM/LK-ссылок. Для CRM-реле этот
        метод может быть недостаточным, потому что он игнорирует `LINKS.open`.

        Запрос выполняется как mobile `POST` с `Content-Type: application/json`.
        При `from_app=True` добавляется query-параметр `from=app`; при
        `from_app=False` endpoint вызывается без query-параметров.

        Args:
            relay_id: Идентификатор реле.
            from_app: Добавлять query-параметр `from=app`.

        Returns:
            Результат успешного HTTP-запроса открытия.
        """
        target = self._client.urls.domofon_relay_open_template.format(relay_id=relay_id)
        options = ClientRequestOptions(
            headers=JSON_HEADERS,
            params={"from": "app"} if from_app else None,
            max_retries=NO_RETRY_MAX_RETRIES,
        )
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

    def get_relay_cameras(self) -> tuple[DomofonRelayCameras, ...]:
        """Возвращает домофонные реле вместе с найденными камерами.

        Returns:
            Кортеж связок реле и камер.
        """
        return self._client._run(lambda client: client.domofon.get_relay_cameras())

    def get_cameras_for_relays(
        self,
        relays: Iterable[DomofonRelay],
    ) -> tuple[DomofonRelayCameras, ...]:
        """Возвращает камеры для уже загруженных домофонных реле.

        Args:
            relays: Реле из `get_relays()` или другого источника.

        Returns:
            Кортеж связок реле и камер.
        """
        relays_tuple = tuple(relays)
        return self._client._run(lambda client: client.domofon.get_cameras_for_relays(relays_tuple))

    def open_relay(
        self,
        relay: DomofonRelay,
        *,
        from_app: bool = True,
    ) -> DomofonOpenResult:
        """Открывает домофонное реле.

        Синхронный аналог `DomofonAPI.open_relay()`. Использует `LINKS.open` из
        переданного объекта реле и автоматически выбирает mobile API-open или
        CRM/LK-open.

        Args:
            relay: Реле из `get_relays()`.
            from_app: Добавлять query-параметр `from=app` для mobile API-open.

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

        Синхронный аналог `DomofonAPI.open_relay_by_id()`. Сначала загружает список
        реле, затем открывает найденный объект через его `LINKS.open`.

        Args:
            relay_id: Идентификатор реле.
            from_app: Добавлять query-параметр `from=app` для mobile API-open.

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

        Синхронный аналог `DomofonAPI.open_relay_by_api_id()`. Всегда вызывает
        `/domofon/relays/{relay_id}/open` через mobile API и не использует
        `LINKS.open`.

        Args:
            relay_id: Идентификатор реле.
            from_app: Добавлять query-параметр `from=app`.

        Returns:
            Результат успешного HTTP-запроса открытия.
        """
        return self._client._run(
            lambda client: client.domofon.open_relay_by_api_id(relay_id, from_app=from_app)
        )


def build_domofon_open_url(relay: DomofonRelay, urls: IS74ServiceUrls | None = None) -> str:
    """Возвращает fallback URL открытия реле.

    Args:
        relay: Домофонное реле.
        urls: URL-конфигурация клиента.

    Returns:
        URL открытия через mobile API.

    Raises:
        IS74APIError: У реле нет `RELAY_ID`.
    """
    if relay.relay_id is None:
        msg = "IS74 domofon relay does not contain open URL or RELAY_ID."
        raise IS74APIError(msg, relay.raw)
    service_urls = urls or IS74ServiceUrls()
    return service_urls.domofon_relay_open_template.format(relay_id=relay.relay_id)


def collect_unique_entrance_uids(relays: Iterable[DomofonRelay]) -> tuple[str, ...]:
    """Собирает уникальные непустые `ENTRANCE_UID` из реле.

    Args:
        relays: Домофонные реле.

    Returns:
        Кортеж UID в порядке первого появления.
    """
    entrance_uids = [relay.entrance_uid for relay in relays if relay.entrance_uid]
    return tuple(dict.fromkeys(entrance_uids))


def should_add_from_app(
    target: str,
    *,
    from_app: bool,
    urls: IS74ServiceUrls | None = None,
) -> bool:
    """Проверяет, нужно ли добавить query-параметр `from=app`.

    Args:
        target: URL открытия реле.
        from_app: Пользовательское разрешение добавлять параметр.
        urls: URL-конфигурация клиента.

    Returns:
        `True`, если параметр нужно добавить.
    """
    service_urls = urls or IS74ServiceUrls()
    return from_app and service_urls.is_api_url(target)


def is_crm_open_url(target: str, urls: IS74ServiceUrls | None = None) -> bool:
    """Проверяет, что ссылка открытия относится к CRM API.

    Args:
        target: URL открытия реле.
        urls: URL-конфигурация клиента.

    Returns:
        `True`, если ссылка начинается с CRM base URL.
    """
    service_urls = urls or IS74ServiceUrls()
    return service_urls.is_crm_url(target)


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

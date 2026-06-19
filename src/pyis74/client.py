"""Публичные клиенты библиотеки pyis74."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from dataclasses import dataclass
from types import TracebackType

from pyis74.endpoints import BaseUrl, join_url
from pyis74.exceptions import IS74Error
from pyis74.transport import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    IS74Transport,
    RequestOptions,
)
from pyis74.types import JsonValue, QueryParams


@dataclass(frozen=True, slots=True, kw_only=True)
class ClientRequestOptions:
    """Параметры запроса публичного клиента.

    Args:
        base_url: Базовый URL для относительного endpoint.
        auth_token: Bearer-токен авторизации.
        headers: Дополнительные HTTP-заголовки.
        params: Query-параметры.
        json_body: JSON-тело запроса.
        form: Form-urlencoded данные запроса.
        content: Текстовое или бинарное тело запроса.
    """

    base_url: BaseUrl | str = BaseUrl.API
    auth_token: str | None = None
    headers: dict[str, str] | None = None
    params: QueryParams | None = None
    json_body: JsonValue | None = None
    form: dict[str, str] | None = None
    content: str | bytes | None = None


class IS74Async:
    """Асинхронный клиент верхнего уровня для API IS74."""

    def __init__(
        self,
        *,
        transport: IS74Transport | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        """Создает асинхронный клиент.

        Args:
            transport: Готовый transport. Если передан, клиент не создает свой transport.
            timeout: Таймаут запросов в секундах для собственного transport.
            max_retries: Количество повторных попыток после первого запроса.
            backoff_factor: Базовая задержка между повторными попытками.
        """
        self._owns_transport = transport is None
        self._transport = transport or IS74Transport(
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )

    async def __aenter__(self) -> IS74Async:
        """Возвращает асинхронный клиент для context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Закрывает ресурсы клиента при выходе из context manager."""
        await self.aclose()

    async def aclose(self) -> None:
        """Закрывает transport, если он был создан самим клиентом."""
        if self._owns_transport:
            await self._transport.aclose()

    async def request(
        self,
        method: str,
        target: str,
        options: ClientRequestOptions | None = None,
    ) -> JsonValue:
        """Выполняет низкоуровневый JSON-запрос к API IS74.

        Args:
            method: HTTP-метод.
            target: Относительный endpoint или абсолютный URL.
            options: Параметры клиентского запроса.

        Returns:
            Нормализованный JSON-ответ.
        """
        request_options = options or ClientRequestOptions()
        url = join_url(request_options.base_url, target)
        headers = dict(request_options.headers or {})
        if request_options.auth_token is not None:
            headers["Authorization"] = f"Bearer {request_options.auth_token}"

        transport_options = RequestOptions(
            headers=headers,
            params=request_options.params,
            json_body=request_options.json_body,
            form=request_options.form,
            content=request_options.content,
        )
        return await self._transport.request_json(method, url, transport_options)


@dataclass(frozen=True, slots=True, kw_only=True)
class IS74:
    """Синхронная обертка над `IS74Async` для простых сценариев."""

    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR

    def request(
        self,
        method: str,
        target: str,
        options: ClientRequestOptions | None = None,
    ) -> JsonValue:
        """Выполняет синхронный низкоуровневый JSON-запрос к API IS74.

        Args:
            method: HTTP-метод.
            target: Относительный endpoint или абсолютный URL.
            options: Параметры клиентского запроса.

        Returns:
            Нормализованный JSON-ответ.

        Raises:
            IS74Error: Метод вызван из уже запущенного event loop.
        """
        coroutine = self._request_async(method, target, options)
        return _run_sync(coroutine)

    async def _request_async(
        self,
        method: str,
        target: str,
        options: ClientRequestOptions | None,
    ) -> JsonValue:
        async with IS74Async(
            timeout=self.timeout,
            max_retries=self.max_retries,
            backoff_factor=self.backoff_factor,
        ) as client:
            return await client.request(method, target, options)


def _run_sync[ResultT](coroutine: Coroutine[object, object, ResultT]) -> ResultT:
    """Запускает coroutine в синхронном контексте.

    Args:
        coroutine: Coroutine, которую нужно выполнить.

    Returns:
        Результат coroutine.

    Raises:
        IS74Error: В текущем потоке уже работает event loop.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    coroutine.close()
    msg = "Synchronous IS74 client cannot be used inside a running event loop; use IS74Async."
    raise IS74Error(msg)

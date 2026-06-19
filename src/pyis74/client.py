"""Публичные клиенты библиотеки pyis74."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass, field, replace
from types import TracebackType

from pyis74.account import AccountAPI, SyncAccountAPI
from pyis74.auth import AuthAPI, SyncAuthAPI
from pyis74.endpoints import join_url
from pyis74.exceptions import IS74AuthRequiredError, IS74Error
from pyis74.options import ClientRequestOptions
from pyis74.transport import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    IS74Transport,
    RequestOptions,
)
from pyis74.types import JsonValue


class IS74Async:
    """Асинхронный клиент верхнего уровня для API IS74."""

    def __init__(
        self,
        *,
        transport: IS74Transport | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        mobile_token: str | None = None,
    ) -> None:
        """Создает асинхронный клиент.

        Args:
            transport: Готовый transport. Если передан, клиент не создает свой transport.
            timeout: Таймаут запросов в секундах для собственного transport.
            max_retries: Количество повторных попыток после первого запроса.
            backoff_factor: Базовая задержка между повторными попытками.
            mobile_token: Существующий mobile access token для запросов аккаунта.
        """
        self._owns_transport = transport is None
        self._transport = transport or IS74Transport(
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )
        self._mobile_token = mobile_token
        self.auth: AuthAPI = AuthAPI(self)
        self.account: AccountAPI = AccountAPI(self)

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

    @property
    def mobile_token(self) -> str | None:
        """Возвращает текущий mobile access token."""
        return self._mobile_token

    def set_mobile_token(self, token: str) -> None:
        """Сохраняет mobile access token в клиенте.

        Args:
            token: Bearer-токен мобильного API.
        """
        self._mobile_token = token

    def clear_mobile_token(self) -> None:
        """Удаляет mobile access token из клиента."""
        self._mobile_token = None

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

    async def request_mobile(
        self,
        method: str,
        target: str,
        options: ClientRequestOptions | None = None,
    ) -> JsonValue:
        """Выполняет JSON-запрос с mobile access token.

        Args:
            method: HTTP-метод.
            target: Относительный endpoint или абсолютный URL.
            options: Параметры клиентского запроса.

        Returns:
            Нормализованный JSON-ответ.

        Raises:
            IS74AuthRequiredError: В клиенте нет mobile access token.
        """
        request_options = options or ClientRequestOptions()
        token = request_options.auth_token or self._mobile_token
        if token is None:
            msg = "Mobile access token is required for this IS74 request."
            raise IS74AuthRequiredError(msg)
        return await self.request(method, target, replace(request_options, auth_token=token))


@dataclass(slots=True, kw_only=True)
class IS74:
    """Синхронная обертка над `IS74Async` для простых сценариев."""

    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    mobile_token: str | None = None
    auth: SyncAuthAPI = field(init=False)
    account: SyncAccountAPI = field(init=False)

    def __post_init__(self) -> None:
        """Инициализирует синхронные домены API."""
        self.auth = SyncAuthAPI(self)
        self.account = SyncAccountAPI(self)

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
        return self._run(lambda client: client.request(method, target, options))

    def request_mobile(
        self,
        method: str,
        target: str,
        options: ClientRequestOptions | None = None,
    ) -> JsonValue:
        """Выполняет синхронный JSON-запрос с mobile access token.

        Args:
            method: HTTP-метод.
            target: Относительный endpoint или абсолютный URL.
            options: Параметры клиентского запроса.

        Returns:
            Нормализованный JSON-ответ.

        Raises:
            IS74Error: Метод вызван из уже запущенного event loop.
            IS74AuthRequiredError: В клиенте нет mobile access token.
        """
        return self._run(lambda client: client.request_mobile(method, target, options))

    def set_mobile_token(self, token: str) -> None:
        """Сохраняет mobile access token в клиенте.

        Args:
            token: Bearer-токен мобильного API.
        """
        self.mobile_token = token

    def clear_mobile_token(self) -> None:
        """Удаляет mobile access token из клиента."""
        self.mobile_token = None

    def _run[ResultT](self, action: Callable[[IS74Async], Awaitable[ResultT]]) -> ResultT:
        """Запускает действие в одноразовом асинхронном клиенте."""
        return _run_sync(self._run_async(action))

    async def _run_async[ResultT](
        self,
        action: Callable[[IS74Async], Awaitable[ResultT]],
    ) -> ResultT:
        """Выполняет действие и синхронизирует mobile token обратно."""
        async with IS74Async(
            timeout=self.timeout,
            max_retries=self.max_retries,
            backoff_factor=self.backoff_factor,
            mobile_token=self.mobile_token,
        ) as client:
            try:
                return await action(client)
            finally:
                self.mobile_token = client.mobile_token


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

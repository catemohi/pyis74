"""HTTP transport для API IS74."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from types import TracebackType
from typing import Final

import httpx

from pyis74.exceptions import (
    HTTPErrorContext,
    IS74AuthError,
    IS74HTTPError,
    IS74RateLimitError,
    IS74TransportError,
)
from pyis74.types import JsonValue, QueryParams, clean_query_params, normalize_json_value

LOGGER = logging.getLogger("pyis74.transport")

DEFAULT_TIMEOUT: Final = 15.0
DEFAULT_MAX_RETRIES: Final = 2
DEFAULT_BACKOFF_FACTOR: Final = 0.25
HTTP_ERROR_STATUS: Final = 400
HTTP_AUTH_STATUSES: Final[frozenset[int]] = frozenset({401, 403})
HTTP_RATE_LIMIT_STATUS: Final = 429
RETRY_STATUSES: Final[frozenset[int]] = frozenset({408, 425, 429, 500, 502, 503, 504})
SENSITIVE_HEADERS: Final[frozenset[str]] = frozenset(
    {
        "authorization",
        "cookie",
        "proxy-authorization",
        "set-cookie",
        "x-api-key",
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RequestOptions:
    """Параметры HTTP-запроса transport-слоя.

    Args:
        headers: HTTP-заголовки запроса.
        params: Query-параметры запроса.
        json_body: JSON-тело запроса.
        form: Form-urlencoded данные запроса.
        content: Текстовое или бинарное тело запроса.
    """

    headers: dict[str, str] | None = None
    params: QueryParams | None = None
    json_body: JsonValue | None = None
    form: dict[str, str] | None = None
    content: str | bytes | None = None


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    """Маскирует чувствительные HTTP-заголовки для безопасного логирования.

    Args:
        headers: Заголовки запроса.

    Returns:
        Новый словарь заголовков с замаскированными секретами.
    """
    return {
        key: "***" if key.lower() in SENSITIVE_HEADERS else value for key, value in headers.items()
    }


class IS74Transport:
    """Асинхронный HTTP transport с retry и нормализацией ошибок."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        """Создает transport.

        Args:
            client: Внешний `httpx.AsyncClient`. Если передан, transport не закрывает его сам.
            timeout: Таймаут запросов в секундах для собственного клиента.
            max_retries: Количество повторных попыток после первого запроса.
            backoff_factor: Базовая задержка между повторными попытками.
        """
        if max_retries < 0:
            msg = "max_retries must be greater than or equal to zero."
            raise ValueError(msg)
        if backoff_factor < 0:
            msg = "backoff_factor must be greater than or equal to zero."
            raise ValueError(msg)

        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor

    async def __aenter__(self) -> IS74Transport:
        """Возвращает transport для использования в async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Закрывает собственный HTTP-клиент при выходе из context manager."""
        await self.aclose()

    async def aclose(self) -> None:
        """Закрывает собственный HTTP-клиент transport-слоя."""
        if self._owns_client and not self._client.is_closed:
            await self._client.aclose()

    async def request(
        self, method: str, url: str, options: RequestOptions | None = None
    ) -> httpx.Response:
        """Выполняет HTTP-запрос и возвращает сырой HTTP-ответ.

        Args:
            method: HTTP-метод.
            url: Абсолютный URL запроса.
            options: Параметры запроса.

        Returns:
            HTTP-ответ `httpx.Response`.

        Raises:
            IS74HTTPError: Сервер вернул неуспешный HTTP-код.
            IS74TransportError: Запрос не дошел до валидного HTTP-ответа.
        """
        request_options = options or RequestOptions()
        response: httpx.Response | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = await self._request_once(method, url, request_options)
            except (httpx.TimeoutException, httpx.TransportError) as error:
                if attempt >= self._max_retries:
                    msg = f"Transport error for {method.upper()} {url}."
                    raise IS74TransportError(msg) from error
                await self._sleep_before_retry(attempt)
                continue

            if response.status_code < HTTP_ERROR_STATUS:
                return response

            if not self._should_retry_response(response) or attempt >= self._max_retries:
                raise self._build_http_error(method, url, response)

            await self._sleep_before_retry(attempt, response)

        msg = f"Transport retry loop exhausted for {method.upper()} {url}."
        raise IS74TransportError(msg)

    async def request_json(
        self,
        method: str,
        url: str,
        options: RequestOptions | None = None,
    ) -> JsonValue:
        """Выполняет HTTP-запрос и возвращает нормализованный JSON.

        Args:
            method: HTTP-метод.
            url: Абсолютный URL запроса.
            options: Параметры запроса.

        Returns:
            Нормализованное JSON-значение.

        Raises:
            IS74TransportError: Ответ не содержит корректный JSON.
        """
        response = await self.request(method, url, options)
        try:
            payload: object = response.json()
        except ValueError as error:
            msg = f"Invalid JSON response for {method.upper()} {url}."
            raise IS74TransportError(msg) from error
        return normalize_json_value(payload)

    async def _request_once(
        self,
        method: str,
        url: str,
        options: RequestOptions,
    ) -> httpx.Response:
        headers = options.headers or {}
        redacted_headers = redact_headers(headers)
        LOGGER.debug("HTTP request: %s %s headers=%s", method.upper(), url, redacted_headers)
        return await self._client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=clean_query_params(options.params),
            json=options.json_body,
            data=options.form,
            content=options.content,
        )

    async def _sleep_before_retry(
        self,
        attempt: int,
        response: httpx.Response | None = None,
    ) -> None:
        delay = self._retry_after(response) or self._backoff_factor * (2**attempt)
        if delay > 0:
            await asyncio.sleep(delay)

    @staticmethod
    def _retry_after(response: httpx.Response | None) -> float | None:
        if response is None:
            return None
        header = response.headers.get("Retry-After")
        if header is None:
            return None
        try:
            return max(float(header), 0.0)
        except ValueError:
            return None

    @staticmethod
    def _should_retry_response(response: httpx.Response) -> bool:
        return response.status_code in RETRY_STATUSES

    @staticmethod
    def _build_http_error(method: str, url: str, response: httpx.Response) -> IS74HTTPError:
        context = HTTPErrorContext(
            status_code=response.status_code,
            method=method,
            url=url,
            response_text=response.text,
        )
        if response.status_code in HTTP_AUTH_STATUSES:
            return IS74AuthError(context)
        if response.status_code == HTTP_RATE_LIMIT_STATUS:
            return IS74RateLimitError(context)
        return IS74HTTPError(context)

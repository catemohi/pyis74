"""Тесты HTTP transport-слоя."""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from pyis74.exceptions import IS74AuthError, IS74HTTPError, IS74RateLimitError, IS74TransportError
from pyis74.transport import IS74Transport, RequestOptions, redact_headers

EXPECTED_RETRY_REQUESTS = 2
HTTP_NOT_FOUND = 404


@pytest.mark.asyncio
async def test_transport_request_json_returns_normalized_payload(httpx_mock: HTTPXMock) -> None:
    """Проверяет успешный JSON-запрос через transport."""
    httpx_mock.add_response(url="https://api.is74.ru/user/user", json={"USER_ID": 42})

    async with IS74Transport(backoff_factor=0) as transport:
        payload = await transport.request_json(
            "GET",
            "https://api.is74.ru/user/user",
            RequestOptions(headers={"Authorization": "Bearer token"}),
        )

    assert payload == {"USER_ID": 42}
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer token"


@pytest.mark.asyncio
async def test_transport_retries_retryable_status(httpx_mock: HTTPXMock) -> None:
    """Проверяет повтор запроса после временной ошибки сервера."""
    httpx_mock.add_response(url="https://api.is74.ru/user/user", status_code=500)
    httpx_mock.add_response(url="https://api.is74.ru/user/user", json={"ok": True})

    async with IS74Transport(max_retries=1, backoff_factor=0) as transport:
        payload = await transport.request_json("GET", "https://api.is74.ru/user/user")

    assert payload == {"ok": True}
    assert len(httpx_mock.get_requests()) == EXPECTED_RETRY_REQUESTS


@pytest.mark.asyncio
async def test_transport_raises_http_error(httpx_mock: HTTPXMock) -> None:
    """Проверяет ошибку HTTP-уровня."""
    httpx_mock.add_response(
        url="https://api.is74.ru/user/user",
        status_code=HTTP_NOT_FOUND,
        text="not found",
    )

    async with IS74Transport(max_retries=0) as transport:
        with pytest.raises(IS74HTTPError) as exc_info:
            await transport.request_json("GET", "https://api.is74.ru/user/user")

    assert exc_info.value.context.status_code == HTTP_NOT_FOUND
    assert exc_info.value.context.response_text == "not found"


@pytest.mark.asyncio
async def test_transport_raises_auth_error(httpx_mock: HTTPXMock) -> None:
    """Проверяет отдельную ошибку авторизации."""
    httpx_mock.add_response(url="https://api.is74.ru/user/user", status_code=401)

    async with IS74Transport(max_retries=0) as transport:
        with pytest.raises(IS74AuthError):
            await transport.request_json("GET", "https://api.is74.ru/user/user")


@pytest.mark.asyncio
async def test_transport_raises_rate_limit_error(httpx_mock: HTTPXMock) -> None:
    """Проверяет отдельную ошибку rate limit."""
    httpx_mock.add_response(url="https://api.is74.ru/user/user", status_code=429)

    async with IS74Transport(max_retries=0) as transport:
        with pytest.raises(IS74RateLimitError):
            await transport.request_json("GET", "https://api.is74.ru/user/user")


@pytest.mark.asyncio
async def test_transport_wraps_network_errors(httpx_mock: HTTPXMock) -> None:
    """Проверяет нормализацию сетевых ошибок."""
    httpx_mock.add_exception(httpx.ConnectError("connection failed"))

    async with IS74Transport(max_retries=0) as transport:
        with pytest.raises(IS74TransportError):
            await transport.request_json("GET", "https://api.is74.ru/user/user")


def test_redact_headers_masks_sensitive_values() -> None:
    """Проверяет маскирование чувствительных заголовков."""
    assert redact_headers({"Authorization": "Bearer token", "Accept": "application/json"}) == {
        "Accept": "application/json",
        "Authorization": "***",
    }


@pytest.mark.asyncio
async def test_request_options_can_disable_retries(httpx_mock: HTTPXMock) -> None:
    """Проверяет отключение retry для отдельного запроса."""
    httpx_mock.add_response(url="https://api.is74.ru/domofon/relays/900001/open", status_code=500)

    async with IS74Transport(max_retries=1, backoff_factor=0) as transport:
        with pytest.raises(IS74HTTPError):
            await transport.request_json(
                "POST",
                "https://api.is74.ru/domofon/relays/900001/open",
                RequestOptions(max_retries=0),
            )

    assert len(httpx_mock.get_requests()) == 1

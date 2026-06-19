"""Тесты публичных клиентов pyis74."""

import pytest
from pytest_httpx import HTTPXMock

from pyis74 import IS74, ClientRequestOptions, IS74Async, IS74AuthRequiredError, IS74Error
from pyis74.endpoints import BaseUrl


@pytest.mark.asyncio
async def test_async_client_builds_url_and_auth_header(httpx_mock: HTTPXMock) -> None:
    """Проверяет сборку URL и Bearer-заголовка в асинхронном клиенте."""
    httpx_mock.add_response(url="https://api.is74.ru/user/user", json={"USER_ID": 42})

    async with IS74Async(backoff_factor=0) as client:
        payload = await client.request(
            "GET",
            "/user/user",
            ClientRequestOptions(auth_token="token"),
        )

    assert payload == {"USER_ID": 42}
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer token"


@pytest.mark.asyncio
async def test_async_client_uses_custom_base_url(httpx_mock: HTTPXMock) -> None:
    """Проверяет запросы к сервисам вне базового `api.is74.ru`."""
    httpx_mock.add_response(
        url="https://cams.is74.ru/api/self-cams-with-group",
        json=[],
    )

    async with IS74Async(backoff_factor=0) as client:
        payload = await client.request(
            "GET",
            "/api/self-cams-with-group",
            ClientRequestOptions(base_url=BaseUrl.CAMS),
        )

    assert payload == []


@pytest.mark.asyncio
async def test_async_client_request_mobile_uses_stored_token(httpx_mock: HTTPXMock) -> None:
    """Проверяет подстановку сохраненного mobile access token."""
    httpx_mock.add_response(url="https://api.is74.ru/user/user", json={"USER_ID": 42})

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        payload = await client.request_mobile("GET", "/user/user")

    assert payload == {"USER_ID": 42}
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer mobile-token"


@pytest.mark.asyncio
async def test_async_client_request_mobile_can_override_token(httpx_mock: HTTPXMock) -> None:
    """Проверяет явное переопределение токена для одного запроса."""
    httpx_mock.add_response(url="https://api.is74.ru/user/user", json={"USER_ID": 42})

    async with IS74Async(backoff_factor=0, mobile_token="stored-token") as client:
        payload = await client.request_mobile(
            "GET",
            "/user/user",
            ClientRequestOptions(auth_token="override-token"),
        )

    assert payload == {"USER_ID": 42}
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer override-token"


@pytest.mark.asyncio
async def test_async_client_request_mobile_requires_token() -> None:
    """Проверяет локальную ошибку при запросе mobile API без токена."""
    async with IS74Async(backoff_factor=0) as client:
        with pytest.raises(IS74AuthRequiredError):
            await client.request_mobile("GET", "/user/user")


@pytest.mark.asyncio
async def test_async_client_request_lk_uses_stored_token(httpx_mock: HTTPXMock) -> None:
    """Проверяет подстановку сохраненного CRM/LK access token."""
    httpx_mock.add_response(
        url="https://td-crm.is74.ru/api/user/history",
        json={"data": []},
    )

    async with IS74Async(backoff_factor=0) as client:
        client.set_lk_token("lk-token")
        payload = await client.request_lk("GET", "https://td-crm.is74.ru/api/user/history")

    assert payload == {"data": []}
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer lk-token"


@pytest.mark.asyncio
async def test_async_client_request_lk_can_obtain_lk_token(httpx_mock: HTTPXMock) -> None:
    """Проверяет автоматическое получение CRM/LK token по mobile token."""
    httpx_mock.add_response(
        method="POST",
        url="https://td-crm.is74.ru/api/auth-lk",
        json={"TOKEN": "lk-token"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://td-crm.is74.ru/api/user/history",
        json={"data": []},
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        payload = await client.request_lk("GET", "https://td-crm.is74.ru/api/user/history")

    assert payload == {"data": []}
    assert client.lk_token == "lk-token"
    requests = httpx_mock.get_requests()
    assert requests[1].headers["authorization"] == "Bearer lk-token"


def test_sync_client_request(httpx_mock: HTTPXMock) -> None:
    """Проверяет синхронную обертку клиента."""
    httpx_mock.add_response(url="https://api.is74.ru/user/user", json={"USER_ID": 42})

    payload = IS74(backoff_factor=0).request("GET", "/user/user")

    assert payload == {"USER_ID": 42}


@pytest.mark.asyncio
async def test_sync_client_rejects_running_event_loop() -> None:
    """Проверяет защиту от синхронного клиента внутри работающего event loop."""
    with pytest.raises(IS74Error, match="use IS74Async"):
        IS74().request("GET", "/user/user")

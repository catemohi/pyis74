"""Тесты публичных клиентов pyis74."""

import pytest
from pytest_httpx import HTTPXMock

from pyis74 import IS74, ClientRequestOptions, IS74Async, IS74Error
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

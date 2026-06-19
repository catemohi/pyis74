"""Тесты домена аккаунта IS74."""

from decimal import Decimal

import pytest
from pytest_httpx import HTTPXMock

from pyis74 import IS74, IS74Async, IS74AuthRequiredError, endpoints

USER_ID = 100
FLAT_ID = 200
BUILDING_ID = 300
SUMMARY_REQUEST_COUNT = 4


@pytest.mark.asyncio
async def test_account_requires_mobile_token() -> None:
    """Проверяет локальную ошибку при запросе аккаунта без токена."""
    async with IS74Async(backoff_factor=0) as client:
        with pytest.raises(IS74AuthRequiredError):
            await client.account.get_user()


@pytest.mark.asyncio
async def test_get_user_sends_mobile_token(httpx_mock: HTTPXMock) -> None:
    """Проверяет получение пользователя с mobile access token."""
    httpx_mock.add_response(
        method="GET",
        url=endpoints.USER_INFO,
        json={"USER_ID": USER_ID, "FULL_NAME": "Иван Иванов", "LOGIN": "ivan"},
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        user = await client.account.get_user()

    assert user.user_id == USER_ID
    assert user.full_name == "Иван Иванов"
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer mobile-token"


@pytest.mark.asyncio
async def test_get_balance_uses_versioned_accept_header(httpx_mock: HTTPXMock) -> None:
    """Проверяет получение баланса через версионированный endpoint."""
    httpx_mock.add_response(
        method="GET",
        url=endpoints.USER_BALANCE,
        json={"balance": "125.50", "nextPayment": {"pay": "700", "text": "до 25 июня"}},
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        balance = await client.account.get_balance()

    assert balance.balance == Decimal("125.50")
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer mobile-token"
    assert request.headers["accept"] == "application/json; version=v2"


@pytest.mark.asyncio
async def test_get_summary_loads_account_parts(httpx_mock: HTTPXMock) -> None:
    """Проверяет сборку сводной информации аккаунта."""
    httpx_mock.add_response(
        method="GET",
        url=endpoints.USER_STATUS,
        json={"status": "active", "title": "Активно"},
    )
    httpx_mock.add_response(
        method="GET",
        url=endpoints.USER_INFO,
        json={"USER_ID": USER_ID, "FULL_NAME": "Иван Иванов"},
    )
    httpx_mock.add_response(
        method="GET",
        url=endpoints.USER_ADDRESS,
        json={"USER_ID": USER_ID, "FLAT_ID": FLAT_ID, "BUILDING_ID": BUILDING_ID},
    )
    httpx_mock.add_response(
        method="GET",
        url=endpoints.USER_BALANCE,
        json={"balance": "125.50"},
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        summary = await client.account.get_summary()

    assert summary.service_status.status == "active"
    assert summary.user.user_id == USER_ID
    assert summary.address.flat_id == FLAT_ID
    assert summary.balance.balance == Decimal("125.50")
    assert len(httpx_mock.get_requests()) == SUMMARY_REQUEST_COUNT


def test_sync_client_reuses_token_after_login(httpx_mock: HTTPXMock) -> None:
    """Проверяет сохранение токена в синхронном клиенте после login."""
    httpx_mock.add_response(
        method="POST",
        url=endpoints.AUTH_MOBILE,
        json={"TOKEN": "mobile-token"},
    )
    httpx_mock.add_response(
        method="GET",
        url=endpoints.USER_BALANCE,
        json={"balance": "125.50"},
    )

    client = IS74(backoff_factor=0)
    token = client.auth.login_with_password("user", "secret")
    balance = client.account.get_balance()

    assert token.token == "mobile-token"
    assert client.mobile_token == "mobile-token"
    assert balance.balance == Decimal("125.50")
    requests = httpx_mock.get_requests()
    assert requests[1].headers["authorization"] == "Bearer mobile-token"

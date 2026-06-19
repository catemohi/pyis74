"""Тесты домена авторизации IS74."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from pyis74 import IS74Async, endpoints
from pyis74.auth import normalize_phone

USER_ID = 100


@pytest.mark.asyncio
async def test_login_with_password_sets_mobile_token(httpx_mock: HTTPXMock) -> None:
    """Проверяет авторизацию по логину и паролю."""
    httpx_mock.add_response(
        method="POST",
        url=endpoints.AUTH_MOBILE,
        json={"TOKEN": "mobile-token", "ACCESS_END": "2026-06-19T12:30:00Z"},
    )

    async with IS74Async(backoff_factor=0) as client:
        token = await client.auth.login_with_password("user", "secret")

    assert token.token == "mobile-token"
    assert client.mobile_token == "mobile-token"
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"username": "user", "password": "secret"}


@pytest.mark.asyncio
async def test_request_phone_confirmation_sends_device_id(httpx_mock: HTTPXMock) -> None:
    """Проверяет старт телефонной авторизации."""
    httpx_mock.add_response(
        method="POST",
        url=endpoints.AUTH_SEND_SMS,
        json={"authId": "auth-1"},
    )

    async with IS74Async(backoff_factor=0) as client:
        result = await client.auth.request_phone_confirmation(
            "+7 (912) 345-67-89",
            device_id="device-1",
        )

    assert result.auth_id == "auth-1"
    assert result.device_id == "device-1"
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"phone": "9123456789", "uniqueDeviceId": "device-1"}


@pytest.mark.asyncio
async def test_check_phone_confirmation_sends_json(httpx_mock: HTTPXMock) -> None:
    """Проверяет отправку кода подтверждения в JSON-виде."""
    httpx_mock.add_response(
        method="POST",
        url=endpoints.AUTH_CONFIRM,
        json={
            "authId": "auth-1",
            "addresses": [{"USER_ID": str(USER_ID), "ADDRESS": "Челябинск, Ленина 1"}],
        },
    )

    async with IS74Async(backoff_factor=0) as client:
        result = await client.auth.check_phone_confirmation(
            "89123456789",
            "1234",
            device_id="device-1",
        )

    assert result.auth_id == "auth-1"
    assert result.addresses[0].user_id == USER_ID
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {
        "confirmCode": "1234",
        "phone": "9123456789",
        "uniqueDeviceId": "device-1",
    }


@pytest.mark.asyncio
async def test_get_token_for_user_sets_mobile_token(httpx_mock: HTTPXMock) -> None:
    """Проверяет получение токена для выбранного адреса."""
    httpx_mock.add_response(
        method="POST",
        url=endpoints.AUTH_GET_TOKEN,
        json={"TOKEN": "selected-token"},
    )

    async with IS74Async(backoff_factor=0) as client:
        token = await client.auth.get_token_for_user(
            auth_id="auth-1",
            user_id=100,
            device_id="device-1",
        )

    assert token.token == "selected-token"
    assert client.mobile_token == "selected-token"
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {
        "authId": "auth-1",
        "userId": "100",
    }


def test_normalize_phone() -> None:
    """Проверяет нормализацию российских телефонных номеров."""
    assert normalize_phone("+7 (912) 345-67-89") == "9123456789"
    assert normalize_phone("89123456789") == "9123456789"
    assert normalize_phone("9123456789") == "9123456789"

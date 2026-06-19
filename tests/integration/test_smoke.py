"""Opt-in smoke tests against live IS74 API."""

from __future__ import annotations

import os

import pytest

from pyis74 import IS74Async


def integration_enabled() -> bool:
    """Возвращает `True`, если live integration tests явно разрешены."""
    value = os.getenv("IS74_RUN_INTEGRATION", "")
    return value.lower() in {"1", "true", "yes", "on"}


pytestmark = pytest.mark.skipif(
    not integration_enabled(),
    reason="live IS74 integration tests require IS74_RUN_INTEGRATION=yes",
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_account_domofon_camera_smoke() -> None:
    """Проверяет базовые read-only endpoints на реальном аккаунте."""
    mobile_token = os.getenv("IS74_MOBILE_TOKEN")
    login = os.getenv("IS74_LOGIN")
    password = os.getenv("IS74_PASSWORD")

    if not mobile_token and not (login and password):
        pytest.skip("set IS74_MOBILE_TOKEN or IS74_LOGIN/IS74_PASSWORD")

    async with IS74Async(mobile_token=mobile_token) as client:
        if not mobile_token:
            await client.auth.login_with_password(login or "", password or "")

        summary = await client.account.get_summary()
        relays = await client.domofon.get_relays()
        camera_groups = await client.cameras.get_groups()
        history = await client.history.get_events(per_page=1)

    assert summary.user.user_id is not None
    assert isinstance(relays, tuple)
    assert isinstance(camera_groups, tuple)
    assert isinstance(history.events, tuple)

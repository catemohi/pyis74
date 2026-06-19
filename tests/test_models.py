"""Тесты типизированных моделей API IS74."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from pyis74.exceptions import IS74APIError
from pyis74.models import Balance, MobileToken, PhoneConfirmationCheck, parse_datetime


def test_mobile_token_from_json_object() -> None:
    """Проверяет разбор mobile access token."""
    token = MobileToken.from_json_object(
        {
            "TOKEN": "mobile-token",
            "ACCESS_END": "2026-06-19T12:30:00Z",
        }
    )

    assert token.token == "mobile-token"
    assert token.expires_at == datetime(2026, 6, 19, 12, 30, tzinfo=UTC)


def test_mobile_token_requires_token_field() -> None:
    """Проверяет валидацию обязательного поля `TOKEN`."""
    with pytest.raises(IS74APIError, match="TOKEN"):
        MobileToken.from_json_object({"ACCESS_END": "2026-06-19T12:30:00Z"})


def test_phone_confirmation_check_parses_addresses() -> None:
    """Проверяет разбор списка адресов после подтверждения телефона."""
    result = PhoneConfirmationCheck.from_json_object(
        {
            "authId": "auth-1",
            "addresses": [
                {"USER_ID": "100", "ADDRESS": "Челябинск, Ленина 1"},
                {"userId": 101, "address": "Челябинск, Кирова 2"},
                "ignored",
            ],
        }
    )

    assert result.auth_id == "auth-1"
    assert [address.user_id for address in result.addresses] == [100, 101]
    assert result.addresses[0].address == "Челябинск, Ленина 1"


def test_balance_from_json_object() -> None:
    """Проверяет разбор баланса и следующего платежа."""
    balance = Balance.from_json_object(
        {
            "balance": "125.50",
            "nextPayment": {"pay": 700, "text": "до 25 июня"},
            "debt": 0,
            "blocked": "N",
            "dateDelayLock": "2026-06-25",
        }
    )

    assert balance.balance == Decimal("125.50")
    assert balance.next_payment is not None
    assert balance.next_payment.amount == Decimal("700")
    assert balance.debt == Decimal("0")
    assert balance.blocked == "N"


def test_parse_datetime_handles_naive_value_as_utc() -> None:
    """Проверяет нормализацию даты без timezone в UTC."""
    assert parse_datetime("2026-06-19T12:30:00") == datetime(
        2026,
        6,
        19,
        12,
        30,
        tzinfo=UTC,
    )

"""Тесты типизированных моделей API IS74."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from pyis74.exceptions import IS74APIError
from pyis74.models import (
    Balance,
    Camera,
    HistoryEventKind,
    HistoryResponse,
    LkToken,
    MobileToken,
    PhoneConfirmationCheck,
    classify_history_event_type,
    parse_datetime,
)

HISTORY_PER_PAGE = 20


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
    with pytest.raises(IS74APIError, match="TOKEN or token"):
        MobileToken.from_json_object({"ACCESS_END": "2026-06-19T12:30:00Z"})


def test_mobile_token_accepts_lower_case_token_field() -> None:
    """Проверяет поддержку ответа с полем `token`."""
    token = MobileToken.from_json_object({"token": "mobile-token"})

    assert token.token == "mobile-token"


def test_lk_token_from_json_object() -> None:
    """Проверяет разбор CRM/LK token."""
    token = LkToken.from_json_object({"TOKEN": "lk-token"})

    assert token.token == "lk-token"


def test_phone_confirmation_check_parses_addresses() -> None:
    """Проверяет разбор списка адресов после подтверждения телефона."""
    result = PhoneConfirmationCheck.from_json_object(
        {
            "authId": "auth-1",
            "addresses": [
                {"USER_ID": "100", "ADDRESS": "Тестоград, ул. Примерная, 1"},
                {"userId": 101, "address": "Тестоград, ул. Учебная, 2"},
                "ignored",
            ],
        }
    )

    assert result.auth_id == "auth-1"
    assert [address.user_id for address in result.addresses] == [100, 101]
    assert result.addresses[0].address == "Тестоград, ул. Примерная, 1"


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


def test_history_response_from_json_object() -> None:
    """Проверяет разбор страницы истории."""
    history = HistoryResponse.from_json_object(
        {
            "data": [
                {
                    "create_date": "2026-06-19T12:30:00Z",
                    "type": "HANDSET_CALL",
                    "params": {
                        "mac": "02:00:00:00:00:01",
                        "address": "Тестоград, ул. Примерная, 1",
                        "entranceTitle": "Подъезд 1",
                    },
                    "image_link": "https://example.invalid/history/snapshot.jpg",
                }
            ],
            "page": "1",
            "perPage": str(HISTORY_PER_PAGE),
            "count": "1",
        }
    )

    assert history.page == 1
    assert history.per_page == HISTORY_PER_PAGE
    assert history.count == 1
    assert len(history.events) == 1
    event = history.events[0]
    assert event.created_at == datetime(2026, 6, 19, 12, 30, tzinfo=UTC)
    assert event.event_type == "HANDSET_CALL"
    assert event.kind is HistoryEventKind.CALL
    assert event.is_call is True
    assert event.is_open is False
    assert event.params is not None
    assert event.params.entrance_title == "Подъезд 1"


def test_history_response_filters_events() -> None:
    """Проверяет локальные фильтры истории."""
    history = HistoryResponse.from_json_object(
        {
            "data": [
                {"create_date": "2026-06-19T12:30:00Z", "type": "OPEN_API"},
                {"create_date": "2026-06-19T12:31:00Z", "type": "HANDSET_CALL"},
                {
                    "create_date": "2026-06-19T12:32:00Z",
                    "type": "OTHER_EVENT",
                    "image_link": "https://example.invalid/history/snapshot.jpg",
                },
            ],
            "page": "1",
            "perPage": str(HISTORY_PER_PAGE),
            "count": "3",
        }
    )

    assert [event.event_type for event in history.filter_events(kinds=("open", "call"))] == [
        "OPEN_API",
        "HANDSET_CALL",
    ]
    assert [event.event_type for event in history.filter_events(event_types=("open_api",))] == [
        "OPEN_API"
    ]
    assert [event.event_type for event in history.filter_events(with_images=True)] == [
        "OTHER_EVENT"
    ]


def test_classify_history_event_type() -> None:
    """Проверяет нормализацию типов истории."""
    assert classify_history_event_type("OPEN_INTERNAL") is HistoryEventKind.OPEN
    assert classify_history_event_type("HANDSET_CALL") is HistoryEventKind.CALL
    assert classify_history_event_type("UNKNOWN") is HistoryEventKind.OTHER
    assert classify_history_event_type(None) is HistoryEventKind.OTHER


def test_camera_streams_collects_urls() -> None:
    """Проверяет компактную модель stream URL камеры."""
    camera = Camera.from_json_object(
        {
            "ID": 9100,
            "UUID": "00000000-0000-4000-8000-000000000001",
            "OBJECT": "CAMERA",
            "MEDIA": {
                "HLS": {
                    "LIVE": {
                        "MAIN": "https://example.invalid/hls/main.m3u8",
                        "LOW_LATENCY": "https://example.invalid/hls/ll.m3u8",
                    },
                    "ARCHIVE": "https://example.invalid/hls/archive.m3u8",
                },
                "MSE": {"LIVE": "wss://example.invalid/ws/mse"},
                "SNAPSHOT": {
                    "LIVE": {
                        "MAIN": "https://example.invalid/snapshot.jpg",
                        "LOSSY": "https://example.invalid/snapshot_lossy.jpg",
                    }
                },
            },
            "REALTIME_WS": {
                "combined": "wss://example.invalid/ws/combined",
                "main": "wss://example.invalid/ws/main",
                "sub": "wss://example.invalid/ws/sub",
            },
        }
    )

    assert camera.streams.has_any is True
    assert camera.streams.items() == (
        ("hls.live.main", "https://example.invalid/hls/main.m3u8"),
        ("hls.live.low_latency", "https://example.invalid/hls/ll.m3u8"),
        ("hls.archive", "https://example.invalid/hls/archive.m3u8"),
        ("mse.live", "wss://example.invalid/ws/mse"),
        ("snapshot.live.main", "https://example.invalid/snapshot.jpg"),
        ("snapshot.live.lossy", "https://example.invalid/snapshot_lossy.jpg"),
        ("realtime_ws.combined", "wss://example.invalid/ws/combined"),
        ("realtime_ws.main", "wss://example.invalid/ws/main"),
        ("realtime_ws.sub", "wss://example.invalid/ws/sub"),
    )


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

"""Тесты домена истории IS74."""

import json
from datetime import UTC, date, datetime

import pytest
from pytest_httpx import HTTPXMock

from pyis74 import IS74, IS74Async, endpoints
from pyis74.types import JsonObject

HISTORY_PAGE = 2
HISTORY_PER_PAGE = 5
HISTORY_COUNT = 11
BUYER_ID = 1
HISTORY_URL = (
    "https://td-crm.is74.ru/api/user/history?from=2026-06-01&to=2026-06-19&page=2&perPage=5"
)


def build_history_payload() -> JsonObject:
    """Возвращает fixture страницы истории."""
    return {
        "data": [
            {
                "create_date": "2026-06-19T12:30:00Z",
                "type": "OPEN_API",
                "params": {
                    "mac": "02:00:00:00:00:01",
                    "address": "Тестоград, ул. Примерная, д. 1",
                    "entranceTitle": "Подъезд 1",
                },
                "image_link": "https://example.invalid/history/snapshot.jpg",
            }
        ],
        "page": HISTORY_PAGE,
        "perPage": HISTORY_PER_PAGE,
        "count": HISTORY_COUNT,
    }


@pytest.mark.asyncio
async def test_get_events_uses_lk_token_and_query_params(httpx_mock: HTTPXMock) -> None:
    """Проверяет запрос истории через LK token и фильтры."""
    httpx_mock.add_response(method="POST", url=endpoints.CRM_AUTH_LK, json={"TOKEN": "lk-token"})
    httpx_mock.add_response(method="GET", url=HISTORY_URL, json=build_history_payload())

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        history = await client.history.get_events(
            from_date=date(2026, 6, 1),
            to_date="2026-06-19",
            page=HISTORY_PAGE,
            per_page=HISTORY_PER_PAGE,
        )

    assert client.lk_token == "lk-token"
    assert history.page == HISTORY_PAGE
    assert history.per_page == HISTORY_PER_PAGE
    assert history.count == HISTORY_COUNT
    assert len(history.events) == 1
    event = history.events[0]
    assert event.create_date == "2026-06-19T12:30:00Z"
    assert event.created_at == datetime(2026, 6, 19, 12, 30, tzinfo=UTC)
    assert event.event_type == "OPEN_API"
    assert event.params is not None
    assert event.params.mac == "02:00:00:00:00:01"
    assert event.params.entrance_title == "Подъезд 1"
    assert event.image_link == "https://example.invalid/history/snapshot.jpg"

    requests = httpx_mock.get_requests()
    assert json.loads(requests[0].content) == {"buyerId": BUYER_ID, "token": "mobile-token"}
    assert requests[1].headers["authorization"] == "Bearer lk-token"


def test_sync_client_gets_history_with_existing_lk_token(httpx_mock: HTTPXMock) -> None:
    """Проверяет синхронное получение истории с уже сохраненным LK token."""
    httpx_mock.add_response(
        method="GET",
        url=endpoints.CRM_HISTORY,
        json={"data": [], "page": 1, "perPage": 20, "count": 0},
    )

    history = IS74(backoff_factor=0, lk_token="lk-token").history.get_events()

    assert history.events == ()
    assert history.page == 1
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer lk-token"

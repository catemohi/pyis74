"""Тесты домена домофонов IS74."""

import pytest
from pytest_httpx import HTTPXMock

from pyis74 import IS74, IS74APIError, IS74Async, IS74AuthRequiredError, endpoints
from pyis74.models import DomofonRelay
from pyis74.types import JsonObject

API_RELAY_ID = 900001
CRM_RELAY_ID = 900002
BUILDING_ID = 900100
QR_STEP = 120
HTTP_OK = 200
HTTP_NO_CONTENT = 204
API_MAC = "02:00:00:00:01:01"
CRM_MAC = "02:00:00:00:02:01"


def build_api_relay_payload() -> JsonObject:
    """Возвращает fixture API-реле ворот."""
    return {
        "ADDRESS": ' "Ворота 1" Тестоград, ул. Примерная, д. 1',
        "BUILDING_ID": str(BUILDING_ID),
        "ENTRANCE_UID": "",
        "HAS_VIDEO": "0",
        "IS_MAIN": "0",
        "LINKS": {"open": f"https://api.is74.ru/domofon/relays/{API_RELAY_ID}/open"},
        "MAC_ADDR": API_MAC,
        "OPENER": {
            "mac": API_MAC,
            "relay_id": API_RELAY_ID,
            "relay_num": 1,
            "type": "api",
        },
        "PORCH_NUM": None,
        "QR_OPTIONS": None,
        "RELAY_DESCR": "Ворота 1п",
        "RELAY_ID": str(API_RELAY_ID),
        "RELAY_TYPE": "Шлагбаум/ворота",
        "SMART_INTERCOM": "0",
        "STATUS_CODE": "0",
        "STATUS_TEXT": "OK",
    }


def build_crm_relay_payload() -> JsonObject:
    """Возвращает fixture CRM-реле подъезда."""
    return {
        "ADDRESS": "Тестоград, ул. Примерная, д. 1, п. 1",
        "BUILDING_ID": str(BUILDING_ID),
        "ENTRANCE_UID": "00000000-0000-4000-8000-000000000001",
        "HAS_VIDEO": "1",
        "IMAGE_URL": "https://example.invalid/snapshot.jpg",
        "IS_MAIN": "1",
        "LINKS": {"open": f"https://td-crm.is74.ru/api/open/{CRM_MAC}/1"},
        "MAC_ADDR": CRM_MAC,
        "OPENER": {
            "mac": CRM_MAC,
            "relay_id": CRM_RELAY_ID,
            "relay_num": 1,
            "type": "crm",
        },
        "PORCH_NUM": "1",
        "QR_OPTIONS": {
            "isPrivate": 1,
            "lastChangeDate": "2025-10-16 19:53:44",
            "name": "qr",
            "value": {
                "length": 6,
                "salt": "salt",
                "step": QR_STEP,
                "window": 5,
            },
        },
        "RELAY_DESCR": None,
        "RELAY_ID": str(CRM_RELAY_ID),
        "RELAY_TYPE": "Главный вход",
        "SMART_INTERCOM": "1",
        "STATUS_CODE": "0",
        "STATUS_TEXT": "OK",
    }


@pytest.mark.asyncio
async def test_get_relays_parses_domofon_relays(httpx_mock: HTTPXMock) -> None:
    """Проверяет получение и парсинг списка реле."""
    httpx_mock.add_response(
        method="GET",
        url=endpoints.DOMOFON_RELAYS,
        json=[build_api_relay_payload(), build_crm_relay_payload()],
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        relays = await client.domofon.get_relays()

    assert [relay.relay_id for relay in relays] == [API_RELAY_ID, CRM_RELAY_ID]
    assert relays[0].has_video is False
    assert relays[0].opener is not None
    assert relays[0].opener.type == "api"
    assert relays[1].has_video is True
    assert relays[1].is_main is True
    assert relays[1].qr_options is not None
    assert relays[1].qr_options.value is not None
    assert relays[1].qr_options.value.step == QR_STEP
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer mobile-token"


@pytest.mark.asyncio
async def test_get_relays_requires_mobile_token() -> None:
    """Проверяет ошибку при запросе реле без token."""
    async with IS74Async(backoff_factor=0) as client:
        with pytest.raises(IS74AuthRequiredError):
            await client.domofon.get_relays()


@pytest.mark.asyncio
async def test_get_relay_uses_api_id_endpoint(httpx_mock: HTTPXMock) -> None:
    """Проверяет получение одного реле по `RELAY_ID`."""
    httpx_mock.add_response(
        method="GET",
        url=endpoints.DOMOFON_RELAY_TEMPLATE.format(relay_id=API_RELAY_ID),
        json=build_api_relay_payload(),
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        relay = await client.domofon.get_relay(API_RELAY_ID)

    assert relay.relay_id == API_RELAY_ID
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer mobile-token"


@pytest.mark.asyncio
async def test_get_relays_rejects_non_list_response(httpx_mock: HTTPXMock) -> None:
    """Проверяет валидацию формата ответа `/domofon/relays`."""
    httpx_mock.add_response(method="GET", url=endpoints.DOMOFON_RELAYS, json={"bad": True})

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        with pytest.raises(IS74APIError, match="not a list"):
            await client.domofon.get_relays()


@pytest.mark.asyncio
async def test_open_relay_uses_api_open_link_with_from_app(httpx_mock: HTTPXMock) -> None:
    """Проверяет открытие API-реле через ссылку из `LINKS.open`."""
    httpx_mock.add_response(
        method="POST",
        url=f"https://api.is74.ru/domofon/relays/{API_RELAY_ID}/open?from=app",
        json={"result": "ok"},
    )
    relay = DomofonRelay.from_json_object(build_api_relay_payload())

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        result = await client.domofon.open_relay(relay)

    assert result.status_code == HTTP_OK
    assert result.payload == {"result": "ok"}
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer mobile-token"


@pytest.mark.asyncio
async def test_open_relay_by_api_id_uses_direct_api_path(httpx_mock: HTTPXMock) -> None:
    """Проверяет прямое открытие API-реле по `RELAY_ID`."""
    httpx_mock.add_response(
        method="POST",
        url=f"https://api.is74.ru/domofon/relays/{API_RELAY_ID}/open?from=app",
        json={"result": "ok"},
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        result = await client.domofon.open_relay_by_api_id(API_RELAY_ID)

    assert result.status_code == HTTP_OK
    assert result.payload == {"result": "ok"}
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer mobile-token"


@pytest.mark.asyncio
async def test_open_relay_by_id_uses_crm_open_link(httpx_mock: HTTPXMock) -> None:
    """Проверяет открытие CRM-реле через LK token и ссылку из списка реле."""
    crm_url = f"https://td-crm.is74.ru/api/open/{CRM_MAC}/1"
    httpx_mock.add_response(
        method="GET",
        url=endpoints.DOMOFON_RELAYS,
        json=[build_api_relay_payload(), build_crm_relay_payload()],
    )
    httpx_mock.add_response(method="POST", url=endpoints.CRM_AUTH_LK, json={"TOKEN": "lk-token"})
    httpx_mock.add_response(method="GET", url=crm_url, status_code=HTTP_NO_CONTENT)

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        result = await client.domofon.open_relay_by_id(CRM_RELAY_ID)

    assert result.status_code == HTTP_NO_CONTENT
    assert result.payload is None
    requests = httpx_mock.get_requests()
    assert [str(request.url) for request in requests] == [
        endpoints.DOMOFON_RELAYS,
        endpoints.CRM_AUTH_LK,
        crm_url,
    ]
    assert requests[0].headers["authorization"] == "Bearer mobile-token"
    assert requests[2].headers["authorization"] == "Bearer lk-token"


def test_sync_client_gets_relays(httpx_mock: HTTPXMock) -> None:
    """Проверяет синхронную обертку домена домофонов."""
    httpx_mock.add_response(
        method="GET",
        url=endpoints.DOMOFON_RELAYS,
        json=[build_api_relay_payload()],
    )

    relays = IS74(backoff_factor=0, mobile_token="mobile-token").domofon.get_relays()

    assert relays[0].relay_id == API_RELAY_ID

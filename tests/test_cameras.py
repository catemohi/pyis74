"""Тесты домена камер IS74."""

from decimal import Decimal
from urllib.parse import parse_qs

import pytest
from pytest_httpx import HTTPXMock

from pyis74 import IS74, IS74APIError, IS74Async, endpoints
from pyis74.types import JsonObject

GROUP_ID = 9000
CAMERA_ID = 9100
CAMERA_UUID = "00000000-0000-4000-8000-000000000001"
SECOND_CAMERA_UUID = "00000000-0000-4000-8000-000000000002"


def build_camera_payload() -> JsonObject:
    """Возвращает синтетический payload камеры."""
    return {
        "ID": CAMERA_ID,
        "UUID": CAMERA_UUID,
        "OBJECT": "CAMERA",
        "NAME": "Тестовая камера",
        "SHORT_NAME": "Камера",
        "ADDRESS": "Тестоград, ул. Примерная, д. 1",
        "PORCH": "1",
        "HLS": "/live/cam9100-master.m3u8",
        "REALTIME_HLS": "/live/cam9100-realtime-master.m3u8",
        "LINK_TO_ADMIN": None,
        "SLEEP_MODE": None,
        "STREAM_EXISTS": True,
        "ACCESS": {
            "LIVE": {"STATUS": True, "REASON": ""},
            "ARCHIVE": {"STATUS": True, "REASON": "", "AUDIO": True},
            "MOVEMENT": {"STATUS": False, "REASON": "Нет доступа"},
            "DOWNLOAD": {"STATUS": False, "REASON": "Нет доступа"},
            "PTZ": {"STATUS": False, "REASON": ""},
        },
        "ARCHIVE": {
            "LINK": "archive/cam9100.m3u8",
            "START_TIME": "12.06.2026 00:00",
            "STOP_TIME": "19.06.2026 00:00",
        },
        "COORDINATES": {"LATITUDE": "55.000100", "LONGITUDE": "61.000200"},
        "POSITION": {"AZIMUTH": 180, "LATITUDE": 55.0001, "LONGITUDE": 61.0002},
        "MEDIA": {
            "HLS": {
                "LIVE": {
                    "MAIN": "https://example.invalid/hls/main.m3u8?token=example",
                    "LOW_LATENCY": "https://example.invalid/hls/ll.m3u8?token=example",
                },
                "ARCHIVE": "https://example.invalid/hls/archive.m3u8?token=example",
            },
            "MSE": {"LIVE": "wss://example.invalid/ws/mse?token=example"},
            "SNAPSHOT": {
                "LIVE": {
                    "MAIN": "https://example.invalid/snapshot.jpg?token=example",
                    "LOSSY": "https://example.invalid/snapshot_lossy.jpg?token=example",
                }
            },
        },
        "REALTIME_WS": {
            "combined": "wss://example.invalid/ws/mse?token=example",
            "main": "wss://example.invalid/ws/mse?token=example&quality=main",
            "sub": "wss://example.invalid/ws/mse?token=example&quality=sub",
        },
        "SNAPSHOT": {
            "HD": "/snapshots/cam9100.jpg",
            "LOSSY": "/snapshots/cam9100_lossy.jpg",
        },
        "SUPPORTED_FEATURES": {
            "doorbell": False,
            "ptz": False,
            "setup_motion_detect": True,
            "voice": False,
            "zoom": False,
        },
        "VA_FEATURES": {"annotation": False},
    }


@pytest.mark.asyncio
async def test_get_self_cams_with_group(httpx_mock: HTTPXMock) -> None:
    """Проверяет получение self-cams групп."""
    httpx_mock.add_response(
        method="GET",
        url=endpoints.CAMS_SELF_WITH_GROUP,
        json=[
            {
                "id": str(GROUP_ID),
                "groupName": "Тестовая группа",
                "isManagementCompanyOwns": True,
                "cameras": [build_camera_payload()],
            }
        ],
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        groups = await client.cameras.get_self_cams_with_group()

    assert len(groups) == 1
    group = groups[0]
    assert group.group_id == str(GROUP_ID)
    assert group.is_management_company_owns is True
    assert len(group.cameras) == 1
    camera = group.cameras[0]
    assert camera.camera_id == CAMERA_ID
    assert camera.uuid == CAMERA_UUID
    assert camera.coordinates is not None
    assert camera.coordinates.latitude == Decimal("55.000100")
    assert camera.position is not None
    assert camera.position.longitude == Decimal("61.0002")
    assert camera.access is not None
    assert camera.access.archive is not None
    assert camera.access.archive.audio is True
    assert camera.media is not None
    assert camera.media.hls is not None
    assert camera.media.hls.live is not None
    assert camera.media.hls.live.low_latency is not None

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer mobile-token"


@pytest.mark.asyncio
async def test_get_groups_uses_self_cams_query(httpx_mock: HTTPXMock) -> None:
    """Проверяет получение групп с query-параметром `selfCams`."""
    httpx_mock.add_response(
        method="GET",
        url="https://cams.is74.ru/api/get-group/?selfCams=true",
        json=[{"ID": "own", "NAME": "Свои камеры", "OBJECT": "GROUP"}],
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        groups = await client.cameras.get_groups(self_cams=True)

    assert groups[0].group_id == "own"
    assert groups[0].name == "Свои камеры"


@pytest.mark.asyncio
async def test_get_group_splits_groups_and_cameras(httpx_mock: HTTPXMock) -> None:
    """Проверяет разбор смешанного списка группы."""
    httpx_mock.add_response(
        method="GET",
        url=f"https://cams.is74.ru/api/get-group/{GROUP_ID}",
        json=[
            {"ID": 9001, "NAME": "Дочерняя группа", "OBJECT": "GROUP"},
            build_camera_payload(),
        ],
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        content = await client.cameras.get_group(GROUP_ID)

    assert len(content.groups) == 1
    assert content.groups[0].group_id == "9001"
    assert len(content.cameras) == 1
    assert content.cameras[0].name == "Тестовая камера"


@pytest.mark.asyncio
async def test_get_limited_info_by_uuids_posts_form(httpx_mock: HTTPXMock) -> None:
    """Проверяет batch limited-info запрос по UUID."""
    httpx_mock.add_response(
        method="POST",
        url=endpoints.CAMS_LIMITED_INFO_BY_UUID,
        json={str(CAMERA_ID): build_camera_payload()},
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        info = await client.cameras.get_limited_info_by_uuids((CAMERA_UUID, SECOND_CAMERA_UUID))

    assert len(info.cameras) == 1
    assert info.cameras[0].camera_id == CAMERA_ID

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer mobile-token"
    assert request.headers["content-type"] == "application/x-www-form-urlencoded"
    parsed_form = parse_qs(request.content.decode())
    assert parsed_form == {"CAMERA_UUIDS[]": [CAMERA_UUID, SECOND_CAMERA_UUID]}


@pytest.mark.asyncio
async def test_get_limited_info_by_uuids_skips_empty_request(httpx_mock: HTTPXMock) -> None:
    """Проверяет, что пустой список UUID не отправляет HTTP-запрос."""
    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        info = await client.cameras.get_limited_info_by_uuids(())

    assert info.cameras == ()
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_get_group_rejects_non_list_response(httpx_mock: HTTPXMock) -> None:
    """Проверяет ошибку на неожиданной форме ответа группы."""
    httpx_mock.add_response(
        method="GET",
        url=f"https://cams.is74.ru/api/get-group/{GROUP_ID}",
        json={"unexpected": "object"},
    )

    async with IS74Async(backoff_factor=0, mobile_token="mobile-token") as client:
        with pytest.raises(IS74APIError, match="not a list"):
            await client.cameras.get_group(GROUP_ID)


def test_sync_client_gets_camera_groups(httpx_mock: HTTPXMock) -> None:
    """Проверяет синхронную обертку домена камер."""
    httpx_mock.add_response(
        method="GET",
        url=endpoints.CAMS_GET_GROUP,
        json=[{"ID": GROUP_ID, "NAME": "Тестовая группа", "OBJECT": "GROUP"}],
    )

    groups = IS74(backoff_factor=0, mobile_token="mobile-token").cameras.get_groups()

    assert len(groups) == 1
    assert groups[0].group_id == str(GROUP_ID)

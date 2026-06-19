"""Базовые URL и известные endpoint API IS74."""

from enum import StrEnum, unique
from typing import Final
from urllib.parse import urlparse


@unique
class BaseUrl(StrEnum):
    """Базовые URL сервисов IS74."""

    API = "https://api.is74.ru"
    CAMS = "https://cams.is74.ru"
    CDN_CAMS = "https://cdn.cams.is74.ru"
    CRM = "https://td-crm.is74.ru"
    FIREBASE_REMOTE_CONFIG = "https://firebaseremoteconfig.googleapis.com"
    TRACK = "https://track.is74.ru"


def is_absolute_url(value: str) -> bool:
    """Проверяет, является ли строка абсолютным HTTP(S) URL.

    Args:
        value: Проверяемая строка.

    Returns:
        `True`, если строка содержит схему `http` или `https` и сетевой адрес.
    """
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def join_url(base_url: BaseUrl | str, path: str) -> str:
    """Собирает абсолютный URL из базового URL и пути.

    Args:
        base_url: Базовый URL сервиса.
        path: Относительный путь endpoint или уже готовый абсолютный URL.

    Returns:
        Абсолютный URL.
    """
    if is_absolute_url(path):
        return path

    normalized_base = str(base_url).rstrip("/")
    normalized_path = path.lstrip("/")
    if not normalized_path:
        return normalized_base
    return f"{normalized_base}/{normalized_path}"


AUTH_MOBILE: Final = join_url(BaseUrl.API, "/auth/mobile")
AUTH_SEND_SMS: Final = join_url(BaseUrl.API, "/mobile/auth/send-sms")
AUTH_CONFIRM: Final = join_url(BaseUrl.API, "/mobile/auth/confirm")
AUTH_GET_CONFIRM: Final = join_url(BaseUrl.API, "/mobile/auth/get-confirm")
AUTH_CHECK_CONFIRM: Final = join_url(BaseUrl.API, "/mobile/auth/check-confirm")
AUTH_GET_TOKEN: Final = join_url(BaseUrl.API, "/mobile/auth/get-token")
TOKEN_CHECK: Final = join_url(BaseUrl.API, "/token/check")

USER_STATUS: Final = join_url(BaseUrl.API, "/user/service/status")
USER_INFO: Final = join_url(BaseUrl.API, "/user/user")
USER_ADDRESS: Final = join_url(BaseUrl.API, "/user/address")
USER_BALANCE: Final = join_url(BaseUrl.API, "/user/balance")

DOMOFON_RELAYS: Final = join_url(BaseUrl.API, "/domofon/relays")
DOMOFON_RELAY_OPEN_TEMPLATE: Final = join_url(BaseUrl.API, "/domofon/relays/{relay_id}/open")

CAMS_SELF_WITH_GROUP: Final = join_url(BaseUrl.CAMS, "/api/self-cams-with-group")
CAMS_GET_GROUP: Final = join_url(BaseUrl.CAMS, "/api/get-group/")
CAMS_LIMITED_INFO_BY_UUID: Final = join_url(BaseUrl.CAMS, "/api/limited-info-by-uuid")

CRM_AUTH_LK: Final = join_url(BaseUrl.CRM, "/api/auth-lk")
CRM_HISTORY: Final = join_url(BaseUrl.CRM, "/api/user/history")
CRM_SIP_ACCOUNT: Final = join_url(BaseUrl.CRM, "/api/sip-account")
CRM_USER_DEVICE: Final = join_url(BaseUrl.CRM, "/api/user-device")

TRACK_MOBILE: Final = join_url(BaseUrl.TRACK, "/mobile/track")

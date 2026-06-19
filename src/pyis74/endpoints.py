"""Базовые URL и известные endpoint API IS74."""

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final
from urllib.parse import urlparse

DEFAULT_SCHEME: Final = "https"
DEFAULT_BASE_DOMAIN: Final = "is74.ru"


@unique
class BaseUrl(StrEnum):
    """Базовые URL сервисов IS74."""

    API = "https://api.is74.ru"
    CAMS = "https://cams.is74.ru"
    CDN_CAMS = "https://cdn.cams.is74.ru"
    CRM = "https://td-crm.is74.ru"
    FIREBASE_REMOTE_CONFIG = "https://firebaseremoteconfig.googleapis.com"
    TRACK = "https://track.is74.ru"


@dataclass(frozen=True, slots=True, kw_only=True)
class IS74ServiceUrls:
    """Базовые URL сервисов IS74 для конкретного домена.

    Args:
        base_domain: Корневой домен IS74 без имени сервиса, например `is74.ru`.
        scheme: HTTP-схема для сервисов IS74.
    """

    base_domain: str = DEFAULT_BASE_DOMAIN
    scheme: str = DEFAULT_SCHEME

    def __post_init__(self) -> None:
        """Нормализует и проверяет домен."""
        normalized_domain = normalize_base_domain(self.base_domain)
        normalized_scheme = self.scheme.rstrip(":/")
        if not normalized_domain:
            msg = "base_domain must not be empty."
            raise ValueError(msg)
        if normalized_scheme not in {"http", "https"}:
            msg = "scheme must be either 'http' or 'https'."
            raise ValueError(msg)
        object.__setattr__(self, "base_domain", normalized_domain)
        object.__setattr__(self, "scheme", normalized_scheme)

    @property
    def api(self) -> str:
        """Возвращает base URL mobile API."""
        return self._service_url("api")

    @property
    def cams(self) -> str:
        """Возвращает base URL camera API."""
        return self._service_url("cams")

    @property
    def cdn_cams(self) -> str:
        """Возвращает base URL camera CDN."""
        return self._service_url("cdn.cams")

    @property
    def crm(self) -> str:
        """Возвращает base URL CRM/LK API."""
        return self._service_url("td-crm")

    @property
    def track(self) -> str:
        """Возвращает base URL track API."""
        return self._service_url("track")

    @property
    def firebase_remote_config(self) -> str:
        """Возвращает внешний base URL Firebase Remote Config."""
        return str(BaseUrl.FIREBASE_REMOTE_CONFIG)

    @property
    def auth_mobile(self) -> str:
        """Возвращает URL password-auth endpoint."""
        return self.join(BaseUrl.API, "/auth/mobile")

    @property
    def auth_send_sms(self) -> str:
        """Возвращает URL phone-auth start endpoint."""
        return self.join(BaseUrl.API, "/mobile/auth/send-sms")

    @property
    def auth_confirm(self) -> str:
        """Возвращает URL phone-auth confirm endpoint."""
        return self.join(BaseUrl.API, "/mobile/auth/confirm")

    @property
    def auth_get_confirm(self) -> str:
        """Возвращает URL legacy phone-auth get-confirm endpoint."""
        return self.join(BaseUrl.API, "/mobile/auth/get-confirm")

    @property
    def auth_check_confirm(self) -> str:
        """Возвращает URL legacy phone-auth check-confirm endpoint."""
        return self.join(BaseUrl.API, "/mobile/auth/check-confirm")

    @property
    def auth_get_token(self) -> str:
        """Возвращает URL phone-auth token endpoint."""
        return self.join(BaseUrl.API, "/mobile/auth/get-token")

    @property
    def token_check(self) -> str:
        """Возвращает URL token-check endpoint."""
        return self.join(BaseUrl.API, "/token/check")

    @property
    def user_status(self) -> str:
        """Возвращает URL user service status endpoint."""
        return self.join(BaseUrl.API, "/user/service/status")

    @property
    def user_info(self) -> str:
        """Возвращает URL user info endpoint."""
        return self.join(BaseUrl.API, "/user/user")

    @property
    def user_address(self) -> str:
        """Возвращает URL user address endpoint."""
        return self.join(BaseUrl.API, "/user/address")

    @property
    def user_balance(self) -> str:
        """Возвращает URL user balance endpoint."""
        return self.join(BaseUrl.API, "/user/balance")

    @property
    def domofon_relays(self) -> str:
        """Возвращает URL списка домофонных реле."""
        return self.join(BaseUrl.API, "/domofon/relays")

    @property
    def domofon_relay_template(self) -> str:
        """Возвращает URL-шаблон одного домофонного реле."""
        return self.join(BaseUrl.API, "/domofon/relays/{relay_id}")

    @property
    def domofon_relay_open_template(self) -> str:
        """Возвращает URL-шаблон открытия домофонного реле."""
        return self.join(BaseUrl.API, "/domofon/relays/{relay_id}/open")

    @property
    def cams_self_with_group(self) -> str:
        """Возвращает URL endpoint собственных камер с группами."""
        return self.join(BaseUrl.CAMS, "/api/self-cams-with-group")

    @property
    def cams_get_group(self) -> str:
        """Возвращает URL endpoint просмотра групп камер."""
        return self.join(BaseUrl.CAMS, "/api/get-group/")

    @property
    def cams_limited_info_by_uuid(self) -> str:
        """Возвращает URL endpoint limited camera info."""
        return self.join(BaseUrl.CAMS, "/api/limited-info-by-uuid")

    @property
    def crm_auth_lk(self) -> str:
        """Возвращает URL CRM/LK auth endpoint."""
        return self.join(BaseUrl.CRM, "/api/auth-lk")

    @property
    def crm_history(self) -> str:
        """Возвращает URL CRM history endpoint."""
        return self.join(BaseUrl.CRM, "/api/user/history")

    @property
    def crm_user_device(self) -> str:
        """Возвращает URL CRM user-device endpoint."""
        return self.join(BaseUrl.CRM, "/api/user-device")

    @property
    def track_mobile(self) -> str:
        """Возвращает URL mobile track endpoint."""
        return self.join(BaseUrl.TRACK, "/mobile/track")

    def join(self, base_url: BaseUrl | str, path: str) -> str:
        """Собирает абсолютный URL с учетом домена клиента.

        Args:
            base_url: Идентификатор сервиса или готовый base URL.
            path: Относительный путь endpoint или уже готовый абсолютный URL.

        Returns:
            Абсолютный URL.
        """
        return join_url(self.resolve_base_url(base_url), path)

    def resolve_base_url(self, base_url: BaseUrl | str) -> str:
        """Возвращает base URL сервиса для домена клиента.

        Args:
            base_url: Значение `BaseUrl` или явная строка URL.

        Returns:
            Base URL, привязанный к `base_domain`, если передан `BaseUrl`.
        """
        if not isinstance(base_url, BaseUrl):
            return str(base_url)

        return {
            BaseUrl.API: self.api,
            BaseUrl.CAMS: self.cams,
            BaseUrl.CDN_CAMS: self.cdn_cams,
            BaseUrl.CRM: self.crm,
            BaseUrl.FIREBASE_REMOTE_CONFIG: self.firebase_remote_config,
            BaseUrl.TRACK: self.track,
        }[base_url]

    def is_api_url(self, value: str) -> bool:
        """Проверяет, что URL относится к mobile API текущего домена."""
        return value.startswith(self.api)

    def is_crm_url(self, value: str) -> bool:
        """Проверяет, что URL относится к CRM API текущего домена."""
        return value.startswith(self.crm)

    def _service_url(self, service: str) -> str:
        return f"{self.scheme}://{service}.{self.base_domain}"


def normalize_base_domain(value: str) -> str:
    """Нормализует домен IS74.

    Args:
        value: Домен вида `is74.ru` или URL вида `https://is74.ru`.

    Returns:
        Домен без схемы и завершающего слеша.
    """
    stripped = value.strip().rstrip("/")
    parsed = urlparse(stripped)
    if parsed.netloc:
        return parsed.netloc
    return stripped


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


DEFAULT_SERVICE_URLS: Final = IS74ServiceUrls()

AUTH_MOBILE: Final = DEFAULT_SERVICE_URLS.auth_mobile
AUTH_SEND_SMS: Final = DEFAULT_SERVICE_URLS.auth_send_sms
AUTH_CONFIRM: Final = DEFAULT_SERVICE_URLS.auth_confirm
AUTH_GET_CONFIRM: Final = DEFAULT_SERVICE_URLS.auth_get_confirm
AUTH_CHECK_CONFIRM: Final = DEFAULT_SERVICE_URLS.auth_check_confirm
AUTH_GET_TOKEN: Final = DEFAULT_SERVICE_URLS.auth_get_token
TOKEN_CHECK: Final = DEFAULT_SERVICE_URLS.token_check

USER_STATUS: Final = DEFAULT_SERVICE_URLS.user_status
USER_INFO: Final = DEFAULT_SERVICE_URLS.user_info
USER_ADDRESS: Final = DEFAULT_SERVICE_URLS.user_address
USER_BALANCE: Final = DEFAULT_SERVICE_URLS.user_balance

DOMOFON_RELAYS: Final = DEFAULT_SERVICE_URLS.domofon_relays
DOMOFON_RELAY_TEMPLATE: Final = DEFAULT_SERVICE_URLS.domofon_relay_template
DOMOFON_RELAY_OPEN_TEMPLATE: Final = DEFAULT_SERVICE_URLS.domofon_relay_open_template

CAMS_SELF_WITH_GROUP: Final = DEFAULT_SERVICE_URLS.cams_self_with_group
CAMS_GET_GROUP: Final = DEFAULT_SERVICE_URLS.cams_get_group
CAMS_LIMITED_INFO_BY_UUID: Final = DEFAULT_SERVICE_URLS.cams_limited_info_by_uuid

CRM_AUTH_LK: Final = DEFAULT_SERVICE_URLS.crm_auth_lk
CRM_HISTORY: Final = DEFAULT_SERVICE_URLS.crm_history
CRM_USER_DEVICE: Final = DEFAULT_SERVICE_URLS.crm_user_device

TRACK_MOBILE: Final = DEFAULT_SERVICE_URLS.track_mobile

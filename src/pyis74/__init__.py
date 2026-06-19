"""Публичный пакет библиотеки pyis74.

Модуль экспортирует основные клиенты, исключения и низкоуровневые типы, которые нужны
пользователям библиотеки.
"""

from importlib.metadata import PackageNotFoundError, version

from pyis74.client import IS74, IS74Async
from pyis74.endpoints import BaseUrl
from pyis74.exceptions import (
    IS74APIError,
    IS74AuthError,
    IS74AuthRequiredError,
    IS74Error,
    IS74HTTPError,
    IS74RateLimitError,
    IS74TransportError,
)
from pyis74.models import (
    AccountSummary,
    Address,
    AddressCandidate,
    Balance,
    DomofonLinks,
    DomofonOpener,
    DomofonOpenResult,
    DomofonQrOptions,
    DomofonQrValue,
    DomofonRelay,
    MobileToken,
    NextPayment,
    PhoneConfirmationCheck,
    PhoneConfirmationStart,
    ServiceStatus,
    UserInfo,
)
from pyis74.options import ClientRequestOptions
from pyis74.transport import IS74Transport, RequestOptions
from pyis74.types import JsonObject, JsonValue

try:
    __version__ = version("pyis74")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = (
    "IS74",
    "AccountSummary",
    "Address",
    "AddressCandidate",
    "Balance",
    "BaseUrl",
    "ClientRequestOptions",
    "DomofonLinks",
    "DomofonOpenResult",
    "DomofonOpener",
    "DomofonQrOptions",
    "DomofonQrValue",
    "DomofonRelay",
    "IS74APIError",
    "IS74Async",
    "IS74AuthError",
    "IS74AuthRequiredError",
    "IS74Error",
    "IS74HTTPError",
    "IS74RateLimitError",
    "IS74Transport",
    "IS74TransportError",
    "JsonObject",
    "JsonValue",
    "MobileToken",
    "NextPayment",
    "PhoneConfirmationCheck",
    "PhoneConfirmationStart",
    "RequestOptions",
    "ServiceStatus",
    "UserInfo",
    "__version__",
)

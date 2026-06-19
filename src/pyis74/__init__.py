"""Публичный пакет библиотеки pyis74.

Модуль экспортирует основные клиенты, исключения и низкоуровневые типы, которые нужны
пользователям библиотеки на первом этапе реализации.
"""

from importlib.metadata import PackageNotFoundError, version

from pyis74.client import IS74, ClientRequestOptions, IS74Async
from pyis74.endpoints import BaseUrl
from pyis74.exceptions import (
    IS74APIError,
    IS74AuthError,
    IS74Error,
    IS74HTTPError,
    IS74RateLimitError,
    IS74TransportError,
)
from pyis74.transport import IS74Transport, RequestOptions
from pyis74.types import JsonObject, JsonValue

try:
    __version__ = version("pyis74")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = (
    "IS74",
    "BaseUrl",
    "ClientRequestOptions",
    "IS74APIError",
    "IS74Async",
    "IS74AuthError",
    "IS74Error",
    "IS74HTTPError",
    "IS74RateLimitError",
    "IS74Transport",
    "IS74TransportError",
    "JsonObject",
    "JsonValue",
    "RequestOptions",
    "__version__",
)

"""Параметры публичных запросов клиента pyis74."""

from __future__ import annotations

from dataclasses import dataclass

from pyis74.endpoints import BaseUrl
from pyis74.types import JsonValue, QueryParams


@dataclass(frozen=True, slots=True, kw_only=True)
class ClientRequestOptions:
    """Параметры запроса публичного клиента.

    Args:
        base_url: Базовый URL для относительного endpoint.
        auth_token: Bearer-токен авторизации.
        headers: Дополнительные HTTP-заголовки.
        params: Query-параметры.
        json_body: JSON-тело запроса.
        form: Form-urlencoded данные запроса.
        content: Текстовое или бинарное тело запроса.
    """

    base_url: BaseUrl | str = BaseUrl.API
    auth_token: str | None = None
    headers: dict[str, str] | None = None
    params: QueryParams | None = None
    json_body: JsonValue | None = None
    form: dict[str, str] | None = None
    content: str | bytes | None = None

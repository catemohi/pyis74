"""Исключения библиотеки pyis74."""

from dataclasses import dataclass

from pyis74.types import JsonValue


class IS74Error(Exception):
    """Базовое исключение библиотеки pyis74."""


class IS74TransportError(IS74Error):
    """Ошибка сетевого transport-слоя до получения валидного HTTP-ответа."""


@dataclass(frozen=True, slots=True)
class HTTPErrorContext:
    """Контекст HTTP-ошибки от API IS74.

    Args:
        status_code: HTTP-код ответа.
        method: HTTP-метод запроса.
        url: URL запроса.
        response_text: Текст ответа сервера.
    """

    status_code: int
    method: str
    url: str
    response_text: str


class IS74HTTPError(IS74Error):
    """Ошибка HTTP-ответа от API IS74."""

    def __init__(self, context: HTTPErrorContext) -> None:
        """Создает исключение HTTP-уровня.

        Args:
            context: Контекст ответа сервера.
        """
        self.context = context
        message = (
            f"IS74 API returned HTTP {context.status_code} "
            f"for {context.method.upper()} {context.url}."
        )
        super().__init__(message)


class IS74AuthError(IS74HTTPError):
    """Ошибка авторизации или отклоненный API токен."""


class IS74AuthRequiredError(IS74Error):
    """Ошибка вызова метода, которому нужен mobile access token."""


class IS74RateLimitError(IS74HTTPError):
    """Ошибка ограничения частоты запросов со стороны API."""


class IS74APIError(IS74Error):
    """Ошибка, описанная внутри успешного JSON-ответа API."""

    def __init__(self, message: str, payload: JsonValue | None = None) -> None:
        """Создает исключение прикладного API-уровня.

        Args:
            message: Сообщение API или нормализованное описание ошибки.
            payload: JSON-ответ, из которого была извлечена ошибка.
        """
        self.payload = payload
        super().__init__(message)

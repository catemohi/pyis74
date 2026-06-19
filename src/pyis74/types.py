"""Общие типы данных для библиотеки pyis74.

Модуль описывает JSON-значения и небольшие helpers для проверки данных, которые приходят
из внешнего API. На границе с `httpx` JSON сначала считается неизвестным `object`, а затем
явно приводится к этим типам.
"""

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]
type QueryValue = str | int | float | bool | None
type QueryParams = dict[str, QueryValue]


def normalize_json_value(value: object) -> JsonValue:
    """Проверяет и возвращает значение, совместимое с JSON.

    Args:
        value: Значение, полученное из внешнего JSON-парсера.

    Returns:
        Типизированное JSON-значение.

    Raises:
        TypeError: Значение содержит неподдерживаемый тип или ключ словаря не является строкой.
    """
    if value is None or isinstance(value, str | int | float | bool):
        return value

    if isinstance(value, list):
        return [normalize_json_value(item) for item in value]

    if isinstance(value, dict):
        normalized: JsonObject = {}
        for key, item in value.items():
            if not isinstance(key, str):
                msg = "JSON object keys must be strings."
                raise TypeError(msg)
            normalized[key] = normalize_json_value(item)
        return normalized

    msg = f"Unsupported JSON value type: {type(value).__name__}."
    raise TypeError(msg)


def normalize_json_object(value: object) -> JsonObject:
    """Проверяет, что значение является JSON-объектом.

    Args:
        value: Значение, полученное из внешнего JSON-парсера.

    Returns:
        Типизированный JSON-объект.

    Raises:
        TypeError: Значение не является JSON-объектом.
    """
    normalized = normalize_json_value(value)
    if isinstance(normalized, dict):
        return normalized

    msg = "Expected JSON object."
    raise TypeError(msg)


def clean_query_params(params: QueryParams | None) -> dict[str, str | int | float | bool]:
    """Удаляет `None` из query-параметров перед отправкой HTTP-запроса.

    Args:
        params: Query-параметры пользователя.

    Returns:
        Новый словарь параметров без значений `None`.
    """
    if params is None:
        return {}
    return {key: value for key, value in params.items() if value is not None}

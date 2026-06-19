"""Тесты общих JSON-типов."""

import pytest

from pyis74.types import clean_query_params, normalize_json_object, normalize_json_value


def test_normalize_json_value_accepts_nested_json() -> None:
    """Проверяет нормализацию вложенных JSON-значений."""
    payload = {
        "name": "relay",
        "active": True,
        "items": [{"id": 1}, None],
    }

    assert normalize_json_value(payload) == payload


def test_normalize_json_object_requires_object() -> None:
    """Проверяет, что JSON-объект не подменяется массивом."""
    with pytest.raises(TypeError, match="Expected JSON object"):
        normalize_json_object(["not", "object"])


def test_normalize_json_value_rejects_non_string_keys() -> None:
    """Проверяет, что ключи JSON-объекта должны быть строками."""
    with pytest.raises(TypeError, match="keys must be strings"):
        normalize_json_value({1: "bad"})


def test_clean_query_params_removes_none() -> None:
    """Проверяет очистку query-параметров от значений `None`."""
    assert clean_query_params({"page": 1, "missing": None, "enabled": True}) == {
        "enabled": True,
        "page": 1,
    }

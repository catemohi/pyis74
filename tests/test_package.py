"""Тесты базовой импортируемости пакета."""

import pyis74


def test_package_has_version() -> None:
    """Проверяет, что пакет экспортирует строковую версию."""
    assert isinstance(pyis74.__version__, str)
    assert pyis74.__version__


def test_package_exports_core_client() -> None:
    """Проверяет, что пакет экспортирует core-клиенты."""
    assert pyis74.IS74 is not None
    assert pyis74.IS74Async is not None

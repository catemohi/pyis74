"""Тесты базовой импортируемости пакета."""

import pyis74


def test_package_has_version() -> None:
    """Проверяет, что пакет экспортирует строковую версию."""
    assert isinstance(pyis74.__version__, str)
    assert pyis74.__version__

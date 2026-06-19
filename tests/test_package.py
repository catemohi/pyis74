"""Тесты базовой импортируемости пакета."""

from importlib.resources import files

import pyis74


def test_package_has_version() -> None:
    """Проверяет, что пакет экспортирует строковую версию."""
    assert isinstance(pyis74.__version__, str)
    assert pyis74.__version__


def test_package_exports_core_client() -> None:
    """Проверяет, что пакет экспортирует core-клиенты."""
    assert pyis74.IS74 is not None
    assert pyis74.IS74Async is not None
    assert pyis74.IS74ServiceUrls is not None


def test_package_exports_account_models() -> None:
    """Проверяет, что пакет экспортирует модели auth/account."""
    assert pyis74.MobileToken is not None
    assert pyis74.LkToken is not None
    assert pyis74.AccountSummary is not None
    assert pyis74.Balance is not None
    assert pyis74.IS74AuthRequiredError is not None


def test_package_exports_domofon_models() -> None:
    """Проверяет, что пакет экспортирует модели домофона."""
    assert pyis74.DomofonRelay is not None
    assert pyis74.DomofonOpenResult is not None


def test_package_exports_history_models() -> None:
    """Проверяет, что пакет экспортирует модели истории."""
    assert pyis74.HistoryEvent is not None
    assert pyis74.HistoryEventParams is not None
    assert pyis74.HistoryResponse is not None


def test_package_exports_camera_models() -> None:
    """Проверяет, что пакет экспортирует модели камер."""
    assert pyis74.Camera is not None
    assert pyis74.CameraGroup is not None
    assert pyis74.CameraGroupContent is not None
    assert pyis74.CameraLimitedInfo is not None
    assert pyis74.CameraStreams is not None
    assert pyis74.SelfCameraGroup is not None


def test_package_exports_high_level_models() -> None:
    """Проверяет, что пакет экспортирует high-level модели."""
    assert pyis74.DomofonRelayCameras is not None
    assert pyis74.HistoryEventKind is not None


def test_package_includes_py_typed_marker() -> None:
    """Проверяет наличие PEP 561 marker для downstream type checkers."""
    assert files("pyis74").joinpath("py.typed").is_file()

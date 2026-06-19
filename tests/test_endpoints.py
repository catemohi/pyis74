"""Тесты URL endpoint-слоя."""

import pytest

from pyis74.endpoints import BaseUrl, IS74ServiceUrls, is_absolute_url, join_url


def test_is_absolute_url_detects_http_urls() -> None:
    """Проверяет распознавание абсолютных HTTP URL."""
    assert is_absolute_url("https://api.is74.ru/auth/mobile")
    assert is_absolute_url("http://example.test/path")
    assert not is_absolute_url("/auth/mobile")


def test_join_url_joins_base_and_path() -> None:
    """Проверяет сборку абсолютного URL из base URL и пути."""
    assert join_url(BaseUrl.API, "/auth/mobile") == "https://api.is74.ru/auth/mobile"
    assert join_url("https://api.is74.ru/", "domofon/relays") == (
        "https://api.is74.ru/domofon/relays"
    )


def test_join_url_keeps_absolute_url() -> None:
    """Проверяет, что абсолютный URL не пересобирается."""
    url = "https://cams.is74.ru/api/self-cams-with-group"

    assert join_url(BaseUrl.API, url) == url


def test_service_urls_builds_urls_from_base_domain() -> None:
    """Проверяет сборку URL сервисов от корневого домена."""
    urls = IS74ServiceUrls(base_domain="example.test")

    assert urls.api == "https://api.example.test"
    assert urls.cams == "https://cams.example.test"
    assert urls.crm == "https://td-crm.example.test"
    assert urls.domofon_relays == "https://api.example.test/domofon/relays"
    assert urls.resolve_base_url(BaseUrl.CAMS) == "https://cams.example.test"


def test_service_urls_accepts_url_like_base_domain() -> None:
    """Проверяет нормализацию домена, переданного как URL."""
    urls = IS74ServiceUrls(base_domain="https://example.test/")

    assert urls.base_domain == "example.test"
    assert urls.api == "https://api.example.test"


def test_service_urls_rejects_invalid_values() -> None:
    """Проверяет базовую валидацию домена и схемы."""
    with pytest.raises(ValueError, match="base_domain"):
        IS74ServiceUrls(base_domain=" ")

    with pytest.raises(ValueError, match="scheme"):
        IS74ServiceUrls(base_domain="example.test", scheme="ftp")

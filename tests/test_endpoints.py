"""Тесты URL endpoint-слоя."""

from pyis74.endpoints import BaseUrl, is_absolute_url, join_url


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

"""Публичный пакет библиотеки pyis74.

Модуль содержит минимальные экспортируемые символы пакета. Основные клиенты и доменные
модули будут добавляться по мере реализации API IS74.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyis74")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ("__version__",)


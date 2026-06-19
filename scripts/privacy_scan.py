"""Проверка публичного репозитория на случайные приватные данные."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".rst",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

IGNORED_DIRS = {
    ".eggs",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}


@dataclass(frozen=True, slots=True)
class PatternRule:
    """Описывает одну проверку privacy scan."""

    name: str
    pattern: re.Pattern[str]


RULES = (
    PatternRule(
        "signed-camera-url",
        re.compile(r"(?:token=|token%3D)bearer-[A-Za-z0-9_-]{16,}", re.IGNORECASE),
    ),
    PatternRule("jwt-like-camera-token", re.compile(r"eyJ0eXAiOiJKV1Qi")),
    PatternRule(
        "snapshot-service-url",
        re.compile("td-" + r"snapshots\.is74\.ru", re.IGNORECASE),
    ),
    PatternRule("raw-cdn-camera-url", re.compile(r"cdn\.cams\.is74\.ru/.+token=", re.IGNORECASE)),
    PatternRule(
        "forbidden-internal-endpoint",
        re.compile("(?i)(" + "CRM_" + "SI" + "P_ACCOUNT|/api/si" + "p-account)"),
    ),
)


def iter_files(root: Path) -> Iterable[Path]:
    """Возвращает текстовые файлы репозитория, которые нужно проверить."""
    self_path = Path(__file__).resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.resolve() == self_path:
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def scan_file(path: Path) -> list[str]:
    """Проверяет один файл и возвращает найденные нарушения."""
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        findings.extend(
            f"{path}:{line_number}: {rule.name}" for rule in RULES if rule.pattern.search(line)
        )
    return findings


def main() -> int:
    """Запускает проверку privacy scan."""
    root = Path.cwd()
    findings: list[str] = []
    for path in iter_files(root):
        findings.extend(scan_file(path.relative_to(root)))

    if findings:
        print("privacy scan failed:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 1

    print("privacy scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

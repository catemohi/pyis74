# Правила участия в разработке

Спасибо за интерес к `pyis74`. Проект является публичной библиотекой для работы с API IS74,
поэтому изменения должны быть аккуратными, типизированными и проверяемыми.

## Требования

- Python `3.14+`.
- `uv` для установки зависимостей и запуска команд.
- Все проверки должны проходить локально и в CI.

## Локальный запуск

```bash
uv sync --all-groups
uv run ruff format
uv run ruff check
uv run mypy src tests
uv run pytest
uv build
```

## Стиль кода

Используется Google Python Style Guide:

https://google.github.io/styleguide/pyguide.html

Документация пишется на русском языке. Служебные слова Google-style docstring
`Args`, `Returns`, `Raises` не переводятся.

## Типизация

- Публичный API должен быть полностью типизирован.
- `Any` нельзя использовать как быстрый способ обойти типизацию.
- Сырые JSON-ответы должны быть локализованы на границе transport-слоя.
- Публичные методы должны возвращать модели или точные типы.

## Коммиты

Используем Conventional Commits:

```text
feat: add phone auth flow
fix: handle expired access token
docs: document camera streams
test: add relay fixtures
ci: add release workflow
```

## Релизы

Версия берется из git tag. Формат тега:

```text
v0.1.0
```

Публикация в PyPI выполняется GitHub Actions через Trusted Publishing.


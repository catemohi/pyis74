# Changelog

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).
Проект использует [Semantic Versioning](https://semver.org/lang/ru/). До версии
`1.0.0` публичный API может меняться в minor-релизах.

## [Unreleased]

### Documentation

- Добавлены ссылки на PyPI package, GitHub Releases и workflow status badges.

## [0.5.1] - 2026-06-20

### Changed

- Обновлены metadata пакета: автор и maintainer теперь указаны как `catemohi`.

## [0.5.0] - 2026-06-20

### Added

- Типизированный marker `py.typed` включен в пакет для downstream-проверок типов.
- Добавлена публичная документация методов в `docs/public-api.md`.
- Добавлен параметр `base_domain` в `IS74Async` и `IS74`; high-level методы и
  `ClientRequestOptions(base_url=BaseUrl.*)` теперь строят URL от домена клиента.
- Добавлены camera helpers для групп, limited-info, домофонных камер и stream URL.
- Добавлен history helper `get_events_until_limit()` для последовательного чтения
  нескольких страниц истории.
- Добавлены opt-in integration smoke tests, которые запускаются только при
  `IS74_RUN_INTEGRATION=yes`.
- Добавлена проверка приватных данных и token-подобных URL в CI.

### Changed

- Side-effect запросы открытия домофона выполняются без retry, чтобы HTTP-повтор не
  мог повторно отправить команду открытия.
- CI и release workflow запускают единый набор проверок: форматирование, lint, mypy,
  pytest, privacy scan, build и `twine check`.

### Documentation

- Документирована работа с подписанными camera stream/snapshot URL: такие ссылки
  считаются временными credential-like значениями и не должны сохраняться в публичные
  логи, fixtures или документацию.
- Добавлен блок благодарностей авторам открытых проектов, по которым сверялись
  известные endpoint и поведение API.

### Removed

- Из публичной документации и endpoint-карты убраны не входящие в релизный scope
  сценарии.

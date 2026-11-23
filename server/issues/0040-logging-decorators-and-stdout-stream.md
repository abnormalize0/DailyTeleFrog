---
id: 0040
title: Исправить порядок декораторов логирования, добавить functools.wraps и перевести логи на stdout/stderr
areas: [api, logging, tests]
date: 2026-11-23
---

# 0040. Исправить порядок декораторов логирования, добавить functools.wraps и перевести логи на stdout/stderr

## Проблема
При 500-ошибке не логируются HTTP-результат и время выполнения запроса, декораторы затирают метаданные функций, а файловый логгер без ротации небезопасен при многопроцессном запуске под Gunicorn.

*(Задача не дублирует `issues/0007-sensible-logging.md`: `0007` отвечает за содержимое логов и `MAX_CONTENT_LENGTH`, а `0040` — за механику декораторов и вывод логов.)*

## Как возникает и к чему приводит
- *Как возникает:*
  - во всех `src/api/routes/*.py` декораторы стоят в порядке `@log.safe_api` → `@log.log_request` → `@log.timer(...)`;
  - в `src/log.py` декораторы `timer`, `log_request` и `safe_api` копируют только `wrapper.__name__ = func.__name__` вместо `@functools.wraps(func)`;
  - в `start.py::standard_configuration` используется `logging.FileHandler` без ротации.
- *Негативный эффект:*
  - при необработанном исключении `@log.safe_api` перехватывает его снаружи, поэтому `Result: 500 ...` и `Processed request in ...` не попадают в лог;
  - теряются `__doc__`, `__annotations__` и сигнатура декорируемых обработчиков;
  - `FileHandler` растёт бесконечно и при нескольких воркерах Gunicorn (см. `0036`) параллельная запись/ротация файла приводит к потере или повреждению логов.

## Желаемое поведение
- Переставить `@log.safe_api` внутрь `@log.log_request` и `@log.timer(...)` во всех файлах `src/api/routes/*.py` и зафиксировать порядок декораторов в докстринге `src/api/api.py` (и в скиле `dailytelefrog-new-api-method`, если там указан порядок).
- Использовать `@functools.wraps(func)` в `timer`, `log_request` и `safe_api`.
- Перевести логирование приложения на `logging.StreamHandler` (`stdout`/`stderr`) вместо `FileHandler` во всех режимах (в продакшне ротацией управляет Docker); в `tests/conftest.py` перенаправлять вывод процесса тестового сервера в файл внутри `WORKDIR`, а в `tests/helpers.py::read_server_log()` читать этот файл (сохраняя копирование в `test_logs/` в `Makefile`).

## Готово, когда
- При 500 в лог попадают и traceback, и `Result: 500`, и время выполнения (проверено unit-тестом).
- Декораторы в `src/log.py` сохраняют `__doc__` и сигнатуру (`functools.wraps`).
- `FileHandler` заменён на `StreamHandler`, а e2e-тесты чтения логов (`read_server_log`) работают с выводом процесса.
- Прогнан `black` и полный `make test` проходит.

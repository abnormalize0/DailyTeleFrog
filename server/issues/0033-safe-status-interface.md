---
id: 0033
title: Сделать интерфейс Status безопасным через фабрики Status.ok / Status.error и валидацию в __init__
areas: [api, db, tests]
date: 2026-11-23
---

# 0033. Сделать интерфейс Status безопасным через фабрики Status.ok / Status.error и валидацию в __init__

## Проблема
Конструктор и поля `Status` в `src/request_status.py` допускают создание невалидных объектов без немедленной ошибки: параметр `is_error: StatusType` назван как `bool`, а отсутствие `error_type` при `StatusType.ERROR` (или передача `bool` / лишних полей при `StatusType.OK`) обнаруживается только позже в виде `AttributeError` или молча игнорируется.

## Как возникает и к чему приводит
- *Как возникает:*
  - параметр `Status.__init__(self, is_error: StatusType, ...)` по имени выглядит как булев флаг, хотя ожидает `StatusType`;
  - в `__init__` нет проверки типов и инвариантов: `Status(StatusType.ERROR)` без `error_type` успешно создаётся и падает с `AttributeError` позже при обращении к `http_code` / `problem()`, `Status(True)` падает на `self._status_type.value` внутри свойства `is_error`, а `Status(StatusType.OK, error_type=...)` молча отбрасывает переданные поля;
  - в классе `Status` объявлены лишние классовые атрибуты `_status_type = None`, `_error_type = None`, `_msg = None`, `_errors = None`, а `is_error` вычисляется через `not bool(self._status_type.value)` вместо явного сравнения с `StatusType.ERROR`.
- *Негативный эффект:*
  - ошибка программиста при создании `Status` проявляется не в месте вызова, а далеко выше по стеку (при сериализации ответа) или маскируется;
  - имя параметра `is_error` провоцирует передавать `bool` вместо `StatusType`, а многословный `Status(StatusType.OK)` / `Status(StatusType.ERROR, error_type=...)` засоряет весь код.

## Желаемое поведение
- В `Status` добавлены фабричные методы `Status.ok()` и `Status.error(error_type: ErrorType, msg: str, errors: list | None = None)`, делающие невалидное состояние невозможным на уровне сигнатуры.
- Параметр `is_error` в `Status.__init__` переименован в `status_type`, а сам `__init__` строго валидирует инварианты (при нарушении сразу выбрасывается `TypeError` или `ValueError`):
  - `status_type` обязан быть экземпляром `StatusType`;
  - при `StatusType.ERROR` обязателен `error_type` типа `ErrorType`;
  - при `StatusType.OK` передача `error_type`, `msg` или `errors` запрещена.
- Свойство `is_error` сравнивает `self._status_type == StatusType.ERROR` (без `not bool(...value)`), лишние атрибуты уровня класса `Status` удалены.
- Все вызовы `Status(...)` в `src/` и тестах переведены на `Status.ok()` / `Status.error(...)` (и `request_status.not_found(...)`, где уместно).
- Добавлены unit-тесты на фабрики и на все невалидные комбинации аргументов `Status(...)`.

## Готово, когда
- `Status.ok()` и `Status.error(...)` реализованы, все вызовы в `src/` и тестах переведены на них.
- `Status.__init__` принимает `status_type: StatusType` и сразу валидирует все инварианты (попытка создать `Status(StatusType.ERROR)` без `error_type`, `Status(True)` или `Status(StatusType.OK, error_type=...)` падает в конструкторе).
- Есть unit-тесты на фабрики и невалидные вызовы `Status`, полный `make test` проходит.

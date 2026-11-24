---
id: 0011
title: Разделение 400 и 422, единый формат errors (pointer/detail) и декларативные перечисления
status: accepted
implementation: done
areas: [api, articles, comments, users, tests]
files: [server/src/request_status.py, server/src/api/errors.py, server/src/api/shared.py, server/src/api/api_info.py, server/src/api/routes/, server/src/db/, server/tests/helpers.py]
date: 2026-11-24
updated: 2026-11-24
superseded_by:
supersedes:
---

# 0011. Разделение 400 и 422, единый формат errors (pointer/detail) и декларативные перечисления

Уточняет и обновляет таблицу ошибок и формат поля `errors` из [0004](0004-rest-api.md).

## Правило для агента
- Синтаксически некорректное JSON-тело (битый JSON, не-объект, пустое тело, неверный `Content-Type`) возвращает `400 /errors/bad-request` (`ErrorType.BadRequest`) **без** `errors`.
- Любая семантическая ошибка валидации параметров или значений (включая императивные проверки в роутах и `src/db/`) возвращает `422 /errors/validation` (`ErrorType.InvalidParameters`) с непустым массивом `errors: [{"pointer", "detail"}]`.
- Формат `pointer`: `"/<имя>"` для параметров body и query; `""` для ошибки уровня всего запроса.
- Список допустимых значений скалярного поля задаётся ключом `"allowed"` в `api_info.py`, а не ручной проверкой в роуте.

## Контекст
После перехода на Problem Details ([0004](0004-rest-api.md)) в API оставались три расхождения:
1. Битый JSON, не-объект и ошибки значений параметров возвращали один код `400`, а методы без обязательных полей (`PATCH /users/me`) принимали битое тело как `{}` и отвечали `204` или `401`.
2. Ошибки валидации из `check_structure` и `article.add_tags` отдавали `errors` с ключами `name`/`reason`, а императивные проверки (`sort_column`, `sort_direction`, `parent` в комментариях, XOR `username`/`email` в `/auth/login`, несуществующий пользователь в подписках/блокировках) — вообще без `errors`.
3. `check_structure` не поддерживал перечисления для скалярных полей, из-за чего `sort_column` и `sort_direction` проверялись вручную и не попадали в `OPTIONS /articles`.

## Решение

### Разделение 400 и 422

| `ErrorType` | `type` | Код | Когда |
|---|---|---|---|
| `BadRequest` | `/errors/bad-request` | 400 | Синтаксически некорректный запрос: битый JSON, тело не JSON-объект, пустое тело, неверный `Content-Type` |
| `InvalidParameters` | `/errors/validation` | 422 | Семантические ошибки валидации: тип, длина, шаблон, допустимые значения (`allowed`), дубликаты тегов, ссылка на несуществующий объект в теле, XOR `username`/`email` |

### Единый формат `errors` и инвариант `Status`
- Каждый ответ `422 /errors/validation` обязан содержать непустой список `errors`, где каждый элемент имеет вид `{"pointer": "<строка>", "detail": "<непустая строка>"}`.
- `pointer` имеет вид `"/<имя>"` как для JSON-тела, так и для query-параметров (`"/title"`, `"/sort_column"`, `"/tags"`, `"/parent"`, `"/sub-users"`, `"/blocked-users"`). Для ошибки уровня всего запроса используется корневой указатель `""`.
- Для взаимоисключающей пары `username`/`email` в `POST /auth/login` возвращаются два элемента: на `"/username"` и `"/email"`.
- Инвариант проверяется программно в `src/request_status.py::Status.__init__`: `InvalidParameters` без непустого корректного списка `errors` бросает `TypeError`/`ValueError`, а любое другое значение `ErrorType` (включая `BadRequest`) с `errors is not None` бросает `ValueError`.

### Декларативные перечисления и проверка тела
- `shared.read_body` проверяет `isinstance(body, dict)` до `check_structure` и при любом отклонении сразу возвращает `400 /errors/bad-request` (`"Request body must be a JSON object"`) — одинаково для всех методов с JSON-телом, включая `PATCH /users/me`. Валидный `{}` с `Content-Type: application/json` в `PATCH /users/me` по-прежнему допустим.
- `shared.check_structure` поддерживает `"allowed": [...]` для скалярных полей (`detail`: `"must be one of {allowed}"`). `sort_column` и `sort_direction` перенесены в `api_info.articles_get`.

## Почему
- **400 vs 422 по RFC 9110:** клиент отличает синтаксически битый запрос от ошибок заполнения полей по HTTP-коду, не разбирая текст `detail`.
- **`pointer`/`detail` по RFC 9457:** стандартные имена полей и единый `"/<имя>"` для body и query избавляют клиентский обработчик от двух форматов.
- **Проверка инварианта в `Status.__init__`:** гарантирует на уровне типа, что ни один метод или слой БД не вернёт `422` без `errors` или со старыми ключами `name`/`reason`.

## Последствия
Изменения, которые нужно учесть на стороне клиента:
- Ошибки валидации теперь приходят с HTTP-кодом **422** (а не 400); код **400** (`/errors/bad-request`) означает битый JSON / не-объект / неверный `Content-Type`.
- В массиве `errors` ключи заменены с `name`/`reason` на **`pointer`/`detail`** (например `{"pointer": "/title", "detail": "is required"}`); массив `errors` теперь присутствует в **каждом** ответе `422 /errors/validation`.
- `OPTIONS /articles` теперь содержит поле `allowed` для `sort_column` и `sort_direction`.
- `PATCH /users/me` с невалидным JSON-телом или неверным `Content-Type` возвращает `400` вместо прежнего молчаливого `204`/`401`.

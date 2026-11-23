---
id: 0029
title: Разделить 400 и 422, перейти на pointer/detail и унифицировать валидацию
areas: [api, articles, comments, users, tests]
date: 2026-11-23
---

# 0029. Разделить 400 и 422, перейти на pointer/detail и унифицировать валидацию

## Проблема
В API действуют два механизма валидации (`api_info.py` и ручные проверки в роутах/БД), синтаксические ошибки тела (битый JSON) и семантические ошибки значений смешаны под одним кодом `400`, а формат `errors` непоследователен (`name`/`reason` только у части `400`, у остальных `errors` отсутствует).

## Как возникает и к чему приводит
- *Как возникает:*
  - `src/api/shared.py::check_structure` не поддерживает список допустимых значений (`allowed`) для скалярных полей, поэтому `sort_column` и `sort_direction` проверяются вручную в `src/api/routes/articles.py` и не попадают в `OPTIONS /articles`;
  - императивные проверки в роутах и БД (`sort_column`, `sort_direction`, `parent` в `src/db/comment.py::add`, XOR `username`/`email` в `POST /auth/login`, несуществующий пользователь в подписках) возвращают `400` без `errors`, тогда как `check_structure` и `article.add_tags` отдают `errors` с ключами `name`/`reason` (вместо `pointer`/`detail` по примеру RFC 9457);
  - ошибки разбора тела (битый JSON / не-объект, см. `issues/0010-reject-invalid-json-body.md`) и ошибки значений полей используют один и тот же код `400`, хотя по RFC 9110 это разные классы ошибок (`400 Bad Request` против `422 Unprocessable Content`).
- *Негативный эффект:*
  - клиент не видит часть допустимых значений в `OPTIONS` и вынужден хардкодить их отдельно;
  - клиентский обработчик ошибок получает два разных формата ответа для ошибок валидации и не отличает синтаксически битый запрос от неверных значений полей по HTTP-коду.

## Желаемое поведение
- **Разделение `400` и `422` по RFC 9110:**
  - `400 Bad Request` (отдельный `ErrorType`, например `BadRequest` → `/errors/bad-request`) — для синтаксически некорректного запроса (битый JSON, не-объект, неверный `Content-Type`, см. `issues/0010-reject-invalid-json-body.md`);
  - `422 Unprocessable Content` (`ErrorType.InvalidParameters` → `/errors/validation`) — для всех семантических ошибок валидации параметров и значений (тип, длина, шаблон, допустимые значения, дубликаты тегов, несуществующий `parent`, XOR `username`/`email` и др.).
- **Единый формат `errors` по RFC 9457 (`pointer` / `detail`) — всегда присутствует в `422 /errors/validation`:**
  - каждый элемент `errors` содержит `pointer` и `detail` (вместо `name` и `reason`), например `{"pointer": "/title", "detail": "must not be blank"}`;
  - для XOR `username`/`email` в `POST /auth/login` возвращаются два элемента (на `/username` и `/email`); для ошибки уровня всего запроса — корневой указатель `""`.
- **Декларативные перечисления в `api_info.py`:** в `check_structure` поддержано ограничение `allowed` для скалярных полей; `sort_column` и `sort_direction` перенесены в `api_info.articles_get` и видны в `OPTIONS /articles`, ручные проверки в `routes/articles.py` удалены.
- Изменение контракта (`400` vs `422` и `pointer`/`detail`) фиксируется новой записью в `decisions/` (пересматривающей соответствующую часть `decisions/0004-rest-api.md`), с явным перечнем изменений для клиента.

## Готово, когда
- Оформлена новая запись в `decisions/` с разделением `400`/`422` и форматом `errors: [{"pointer", "detail"}]`.
- Битый JSON / не-объект возвращает `400`, а все ошибки валидации (декларативные и императивные) возвращают `422 /errors/validation` с массивом `errors: [{"pointer", "detail"}]`.
- `sort_column` и `sort_direction` валидируются декларативно через `api_info.articles_get` и отдаются в `OPTIONS /articles`.
- Обновлены `src/request_status.py`, `src/api/shared.py`, `src/api/api_info.py`, `src/api/routes/`, `src/db/`, `tests/helpers.py`, все unit- и e2e-тесты; полный `make test` проходит.

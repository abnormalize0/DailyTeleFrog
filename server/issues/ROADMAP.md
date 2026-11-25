# Порядок решения задач бэкенда

Рекомендуемый порядок выполнения открытых задач из `issues/` (`0003`–`0044`).

**Принцип сортировки:** сначала ускорение тестов, расчистка мёртвого кода и базовые контракты слоёв и ошибок, чтобы не переписывать код и тесты дважды; затем валидация входных данных в уже едином формате; далее критичные баги корректности, гонок и безопасности; затем схема БД и производительность; после этого — улучшения API-контракта (требующие синхронизации с клиентом), продакшн-инфраструктура и в конце — новые продуктовые фичи.

---

## Этап 0. Ускорение работы и синхронизация правил

Сразу снимает противоречия в документации, убирает лишнюю паузу при прогоне `make test` и чистит файлы перед работой с логированием и WSGI.

1. ~~[0034](done/0034-sync-docs-decisions-and-skills.md) — закрыть уже выполненную задачу `0004` (перенести в `issues/done/`), перевести ADR `0009` в `accepted`, исправить правило именования моделей в скиле БД.~~ *(выполнено)*
2. ~~[0041](done/0041-portable-tests-and-mysql-healthcheck.md) — отвязать тесты от `/app` и `../.env`, заменить `sleep 30s` в `Makefile` на проверку готовности MySQL (экономит время на каждом прогоне `make test` во всех последующих задачах и открывает локальный запуск).~~ *(выполнено)*
3. ~~[0028](done/0028-remove-sqlite-legacy-dead-code.md) — удалить мёртвый SQLite-код в `start.py` и `src/config.py`, убрать пустой `db_api.log`, обновить `README.md` (чистит файлы до задач по логированию и WSGI).~~ *(выполнено)*

---

## Этап 1. Базовые контракты слоёв и ошибок

Выполняется до массовых правок в `src/db/` и валидации, чтобы не переделывать интерфейсы и проверки дважды.

4. ~~[0033](done/0033-safe-status-interface.md) — сделать интерфейс `Status` безопасным через фабрики `Status.ok` / `Status.error` и валидацию в `__init__`.~~ *(выполнено)*
5. ~~[0031](done/0031-decouple-db-from-flask-and-cleanup-proxies.md) — отвязать `src/db/` и `request_status.py` от Flask/HTTP и убрать однострочные прокси в `backend.py`.~~ *(выполнено)*
6. ~~[0030](done/0030-flask-json-responses-and-options-sync.md) — перевести JSON-ответы API на нативный Flask и добавить проверку синхронности `OPTIONS`.~~ *(выполнено)*
7. ~~[0029](done/0029-unify-validation-422-and-pointer-detail.md) — разделить `400` и `422`, перейти на `pointer`/`detail` и унифицировать валидацию *(ключевая точка: все задачи этапа 2 пишутся уже под этот формат)*.~~ *(выполнено)*

---

## Этап 2. Валидация входных данных

Реализуется сразу в едином формате ошибок и валидации из [0029](done/0029-unify-validation-422-and-pointer-detail.md).

8. ~~[0016](done/0016-mutable-default-in-type-defaults.md) — убрать разделяемый изменяемый список в `api_info.type_defaults`.~~ *(выполнено)*
9. ~~[0010](done/0010-reject-invalid-json-body.md) — отклонять некорректное JSON-тело запроса во всех методах.~~ *(выполнено в рамках [0029](done/0029-unify-validation-422-and-pointer-detail.md))*
10. ~~[0014](done/0014-reject-unknown-request-fields.md) — отклонять неизвестные поля в JSON-теле и query-строке запросов.~~ *(выполнено)*
11. ~~[0018](done/0018-reject-nul-and-control-chars.md) — запретить NUL-символы во всех входных данных и управляющие символы в однострочных полях.~~ *(выполнено)*
12. ~~[0011](done/0011-articles-indexes-validation.md) — ограничить значения и длину параметра `indexes` в `GET /articles`.~~ *(выполнено)*
13. ~~[0020](done/0020-sync-article-data-tags-field.md) — синхронизировать поле `tags` в `GET /articles/{id}/data` между `api_info` и `backend`.~~ *(выполнено)*
14. ~~[0042](done/0042-reject-duplicate-scalar-query-params.md) — отклонять дублирующиеся скалярные query-параметры в `shared.read_query`.~~ *(выполнено)*
15. ~~[0043](done/0043-deduplicate-route-docstrings-validation-rules.md) — убрать дублирование правил валидации `api_info` в докстрингах роутов.~~ *(выполнено)*

---

## Этап 3. Критические баги корректности, гонок и безопасности

Задача [0008](done/0008-case-insensitive-comparisons.md) идёт первой в этапе, так как устраняет расхождение регистра между MySQL и Python, от которого зависят проверки в `0009`, `0012`, `0015` и `0021`.

16. ~~[0008](done/0008-case-insensitive-comparisons.md) — устранить расхождение сравнения строк (регистра) между MySQL и Python.~~ *(выполнено)*
17. [0021](0021-user-lookup-ambiguous-args.md) — запретить одновременную передачу `username` и `email` в `is_user_not_exist` и `check_password`.
18. [0012](0012-auth-revocation-race.md) — исключить гонку отзыва токенов и удаления аккаунта против `login` и `refresh`.
19. [0017](0017-login-timing-attack.md) — выровнять время ответа `POST /auth/login` при несуществующем пользователе (защита от timing-атаки).
20. [0006](0006-account-security.md) — усилить безопасность аккаунтов (защита refresh-токенов, отзыв чужого токена в `POST /auth/logout`, rate limiting).
21. [0009](0009-subscription-blacklist-race.md) — исключить одновременную подписку и блокировку при параллельных запросах.
22. [0019](0019-deleted-author-feed-filter-leak.md) — скрыть авторство удалённых аккаунтов в фильтрах ленты `GET /articles`.
23. [0013](0013-comment-tree-iterative.md) — убрать рекурсию (`500 RecursionError`), `O(N²)` и недетерминированный порядок при сборке дерева комментариев *(подготовка к [0026](0026-enrich-article-comments-tree.md))*.
24. [0044](0044-articles-filter-lists-max-items.md) — ограничить длину списочных фильтров в `GET /articles` (`max_items`), чтобы исключить `500` от лимита таблиц MySQL при большом числе `include_tags`.

---

## Этап 4. Схема БД и производительность

Сначала переименовывается таблица и унифицируются запросы существования, затем оптимизируются выборки и агрегации.

25. [0035](0035-rename-article-preview-table-plural.md) — переименовать таблицу `article_preview` в `article_previews` *(до рефакторинга запросов к статьям)*.
26. [0032](0032-unify-db-single-query-existence.md) — унифицировать проверку существования в `src/db/` на одиночный `SELECT`.
27. [0022](0022-avoid-full-row-fetches.md) — убрать лишние полные вычитки `Article`/`User` и перевести сборку ленты на пакетные запросы.
28. [0023](0023-consistent-reaction-counts.md) — считать лайки, дизлайки и рейтинг согласованно без повторных `COUNT(*)`.
29. [0024](0024-sql-pagination-and-tie-breaker.md) — перенести пагинацию ленты в SQL (`LIMIT`/`OFFSET`) и добавить вторичный ключ сортировки *(после [0008](done/0008-case-insensitive-comparisons.md) и [0011](0011-articles-indexes-validation.md))*.
30. [0025](0025-avoid-triple-body-serialization.md) — убрать повторную JSON-сериализацию `body` и `preview` при публикации статьи.
31. [0027](0027-optimize-user-get-rating.md) — перевести расчёт `user.get_rating` с выгрузки ID и `IN (...)` на SQL `JOIN` + `COUNT`.

---

## Этап 5. Улучшение API-контракта (требует синхронизации с клиентом)

32. [0026](0026-enrich-article-comments-tree.md) — отдавать метаданные и реакции комментариев сразу в `GET /articles/{id}` *(после [0013](0013-comment-tree-iterative.md) и [0023](0023-consistent-reaction-counts.md))*.
33. [0015](0015-subscriptions-blacklists-rest-endpoints.md) — вынести подписки и блокировки в отдельные REST-эндпоинты с поддержкой снятия *(после [0008](done/0008-case-insensitive-comparisons.md) и [0009](0009-subscription-blacklist-race.md))*.

---

## Этап 6. Продакшн-инфраструктура и логирование

Сначала готовятся инициализация пула БД, CORS и потоковое логирование, затем сервер переводится на Gunicorn, и в конце фиксируются зависимости и очищаются Docker-образы.

34. [0037](0037-sqlalchemy-pool-and-engine-init.md) — явная `init_db(url)` на старте + `pool_pre_ping=True`, `pool_recycle=3600` *(готовит `shared.py` к WSGI-фабрике)*.
35. [0039](0039-restrict-cors-origins.md) — ограничить CORS через `CORS_ORIGINS` (fail-closed).
36. [0040](0040-logging-decorators-and-stdout-stream.md) — переставить `@log.safe_api` внутрь, добавить `@functools.wraps`, перевести логи на `StreamHandler` (`stdout`/`stderr`) *(готовит логирование к многопроцессному Gunicorn и [0007](0007-sensible-logging.md))*.
37. [0007](0007-sensible-logging.md) — писать в лог только операции и полезные данные (без 16 МБ тел) + `MAX_CONTENT_LENGTH` *(после [0040](0040-logging-decorators-and-stdout-stream.md))*.
38. [0036](0036-gunicorn-wsgi-server.md) — перевести продакшн и e2e-тесты на WSGI-сервер Gunicorn *(опирается на `0037`, `0039`, `0040`, `0041`)*.
39. [0038](0038-docker-secrets-and-pinned-requirements.md) — убрать секреты из Docker-образов, добавить `.dockerignore`, зафиксировать версии и разделить `requirements.txt` / `requirements-dev.txt` с multi-stage сборкой *(после `0036`, чтобы `gunicorn` сразу зафиксировать в `requirements.txt`, и после `0041`, чтобы тесты не искали `/app/.env`)*.

---

## Этап 7. Новые продуктовые фичи

40. [0005](0005-article-drafts.md) — добавить черновики статей.
41. [0003](0003-communities.md) — добавить сообщества.

---

> **Памятка:** задача [0004](done/0004-api-atomicity.md) выполнена в коде и перенесена в `issues/done/` в рамках [0034](done/0034-sync-docs-decisions-and-skills.md).

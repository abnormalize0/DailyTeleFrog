---
id: 0044
title: Ограничить длину списочных фильтров в GET /articles (max_items)
areas: [api, articles, db, tests]
date: 2026-11-25
---

# 0044. Ограничить длину списочных фильтров в GET /articles (max_items)

## Проблема
В `src/api/api_info.py::articles_get` у списочных фильтров `include_tags`, `exclude_tags`, `include_authors`, `exclude_authors` отсутствует ограничение `max_items`. Для `include_tags` каждый уникальный тег добавляет отдельный коррелированный `EXISTS` по таблице `article_tags` (`src/db/article.py::pages_get`), а в MySQL 8 действует жёсткий лимит в 61 таблицу на join-блок (`ER_TOO_MANY_TABLES`, код 1116).

## Как возникает и к чему приводит
- *Как возникает:* клиент передаёт в query-строке `GET /articles` более 60 уникальных значений `include_tags`. MySQL разворачивает подзапросы `EXISTS` в join-блок, превышая ограничение в 61 таблицу.
- *Негативный эффект:* вместо клиентской ошибки валидации `422` сервер падает с необработанной ошибкой БД и возвращает `500 Internal Server Error`, что нарушает контракт `AGENTS.md`. Кроме того, остальные списочные фильтры (`exclude_tags`, `include_authors`, `exclude_authors`) также не ограничены по числу элементов.

## Желаемое поведение
- В `src/api/api_info.py::articles_get` для `include_tags`, `exclude_tags`, `include_authors`, `exclude_authors` задано разумное ограничение `max_items` с запасом ниже лимита MySQL в 61 таблицу (например, 20–50 элементов).
- Запрос с числом элементов сверх `max_items` отклоняется на уровне схемы с `422 /errors/validation` и соответствующим `pointer`/`detail`.
- Запрос с максимальным допустимым числом элементов `include_tags` гарантированно не падает с `500`.

## Готово, когда
- В `api_info.articles_get` задано `max_items` для `include_tags`, `exclude_tags`, `include_authors`, `exclude_authors` (отдаётся в `OPTIONS /articles`).
- Превышение лимита возвращает `422 /errors/validation`, а запрос на границе лимита обрабатывается успешно (не `500`).
- Добавлены unit- и/или e2e-тесты на лимит и граничное значение, полный `make test` проходит.

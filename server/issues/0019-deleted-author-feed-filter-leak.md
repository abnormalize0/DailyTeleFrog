---
id: 0019
title: Скрыть авторство удалённых аккаунтов в фильтрах ленты GET /articles
areas: [api, db, articles, users, tests]
date: 2026-11-23
---

# 0019. Скрыть авторство удалённых аккаунтов в фильтрах ленты GET /articles

## Проблема
После мягкого удаления аккаунта `author_preview` в статьях скрывает его данные (`{"is_deleted": true}`), но фильтры `include_authors` и `exclude_authors` в `GET /articles` по-прежнему сопоставляют статьи по `Article.author_username` без проверки `User.is_deleted`. Это позволяет точно узнать, какие статьи написал удалённый пользователь.

## Как возникает и к чему приводит
- *Как возникает:* в `src/db/article.py::pages_get` фильтры `include_authors` и `exclude_authors` проверяют напрямую `scheme.Article.author_username.in_(...)` и `notin_(...)`, не отсеивая удалённые аккаунты (`scheme.User.is_deleted == True`).
- *Негативный эффект:*
  - запрос `GET /articles?indexes=0&include_authors=<deleted_username>` возвращает все статьи удалённого пользователя, полностью раскрывая его авторство;
  - запрос `GET /articles?indexes=0&exclude_authors=<deleted_username>` скрывает именно его статьи — сравнив выдачу с обычной лентой, можно так же однозначно связать статьи с удалённым аккаунтом, что противоречит `decisions/0005-soft-delete.md`.

## Желаемое поведение
- В `src/db/article.py::pages_get` пользовательские фильтры `include_authors` и `exclude_authors` трактуют удалённый аккаунт так же, как несуществующий:
  - `include_authors` со значением удалённого `username` не находит его статьи (возвращает пустую выдачу, если не указаны другие активные авторы);
  - `exclude_authors` со значением удалённого `username` не исключает его статьи из ленты.
- В обычной ленте без этих фильтров статьи удалённого аккаунта по-прежнему отображаются с `author_preview: {"is_deleted": true}` (как требует `decisions/0005-soft-delete.md`).

## Готово, когда
- `GET /articles` с `include_authors=<deleted_username>` возвращает пустой список, а с `exclude_authors=<deleted_username>` не скрывает статьи удалённого автора.
- Добавлены регрессионные unit- и e2e-тесты, полный `make test` проходит.

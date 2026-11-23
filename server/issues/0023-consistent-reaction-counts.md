---
id: 0023
title: Считать лайки, дизлайки и рейтинг согласованно без повторных COUNT(*)
areas: [db, articles, comments, tests]
date: 2026-11-23
---

# 0023. Считать лайки, дизлайки и рейтинг согласованно без повторных COUNT(*)

## Проблема
При чтении статьи, её данных, превью и данных комментария счётчики `likes`, `dislikes` и `rating` запрашиваются раздельными `COUNT(*)`, причём `rating` пересчитывает оба счётчика заново. Это удваивает число запросов подсчёта реакций и под уровнем изоляции `READ COMMITTED` допускает противоречивый ответ, где `likes - dislikes != rating`.

## Как возникает и к чему приводит
- *Как возникает:* `backend.get_article`, `backend.get_article_preview`, `backend.get_article_data` и `backend.get_comment_data` вызывают `likes_count`, `dislikes_count` и `rating` по отдельности. Внутри `article.rating` (`src/db/article.py`) и `comment.rating` (`src/db/comment.py`) повторно вызываются `_count_likes` и `_count_dislikes` — итого 4 отдельных `SELECT COUNT(*)` вместо одного. Поскольку сервер работает в режиме `READ COMMITTED` (`src/api/shared.py::get_session`, см. `decisions/0009-api-atomicity.md`), каждый `SELECT` видит свой собственный снимок MVCC.
- *Негативный эффект:*
  - выполняются лишние `COUNT(*)` по таблицам реакций в `GET /articles/{id}`, `GET /articles/{id}/data`, `GET /comments/{id}` и `GET /articles`;
  - если между вызовами `likes_count`/`dislikes_count` и `rating` другой пользователь поставил, снял или переключил реакцию, клиент в одном JSON-ответе получает противоречивые числа (например, `likes: 5, dislikes: 1, rating: 5`, либо при переключении лайка на дизлайк оба счётчика отражают разные моменты времени).

## Желаемое поведение
- Для одиночных чтений (`get_article`, `get_article_data`, `get_comment_data`) счётчики лайков и дизлайков статьи или комментария читаются за один SQL-запрос с двумя скалярными подзапросами `COUNT(*)` (единый MVCC-снимок даже под `READ COMMITTED`), а `rating` всегда вычисляется как `likes - dislikes` из этих же значений без повторных обращений к БД.
- Если в `GET /articles/{id}/data` или `GET /comments/{id}` запрошено только `likes` или только `dislikes`, лишний подзапрос не выполняется; при запросе `rating` или любой комбинации `likes`/`dislikes`/`rating` числа берутся согласованно из одного SQL-запроса.
- В пакетной сборке ленты (см. `issues/0022-avoid-full-row-fetches.md`) `rating` также вычисляется из уже собранных `likes` и `dislikes` без повторных `COUNT(*)`.
- В каждом JSON-ответе гарантируется инвариант `rating == likes - dislikes`; схема и правило `decisions/0002-db-write-pattern-and-indexes.md` (подсчёт на лету без кэша) сохраняются без изменений.

## Готово, когда
- `get_article`, `get_article_preview`, `get_article_data` и `get_comment_data` не выполняют повторных `COUNT(*)` для вычисления `rating`.
- При совместном чтении `likes`/`dislikes`/`rating` данные читаются согласованно в одном SQL-запросе, и в ответе всегда выполняется `rating == likes - dislikes`.
- Добавлены unit-тесты (проверка количества SQL-запросов и согласованности значений), полный `make test` проходит.

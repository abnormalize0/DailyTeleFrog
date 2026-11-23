---
id: 0022
title: Убрать лишние полные вычитки Article/User и перевести сборку ленты на пакетные запросы
areas: [db, articles, users, tests]
date: 2026-11-23
---

# 0022. Убрать лишние полные вычитки Article/User и перевести сборку ленты на пакетные запросы

## Проблема
Проверки существования `article.is_article_not_exist` и `user.is_user_not_exist`, а также сборка превью и метаданных статьи/пользователя вычитывают из MySQL целиком ORM-строки `Article` (включая `MEDIUMTEXT body` до 16 МБ) и `User` (включая `TEXT description` и хеш пароля) по много раз в рамках одного HTTP-запроса, а лента `GET /articles` собирает превью статей по одной (N+1 по статьям).

## Как возникает и к чему приводит
- *Как возникает:*
  - `src/db/article.py::is_article_not_exist` делает `session.query(scheme.Article)` вместо `scheme.Article.id` (в отличие от `comment.is_comment_not_exist`, где уже выбирается только `Comment.id`). В `backend.get_article_preview` и `backend.get_article_data` каждая вспомогательная функция (`article.get`, `preview`, `likes_count`, `dislikes_count`, `rating`, `comments_count`, `tags`, `is_liked`, `is_disliked`) заново вызывает `is_article_not_exist` — до 9–10 полных `SELECT` строки `Article` с `body` на одну статью.
  - Кроме того, `backend.get_article_preview` и `backend.get_article_data` (для `creation_date`) вызывают `article.get`, который тоже загружает `Article.body`, хотя ни ленте, ни `/articles/{id}/data` тело статьи не нужно.
  - В `backend.pages_get` превью собираются в цикле по каждой статье отдельно (`get_article_preview`), умножая число SQL-запросов на количество статей на странице (до 50 статей при 10 страницах).
  - Аналогично `src/db/user.py::is_user_not_exist` делает `session.query(scheme.User)` вместо `scheme.User.username`. В `backend.get_user_data` при запросе всех 11 полей профиля проверка вызывается до 11 раз подряд, плюс отдельный `SELECT` на каждую скалярную колонку `User` (22+ запроса на один `GET /users/me`).
- *Негативный эффект:*
  - одна страница ленты (`GET /articles?indexes=0`, 5 статей) выполняет ~100 SQL-запросов и до ~50 раз перегоняет по сети из MySQL полное `Article.body` (до 800 МБ трафика при крупных статьях), хотя лента `body` не использует;
  - `GET /users/me` с полным набором полей делает 22+ запросов к MySQL и 11 раз тянет всю строку `User`;
  - растёт задержка ответа и нагрузка на БД и память сервера даже при небольшом числе пользователей.

## Желаемое поведение
- `article.is_article_not_exist` запрашивает только `scheme.Article.id`, а `user.is_user_not_exist` — только `scheme.User.username`.
- `backend.get_article_preview` и `backend.get_article_data` не загружают `Article.body` (читают только нужные метаданные статьи: `title`, `creation_date`, `author_username`).
- Сборка страниц ленты (`GET /articles` / `backend.pages_get`) переведена на пакетные запросы по списку `article_ids` (`WHERE article_id IN (...)`, `GROUP BY`): метаданные статей без `body`, `preview_content`, авторы (`author_preview`), теги, счётчики комментариев и реакций (`likes`, `dislikes`, `is_liked`, `is_disliked`) загружаются за константное число SQL-запросов O(1) на запрос вместо O(N) по статьям.
- В одиночных составных чтениях (`get_article`, `get_article_data`, `get_user_data`) существование статьи/пользователя проверяется один раз за запрос, а скалярные поля `User` в `get_user_data` читаются одним `SELECT` вместо отдельного запроса на каждую колонку.
- Контракт и форматы ответов всех API-методов (включая `404` и удалённых авторов) остаются без изменений.

## Готово, когда
- `article.is_article_not_exist` выбирает только `Article.id`, `user.is_user_not_exist` — только `User.username`.
- При сборке ленты (`GET /articles`) и `GET /articles/{id}/data` колонка `articles.body` не запрашивается из БД.
- Число SQL-запросов при сборке ленты в `GET /articles` не растёт линейно с числом статей (O(1) пакетных запросов).
- В `GET /users/me`, `GET /articles/{id}/data` и `GET /articles/{id}` убраны повторные проверки существования и поколоночные `SELECT` по `User`.
- Всё подтверждено unit-тестами с подсчётом SQL-запросов (например, через `before_cursor_execute`), полный `make test` проходит.

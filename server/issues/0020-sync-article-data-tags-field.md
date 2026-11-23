---
id: 0020
title: Синхронизировать поле tags в GET /articles/{id}/data между api_info и backend
areas: [api, articles, tests]
date: 2026-11-23
---

# 0020. Синхронизировать поле tags в GET /articles/{id}/data между api_info и backend

## Проблема
`src/backend.py::get_article_data` поддерживает поле `"tags"` в `requested_data`, но в схеме `src/api/api_info.py::articles_data_get` и в докстринге `api_articles_data_get` его нет — поэтому запрос `GET /articles/{id}/data?requested_data=tags` всегда отклоняется с `400`.

## Как возникает и к чему приводит
- *Как возникает:* в `backend.get_article_data` в словаре `accessors` прописан `"tags": lambda: article.tags(session, article_id)`, но при описании схемы `api_info.articles_data_get` и контракта в `src/api/routes/articles_data.py` это поле не добавили.
- *Негативный эффект:* код поддержки `"tags"` в `backend.py` остаётся недостижимым через API, а клиент не может запросить теги статьи через `/articles/{id}/data` без загрузки всей статьи (`GET /articles/{id}`) вместе с телом `body` до 16 МБ.

## Желаемое поведение
- Поле `"tags"` добавлено в `src/api/api_info.py::articles_data_get` (`_requested_field("tags")`) и описано в докстринге `src/api/routes/articles_data.py::api_articles_data_get`.
- `GET /articles/{id}/data?requested_data=tags` возвращает `200 OK` с `{"tags": [...]}` и отдаёт `"tags"` в списке допустимых полей `OPTIONS /articles/{id}/data`.

## Готово, когда
- `GET /articles/{id}/data?requested_data=tags` возвращает список тегов статьи, а `OPTIONS /articles/{id}/data` содержит `"tags"`.
- Обновлён докстринг `api_articles_data_get` и e2e-тест в `tests/routes/test_articles_data.py`.
- Полный `make test` проходит.

---
id: 0025
title: Убрать повторную JSON-сериализацию body и preview при публикации статьи
areas: [api, db, articles, tests]
date: 2026-11-23
---

# 0025. Убрать повторную JSON-сериализацию body и preview при публикации статьи

## Проблема
При обработке `POST /articles` поля `body` (размером до 16 МБ) и `preview` (до 64 КБ) трижды подряд сериализуются через `json.dumps(..., ensure_ascii=False)` и дважды кодируются в UTF-8, хотя нужен ровно один готовый сериализованный результат.

## Как возникает и к чему приводит
- *Как возникает:* в ходе одного запроса `POST /articles` выполняются три независимые сериализации одного и того же `dict`:
  1. `src/api/shared.py::_is_valid_text` вызывает `json.dumps(value, ensure_ascii=False).encode("utf8")` для проверки валидности UTF-8 и отбрасывает результат;
  2. `src/api/shared.py::_stored_size` (из `_check_limits`) снова вызывает `json.dumps(value, ensure_ascii=False).encode("utf8")` для проверки `max_bytes` и снова отбрасывает результат;
  3. `src/db/article.py::post` третий раз вызывает `json.dumps(body, ensure_ascii=False)` (и то же для `preview`) для записи в БД.
- *Негативный эффект:* на крупной статье (близкой к пределу 16 МБ) сервер тратит втрое больше CPU и создаёт десятки мегабайт лишних временных аллокаций (`str` + `bytes`) в памяти на каждый `POST /articles`, повышая задержку и пиковое потребление памяти.

## Желаемое поведение
- При обработке `POST /articles` сериализация `body` и `preview` в JSON (`ensure_ascii=False`) и проверка UTF-8 / `max_bytes` выполняются **ровно один раз**, а полученная JSON-строка переиспользуется при сохранении в `articles.body` и `article_preview.preview_content`.
- Внешнее поведение API (все проверки валидности UTF-8, `not_blank`, `max_bytes` и формат сохранённого JSON в БД) остаётся полностью неизменным.
- Прямые вызовы `backend.post_article` и `article.post` с `dict` (включая существующие unit-тесты) продолжают работать без изменений.

## Готово, когда
- В `POST /articles` поля `body` и `preview` сериализуются в JSON не более одного раза за запрос (объединены проверка валидности/размера и запись в БД).
- Все проверки валидации (`must be valid Unicode text`, `must be at most ... bytes`, `must not be blank`) работают как прежде.
- Полный `make test` проходит.

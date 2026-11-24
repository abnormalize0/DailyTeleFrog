---
id: 0031
title: Отвязать src/db и request_status от Flask/HTTP и убрать лишние прокси в backend.py
areas: [api, db, tests]
date: 2026-11-23
---

# 0031. Отвязать src/db и request_status от Flask/HTTP и убрать лишние прокси в backend.py

## Проблема
Слой работы с БД (`src/db/*.py`) транзитивно импортирует Flask и привязан к HTTP-кодам через `src/request_status.py`, а в `src/backend.py` есть лишние однострочные функции-прокси (`resolve_token`, `add_user`), противоречащие правилу простоты из `SKILL.md`.

## Как возникает и к чему приводит
- *Как возникает:*
  - `src/request_status.py` одновременно хранит доменные статусы (`Status`, `StatusType`, `ErrorType`) и HTTP-слой (`from flask import Response`, HTTP-коды, `problem_response`), поэтому каждый модуль `src/db/*.py` транзитивно тянет зависимость от Flask;
  - `src/backend.py::resolve_token` — однострочная обёртка `return auth.resolve_access_token(...)`, а `src/backend.py::add_user` лишь распаковывает словарь и подставляет `creation_date` (хотя `article.post` и `comment.add` вычисляют `creation_date` сами в `src/db/`), при этом другие маршруты (`routes/articles_item.py`, `routes/auth_logout_all.py`) уже вызывают `src/db/*` напрямую.
- *Негативный эффект:*
  - нарушена однонаправленность зависимостей слоёв (`api` → `backend` → `db`): нижний слой `src/db/` зависит от веб-фреймворка Flask и HTTP-кодов;
  - лишние прокси в `src/backend.py` заставляют прыгать по файлам ради одного вызова и создают непоследовательность между маршрутами.

## Желаемое поведение
- `src/request_status.py` не импортирует Flask и описывает только доменные статусы и виды ошибок (`Status`, `StatusType`, `ErrorType`); построение HTTP-ответа (`problem_response` и маппинг `ErrorType` → HTTP-код, `slug`, `title`) вынесено в HTTP-слой (доступный и `src/api/`, и `src/log.py` без циклических импортов).
- `src/db/` не имеет ни прямых, ни транзитивных импортов Flask.
- Однострочный прокси `backend.resolve_token` удалён (`shared.py` вызывает `auth.resolve_access_token` напрямую), а `user.add_user` сам вычисляет `creation_date` по умолчанию (как `article.post` и `comment.add`), убирая лишнюю обёртку `backend.add_user`.

## Готово, когда
- В `src/request_status.py` и `src/db/` нет импортов Flask (проверено статическим тестом или импортом).
- `problem_response` и HTTP-маппинг живут на HTTP-слое, внешний формат ответов API не изменился.
- Лишние прокси `backend.resolve_token` и `backend.add_user` удалены, их вызывающие переведены на `src/db/`.
- Полный `make test` проходит.

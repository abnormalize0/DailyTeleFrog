---
id: 0030
title: Перевести JSON-ответы API на нативный Flask и добавить проверку синхронности OPTIONS
areas: [api, logging, tests]
date: 2026-11-23
---

# 0030. Перевести JSON-ответы API на нативный Flask и добавить проверку синхронности OPTIONS

## Проблема
Ответы API сериализуются вручную через `json.dumps(...)`: обработчики `OPTIONS` в `src/api/api_info.py` возвращают обычную строку (`Content-Type: text/html` вместо `application/json`), а обычные маршруты используют ручные обёртки `shared.json_response` и `shared.no_content` вместо встроенной сериализации Flask. Кроме того, маршруты и методы в `api_info.py` дублируют `routes/` без автоматической проверки на синхронность.

## Как возникает и к чему приводит
- *Как возникает:*
  - обработчики `OPTIONS` в `src/api/api_info.py` возвращают `json.dumps(...)` (`str`), для которого Flask по умолчанию ставит `Content-Type: text/html; charset=utf-8`;
  - маршруты в `src/api/routes/` вызывают `shared.json_response` (`Response(json.dumps(data), ...)`) и `shared.no_content`, потому что декоратор `src/log.py::log_request` напрямую читает `result.status_code`, `result.status` и `result.get_data()` и падал бы на нативных возвратах Flask (`dict`, `(dict, 201, headers)`, `("", 204)`);
  - соответствие путей и HTTP-методов между `src/api/routes/` и `src/api/api_info.py` проверяется только вручную.
- *Негативный эффект:*
  - клиенты и инструменты, проверяющие `Content-Type: application/json`, некорректно воспринимают ответы `OPTIONS` как HTML;
  - в `shared.py` и `routes/` поддерживается лишний слой ручных обёрток поверх стандартного поведения Flask;
  - легко пропустить или сломать `OPTIONS` при добавлении/изменении маршрута, и тесты этого не поймают.

## Желаемое поведение
- `src/log.py::log_request` преобразует результат обработчика через `flask.make_response(...)`, что позволяет всем маршрутам возвращать нативные значения Flask (`dict`, `(dict, 201, {"Location": ...})`, `("", 204)`).
- Все обработчики `OPTIONS` в `src/api/api_info.py` возвращают `dict` напрямую, получая `Content-Type: application/json` от Flask; в `src/api/routes/` ручные обёртки `shared.json_response` и `shared.no_content` заменены на нативные возвраты Flask (`request_status.problem_response` сохраняется для ответов с нестандартным `Content-Type: application/problem+json`).
- В `src/api/tests/` добавлена автоматическая проверка по `app.url_map` и `app.test_client()`:
  - каждый маршрут и HTTP-метод из `src/api/routes/` описан в `OPTIONS` (`api_info.py`);
  - в `api_info.py` нет «осиротевших» `OPTIONS` для несуществующих маршрутов или методов;
  - каждый ответ `OPTIONS` имеет статус `200`, `Content-Type: application/json` и валидный JSON.

## Готово, когда
- `log_request` использует `make_response`; обработчики в `src/api/routes/` и `src/api/api_info.py` возвращают JSON/статус нативными средствами Flask без ручных `json.dumps`, `json_response` и `no_content`.
- Все ответы `OPTIONS` отдают `Content-Type: application/json`.
- Unit-тест в `src/api/tests/` проверяет полное соответствие маршрутов и методов между `routes/` и `api_info.py`.
- Полный `make test` проходит.

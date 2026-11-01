---
name: "dailytelefrog-new-api-method"
description: "Use when adding a new API method (endpoint) to the DailyTeleFrog backend (server/src/api/routes/), or when changing the parameters or response of an existing one."
---

# Новый API-метод в DailyTeleFrog

Общие правила проекта (только `server/`, простота, типизация, комментарии на русском) берутся из скила `dailytelefrog-backend`. Перед началом просмотри журнал решений по области `api` (скил `dailytelefrog-decisions`).

## 1. Слои

- `server/src/api/routes/<ресурс>.py` принимает запрос: проверяет параметры, открывает сессию, делает `commit` или `rollback` и формирует ответ. Общий `app` и переиспользуемые хелперы (`read_body`, `read_query`, `require_auth` и т.п.) — в `server/src/api/shared.py`.
- `server/src/backend.py` собирает логику из нескольких вызовов `db` (см. `get_article`).
- `server/src/db/*.py` работает с отдельными запросами к таблицам и возвращает `(Status, данные)`.

Если логика укладывается в один вызов `db`, отдельную функцию в `backend.py` не заводи. Новую функцию в `db` добавляй, только если нужного запроса ещё нет.

## 2. Имена

Имя строится из пути без параметров. Для пути `/articles/{id}/like` и типа запроса PUT:
- метод в `src/api/routes/articles_like.py`: `api_articles_like_put` (префикс `api_` обязателен);
- схема параметров в `api_info.py`: `articles_like_put`, если у метода есть параметры помимо пути;
- обработчик OPTIONS в `api_info.py`: `articles_like_info` (один на путь, отдаёт схемы всех типов запроса);
- тест в `tests/routes/test_articles_like.py`: `test_articles_like_put` (файл теста — с префиксом `test_`, обязательным для обнаружения pytest).

Путь, который заканчивается идентификатором (`/articles/{id}`), получает суффикс `_item`: `articles_item.py`, `api_articles_item_get`. Ресурсы называются во множественном числе.

## 3. Четыре места и один порядок

Каждый новый метод добавляется сразу в:
1. `server/src/api/routes/<ресурс>.py`: сам метод (новый файл, если для этого пути его ещё нет);
2. `server/src/api/api_info.py`: схема параметров и ответ на OPTIONS;
3. `server/tests/routes/test_<ресурс>.py`: свой отдельный e2e-тест (тот же `<ресурс>`, что и в п.1, но с обязательным для pytest префиксом `test_` в имени файла);
4. `server/src/backend.py` и/или `server/src/db/*.py`: при необходимости.

Если метод делит путь с уже существующим (например второй метод на `/users/me`), он идёт в тот же файл ресурса, а не в новый. Новый файл ресурса в `src/api/routes/` нужно также подключить в `src/api/routes/__init__.py`. Порядок методов одинаков в файле ресурса, `api_info.py`, тестах и документации. Новый метод вставляй в одну и ту же позицию во всех файлах, рядом с методами того же пути.

## 4. Декораторы

На каждом методе стоят ровно эти декораторы в этом порядке:

```python
@app.route("/articles/<int:article_id>/like", methods=["PUT"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_articles_like_put(article_id: int):
```

`safe_api` — главный обработчик ошибок: он логирует traceback и отдаёт 500 с `UnexpectedError`, чтобы сервер не падал. `log_request` логирует аргументы для поиска проблем. `timer` записывает время выполнения запроса.

## 5. Шаблон тела метода

Шаги идут в таком порядке (образец — `api_articles_post`):
1. `read_body(api_info.<схема>)` или `read_query(api_info.<схема>)`. Обе функции возвращают `(параметры, ошибка)`. Если ошибка есть, сразу верни её: это готовый ответ 400.
2. Остальные проверки параметров, которые можно сделать без БД, через `error_response(ErrorType.<вид>, "текст")`.
3. `fill_default(…)` для необязательных полей (кроме PATCH: там отсутствие поля значит «не менять»).
4. Сессия `with get_session() as session:`, затем `require_auth` или `optional_auth`, вызов `backend`/`db`. При ошибке `session.rollback()` и `return request_status.problem_response(status)`, при успехе `session.commit()`.
5. Успешный ответ: `json_response(data)`, `json_response(data, 201, location=...)` или `no_content()`.

## 6. Формат запроса и ответа

Метод следует классическому REST (см. `dailytelefrog-backend`, раздел «Формат API»):
- идентификатор ресурса в пути, параметры GET в query-строке, данные POST/PUT/PATCH в JSON-теле;
- HTTP-код задаётся `ErrorType`: 400 `InvalidParameters`, 401 `InvalidToken` и `InvalidCredentials`, 403 `Forbidden`, 404 `NotFound`, 409 `Conflict`, 500 `UnexpectedError`;
- PUT и DELETE идемпотентны: повторный вызов даёт тот же результат и ту же успешную реакцию;
- каждое значение, которое попадает в БД, имеет предел в схеме `api_info.py`: `max_length` для `String(n)` (берётся из колонки), `max_bytes` для `Text`, `item_type` и `item_max_length` для списков. Иначе длинное значение вернётся как 500.

## 7. Докстринг метода

По образцу `api_articles_post`: одна строка о том, что делает метод, затем разделы:
- **Принимает**: каждый параметр с типом, обязательностью и смыслом;
- **Отдает**: поля ответа и когда они присутствуют;
- **Ошибки**: каждая ошибка с HTTP-кодом, `type` и условием;
- **Контракт**: что меняется в БД, что метод сознательно не проверяет и какие случаи не считаются ошибкой.

## 8. Тест

Отдельный `test_<имя>` в `server/tests/routes/test_<ресурс>.py` по образцу `test_articles_like_put` (в `tests/routes/test_articles_like.py`):
1. `check_endpoint_structure(endpoint, method)` из `tests/helpers.py`: проверяет, что метод отклоняет запрос без обязательных полей или с неверными типами.
2. Подготовка данных через fixtures из `tests/conftest.py` (`add_user`, `add_article` и т.п., объяви их параметрами тестовой функции).
3. Успешный сценарий: `assert_ok(answer, <код>)`.
4. Каждая ошибка из раздела «Ошибки» докстринга: `assert_error(answer, "<вид>")` проверяет код и формат Problem Details.
5. Результат проверяется не только ответом, но и состоянием: сделай запрос другим методом (например, `read_field("/articles/1/data", "likes")`) и убедись, что данные действительно изменились. Для PUT и DELETE проверь идемпотентность повторным вызовом.
6. Для новых PUT, PATCH и DELETE вызови `assert_preflight_allows(endpoint, method)`: браузер не отправит такой запрос без разрешения CORS.

Каждый блок проверок начинай с комментария «# Проверка, что …», как в существующих тестах.

## 9. Проверка в конце

Прогони все e2e-тесты (`make test` из `server/`) и убедись, что они проходят без ошибок. Если прогнать тесты не удалось, прямо скажи об этом и не считай задачу готовой.

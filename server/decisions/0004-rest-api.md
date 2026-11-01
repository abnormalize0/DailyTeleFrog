---
id: 0004
title: Устройство API. Классический REST, Problem Details, структура и инварианты методов
status: accepted
implementation: done
areas: [api, tests]
files: [server/src/api/api.py, server/src/api/shared.py, server/src/api/routes/, server/src/api/api_info.py, server/src/request_status.py, server/src/log.py, server/tests/routes/, server/tests/conftest.py, server/tests/helpers.py]
date: 2026-11-01
updated: 2026-11-01
superseded_by:
supersedes: 0001
---

# 0004. Устройство API

Единственная действующая запись про API-методы. Заменяет [0001](0001-api-method-conventions.md) целиком: правила структуры из неё перенесены сюда, чтобы всё про API лежало в одном месте.

## Правило для агента

### Структура и инварианты метода
1. Один файл на путь в `server/src/api/routes/`. Общие хелперы и `app` лежат в `server/src/api/shared.py`, а `api.py` только собирает их и запускает сервер.
2. На каждый `api_<путь>_<глагол>` есть отдельный e2e-тест `test_<путь>_<глагол>` в `server/tests/routes/test_<путь>.py`.
3. У метода есть подробный докстринг: Принимает, Отдает, Ошибки, Контракт.
4. Метод атомарен: `session.rollback()` при ошибке и `session.commit()` при успехе внутри `with get_session() as session:`.

### Формат запроса и ответа
5. Идентификатор ресурса передаётся в пути, параметры GET в query-строке, данные POST/PUT/PATCH в JSON-теле. Список в query-строке передаётся повторением параметра: `?tag=a&tag=b`.
6. GET читает, POST создаёт, PUT задаёт состояние, PATCH меняет часть полей, DELETE удаляет. PUT и DELETE идемпотентны.
7. Успех: 200 с данными, 201 при создании (с `Location`, если у ресурса есть адрес), 204 без тела, если возвращать нечего. Служебного `status` в успешном ответе нет.
8. Ошибка: настоящий HTTP-код и тело Problem Details (RFC 9457, `application/problem+json`). Вид ошибки задаётся только через `ErrorType` в `server/src/request_status.py`.

## Контекст
В 0001 был принят половинчатый REST: настоящие коды и query-строка, но старые URL и свой объект `status` в ответе. Коды и query-строка ещё не были реализованы, когда пользователь решил перейти на классический REST: собственный формат пришлось бы объяснять клиенту и читателям проекта, а преимуществ он почти не давал.

## Решение

### Пути

| Было | Стало | Успешный ответ |
|---|---|---|
| `GET /pages` | `GET /articles?indexes=0&...` | 200 |
| `POST /article` | `POST /articles` | 201, `Location` |
| `GET /article` | `GET /articles/{id}` | 200 |
| `GET /article/data` | `GET /articles/{id}/data?requested_data=...` | 200 |
| `POST /article/like` | `PUT` и `DELETE /articles/{id}/like` | 204 |
| `POST /article/dislike` | `PUT` и `DELETE /articles/{id}/dislike` | 204 |
| `POST /article/comment` | `POST /articles/{id}/comments` | 201, `Location` |
| `GET /article/comment/data` | `GET /comments/{id}?requested_data=...` | 200 |
| `POST /article/comment/like` | `PUT` и `DELETE /comments/{id}/like` | 204 |
| `POST /article/comment/dislike` | `PUT` и `DELETE /comments/{id}/dislike` | 204 |
| `POST /users` | `POST /users` | 201 |
| `GET /users/data` | `GET /users/me?requested_data=...` | 200 |
| `POST /users/data` | `PATCH /users/me` | 204 |
| `POST /users/password` | `PUT /users/me/password` | 204 |
| `POST /login` | `POST /auth/login` | 200 |
| `POST /auth/refresh` | `POST /auth/refresh` | 200 |
| `POST /auth/logout` | `POST /auth/logout` | 204 |

`/auth/*` намеренно остаются действиями: вход и выход не являются ресурсами, а `POST /sessions` ничего не дал бы, кроме формальной чистоты. `/users/me` вместо `/users/{username}` выбран потому, что эти методы работают только с владельцем токена.

### Виды ошибок

| `ErrorType` | `type` | Код | Когда |
|---|---|---|---|
| `InvalidParameters` | `/errors/validation` | 400 | Неверные параметры, значение длиннее предела, ссылка на несуществующий объект в теле запроса |
| `InvalidToken` | `/errors/invalid-token` | 401 | Токена нет, он не найден или истёк |
| `InvalidCredentials` | `/errors/invalid-credentials` | 401 | Неверный пароль при входе |
| `Forbidden` | `/errors/forbidden` | 403 | Реакция на свой объект, подписка на себя или блокировка себя, неверный текущий пароль при смене |
| `NotFound` | `/errors/not-found` | 404 | Нет объекта из URL |
| `Conflict` | `/errors/conflict` | 409 | Занят username или email |
| `UnexpectedError` | `/errors/internal-error` | 500 | Необработанное исключение |

Ошибки самого Flask (нет такого пути, метод не разрешён) отдаются тем же форматом с `type: about:blank`.

## Почему
- **Реакция как ресурс** ложится на схему БД из [0002](0002-db-write-pattern-and-indexes.md): реакция хранится отдельной строкой, которую `PUT` создаёт, а `DELETE` удаляет. Старый переключатель зависел от текущего состояния, поэтому повтор запроса при сетевом сбое отменял лайк.
- **Problem Details** даёт готовый стандарт вместо собственного формата и точнее старого `error_type`: `ValueError` объединял «поле неверно», «не найдено» и «занято». Подробная причина ошибки, ради которой вводился `status`, осталась в `type`, `detail` и `errors`.
- **Один `ErrorType` на код и `type`:** два разных источника разошлись бы.
- **Два вида 401:** на `invalid-token` клиент обновляет токены через `/auth/refresh`, а неверный пароль так не исправить. По той же причине неверный текущий пароль при смене даёт 403: токен в этом случае валиден.
- **`/errors/not-found` один на все сущности:** какая именно сущность не найдена, ясно из URL запроса. Отдельные виды не дали бы клиенту новой информации.
- **400 на ссылку внутри тела** (неверный `root` у комментария, несуществующий пользователь в подписках): URL при этом существует, ошибочно только содержимое запроса.
- **Пределы длины живут в схеме параметров** (`max_length`, `max_bytes`, `item_max_length` в `api_info.py`): значение длиннее колонки иначе дошло бы до MySQL и вернулось как 500. Предел `String(n)` берётся прямо из колонки, а не дублируется числом. Клиент видит пределы в ответе `OPTIONS`.
- **Одинаковые теги статьи запрещены и дают 400:** их определяет первичный ключ `article_tags`, а не сравнение в Python, потому что правило сравнения (например, без учёта регистра) задаёт БД.
- **Повторная подписка или блокировка не считается ошибкой:** `PATCH` описывает нужное состояние, и оно уже достигнуто.

## Варианты
### Половинчатый REST из 0001
- Плюсы: не меняются URL на клиенте.
- Минусы: остаётся собственный формат и неидемпотентные лайки.
- Почему не выбран: клиенту всё равно переходить на токены и переделывать GET-запросы, поэтому экономия почти нулевая.

### Свой `status` при ошибках, без Problem Details
- Плюсы: меньше правок.
- Минусы: `ValueError` не различает случаи, клиенту пришлось бы разбирать текст.
- Почему не выбран: при переделке ответов стандарт стоит почти столько же, сколько свой формат.

## Примеры
```python
parameters, error = read_body(api_info.articles_post)
if error:
    return error
...
if status.is_error:
    session.rollback()
    return request_status.problem_response(status)

session.commit()
return json_response({"article_id": article_id}, 201, location=f"/articles/{article_id}")
```

```json
{
  "type": "/errors/validation",
  "title": "Invalid request parameters",
  "status": 400,
  "detail": "Wrong request parameters structure.",
  "errors": [{ "name": "title", "reason": "is required" }]
}
```

## Последствия
- **Клиент:** все вызовы API нужно перевести на новые пути и методы. Успех определяется HTTP-кодом, а не `status.type`. Лайк больше не переключатель: клиент сам выбирает `PUT` или `DELETE` по текущему состоянию. Для `axios` ошибки 4xx и 5xx становятся исключениями.
- **Тело успешного ответа** больше не содержит `status`; остальные поля не изменились.
- **Логи:** тело успешного ответа не пишется, потому что в ответах `/auth/*` лежат токены. У ошибок тело пишется для разбора.

## Условия пересмотра
- Если клиенту потребуется отличать разные случаи 403 или 409 без чтения `detail`, добавить отдельные значения в `ErrorType`.
- Если фильтры ленты упрутся в длину URL, вынести поиск в отдельный ресурс.
- Если появятся публичные профили, добавить `GET /users/{username}` рядом с `/users/me`.

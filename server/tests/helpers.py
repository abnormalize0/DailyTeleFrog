"""
Этот файл служит для хранения вспомогательных функций для тестов в tests/routes/*.py:
общих assert-хелперов для ответов сервера и проверки валидации параметров запросов
(`OPTIONS <endpoint>`). Предполагает, что тестовый сервер уже поднят fixture `server`.
"""

import os
from typing import Any

import requests

LOCALHOST = "http://127.0.0.1:5000"
WORKDIR = os.getenv("MVP_PATH") + "/test_tmp"

# Вид ошибки -> HTTP-код. Таблица повторяет request_status.ErrorType намеренно:
# тесты проверяют контракт с клиентом, а не сверяют код сам с собой.
ERROR_CODES = {
    "validation": 400,
    "invalid-token": 401,
    "invalid-credentials": 401,
    "forbidden": 403,
    "not-found": 404,
    "conflict": 409,
}

DEFAULT_VALUES = {
    "int": 1,
    "str": "qwerty",
    "dict": {"key": "value"},
    "list": ["tag1", "tag2"],
    "bool": True,
}

WRONG_BODY_VALUES = {
    "int": "f",
    "str": 1,
    "dict": [],
    "list": {},
    "bool": "hehe",
}

# В query-строке любое значение является строкой, поэтому неверный тип бывает
# только у int и bool, а у списков — только у элементов (см. _wrong_query_value).
WRONG_QUERY_VALUES = {
    "int": "f",
    "bool": "hehe",
}


def assert_ok(answer: requests.Response, code: int = 200) -> None:
    """Проверяет, что ответ сервера успешный.

    Args:
        answer: ответ requests на запрос к серверу.
        code: ожидаемый HTTP-код, по умолчанию 200.

    Returns:
        None
    """
    assert answer.status_code == code, answer.text


def assert_error(answer: requests.Response, error: str) -> None:
    """Проверяет, что ответ сервера — ошибка ожидаемого вида в формате Problem Details.

    Args:
        answer: ответ requests на запрос к серверу.
        error: ожидаемый вид ошибки, ключ ERROR_CODES.

    Returns:
        None
    """
    code = ERROR_CODES[error]
    assert answer.status_code == code, answer.text
    assert answer.headers["Content-Type"] == "application/problem+json"
    problem = answer.json()
    assert problem["type"] == f"/errors/{error}", problem
    assert problem["status"] == code, problem
    assert problem["title"], problem
    assert problem["detail"], problem


def auth_headers(access_token: str) -> dict:
    """Строит заголовок Authorization: Bearer <access_token> для запроса.

    Args:
        access_token: access token, полученный через /auth/login (см. фикстуру add_user).

    Returns:
        dict вида {"Authorization": "Bearer <access_token>"}.
    """
    return {"Authorization": f"Bearer {access_token}"}


def read_server_log() -> str:
    """Читает лог API тестового сервера — так тесты проверяют, что в него не
    попали секреты.

    Args:
        None

    Returns:
        Содержимое лога.
    """
    with open(os.path.join(WORKDIR, "log", "server_api.log")) as log_file:
        return log_file.read()


def read_field(endpoint: str, field: str, access_token: str = None) -> Any:
    """Читает одно поле через GET-метод с параметром requested_data — так тесты
    проверяют состояние после изменяющего запроса.

    Args:
        endpoint: путь запроса, например "/articles/1/data".
        field: имя запрашиваемого поля.
        access_token: токен вызывающего, если нужен.

    Returns:
        Значение поля.
    """
    headers = auth_headers(access_token) if access_token else None
    answer = requests.get(
        LOCALHOST + endpoint, params={"requested_data": field}, headers=headers
    )
    assert_ok(answer)
    return answer.json()[field]


def assert_preflight_allows(endpoint: str, method: str) -> None:
    """Проверяет, что CORS-запрос браузера перед method разрешён. PUT, PATCH и
    DELETE браузер без него не отправит, а обычными тестами это не поймать:
    requests ограничений CORS не соблюдает.

    Args:
        endpoint: путь запроса.
        method: HTTP-метод в верхнем регистре.

    Returns:
        None
    """
    answer = requests.options(
        LOCALHOST + endpoint,
        headers={
            "Origin": "http://client.test",
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert method in answer.headers["Access-Control-Allow-Methods"], answer.headers


def _valid_value(field: dict) -> Any:
    """Строит корректное значение для параметра.

    Args:
        field: описание параметра из `OPTIONS <endpoint>`.

    Returns:
        Значение, проходящее проверку структуры.
    """
    if field.get("structure"):
        return [field["structure"][0]["name"]]
    if field.get("item_type") == "int":
        return [DEFAULT_VALUES["int"]]
    return DEFAULT_VALUES[field["type"]]


def _wrong_query_value(field: dict) -> Any:
    """Строит значение query-параметра, которое сервер обязан отвергнуть.

    Args:
        field: описание параметра из `OPTIONS <endpoint>`.

    Returns:
        Неверное значение; `None`, если для этого параметра в query-строке
        неверного значения не существует (строки и списки строк).
    """
    if field.get("structure"):
        return ["bogus_field"]
    if field.get("item_type") == "int":
        return ["f"]
    return WRONG_QUERY_VALUES.get(field["type"])


def _too_long_value(field: dict) -> Any:
    """Строит значение, превышающее ограничение из описания параметра.

    Args:
        field: описание параметра из `OPTIONS <endpoint>`.

    Returns:
        Слишком длинное значение; `None`, если ограничения размера у параметра нет.
    """
    if "max_length" in field:
        return "x" * (field["max_length"] + 1)
    if "item_max_length" in field:
        return ["x" * (field["item_max_length"] + 1)]
    if "max_bytes" in field:
        text = "x" * (field["max_bytes"] + 1)
        return {"key": text} if field["type"] == "dict" else text
    return None


def _assert_rejected(
    endpoint: str, method: str, key: str, params: dict, name: str
) -> None:
    """Отправляет запрос и проверяет, что сервер отверг параметр name с кодом 400.

    Args:
        endpoint: путь запроса.
        method: HTTP-метод.
        key: аргумент requests для параметров: "params" (query) или "json" (тело).
        params: параметры запроса.
        name: имя параметра, на который должен пожаловаться сервер.

    Returns:
        None
    """
    answer = requests.request(method, LOCALHOST + endpoint, **{key: params})
    assert_error(answer, "validation")
    assert name in [error["name"] for error in answer.json()["errors"]], answer.text


def check_endpoint_structure(endpoint: str, method: str) -> None:
    """Запрашивает описание параметров через `OPTIONS <endpoint>` и проверяет, что
    метод отвергает неверный тип каждого параметра и отсутствие обязательных.

    Args:
        endpoint: путь запроса.
        method: "get", "post", "put", "patch" или "delete".

    Returns:
        None
    """
    structure = requests.options(LOCALHOST + endpoint).json()[method]
    if not structure:
        return

    is_query = structure[0]["container"] == "query"
    key = "params" if is_query else "json"
    valid = {field["name"]: _valid_value(field) for field in structure}

    for field in structure:
        name = field["name"]
        wrong = (
            _wrong_query_value(field) if is_query else WRONG_BODY_VALUES[field["type"]]
        )
        too_long = _too_long_value(field)
        for value in (wrong, too_long):
            if value is not None:
                _assert_rejected(endpoint, method, key, {**valid, name: value}, name)
        if field["is_required"]:
            without_field = {k: v for k, v in valid.items() if k != name}
            _assert_rejected(endpoint, method, key, without_field, name)

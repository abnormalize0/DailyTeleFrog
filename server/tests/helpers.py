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

# Одиночный суррогат: допустимый JSON, который нельзя записать в UTF-8.
INVALID_TEXT_VALUES = {
    "str": "\ud800",
    "dict": {"key": "\ud800"},
    "list": ["\ud800"],
}

# Выглядит как пустота, хотя strip оставил бы от этой строки нулевой пробел.
BLANK_TEXT = " \t\n\u00a0\u200b"

# Нарушает все регулярные выражения из схем: управляющий символ и пробел.
PATTERN_MISMATCH = "\x00 @"

# Общий текст ошибки проверки структуры: причины по полям лежат в списке errors.
STRUCTURE_ERROR = "Wrong request parameters structure"

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


def assert_error(answer: requests.Response, error: str, detail: str) -> None:
    """Проверяет, что ответ сервера — ошибка ожидаемого вида в формате Problem Details.

    detail обязателен и сверяется целиком: клиент показывает этот текст человеку, а
    непустой, но бесполезный текст вроде "Unexpected error" иначе прошёл бы проверку.

    Args:
        answer: ответ requests на запрос к серверу.
        error: ожидаемый вид ошибки, ключ ERROR_CODES.
        detail: ожидаемый текст ошибки.

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
    assert problem["detail"] == detail, problem


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
    endpoint: str, method: str, key: str, params: dict, name: str, reason: str
) -> None:
    """Отправляет запрос и проверяет, что сервер отверг параметр name с кодом 400 и
    объяснил причину.

    Args:
        endpoint: путь запроса.
        method: HTTP-метод.
        key: аргумент requests для параметров: "params" (query) или "json" (тело).
        params: параметры запроса.
        name: имя параметра, на который должен пожаловаться сервер.
        reason: начало ожидаемой причины; целиком она зависит от ограничений поля.

    Returns:
        None
    """
    answer = requests.request(method, LOCALHOST + endpoint, **{key: params})
    assert_error(answer, "validation", STRUCTURE_ERROR)
    reasons = {error["name"]: error["reason"] for error in answer.json()["errors"]}
    assert reasons.get(name, "").startswith(reason), answer.text


def _wrong_value_reason(field: dict, is_query: bool) -> str:
    """Определяет, как сервер объясняет значение, неверное по типу.

    Args:
        field: описание параметра из `OPTIONS <endpoint>`.
        is_query: параметр передаётся в query-строке.

    Returns:
        Начало ожидаемой причины. В query-строке список всегда остаётся списком,
        поэтому там неверным оказывается элемент, а не сам параметр.
    """
    if is_query and field.get("structure"):
        return "must be one of"
    if is_query and field.get("item_type"):
        return f"must contain {field['item_type']}"
    return f"must be {field['type']}"


def _check_body_is_required(endpoint: str, method: str, structure: list) -> None:
    """Проверяет, что тело, не являющееся JSON-объектом, даёт 400 с перечнем
    обязательных полей, а не 500.

    Args:
        endpoint: путь запроса.
        method: HTTP-метод.
        structure: описание параметров из `OPTIONS <endpoint>`.

    Returns:
        None
    """
    required = {field["name"] for field in structure if field["is_required"]}
    if not required:
        return
    for body in ("{broken", "[1, 2]"):
        answer = requests.request(
            method,
            LOCALHOST + endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        assert_error(answer, "validation", STRUCTURE_ERROR)
        assert {error["name"] for error in answer.json()["errors"]} == required


def check_endpoint_structure(endpoint: str, method: str) -> None:
    """Запрашивает описание параметров через `OPTIONS <endpoint>` и проверяет, что
    метод отвергает с понятной причиной неверный тип, нарушение ограничений и
    невалидный Unicode в каждом параметре, отсутствие обязательных и тело, не
    являющееся JSON-объектом.

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

    if not is_query:
        _check_body_is_required(endpoint, method, structure)

    for field in structure:
        name = field["name"]
        wrong = (
            _wrong_query_value(field) if is_query else WRONG_BODY_VALUES[field["type"]]
        )
        if wrong is not None:
            reason = _wrong_value_reason(field, is_query)
            _assert_rejected(
                endpoint, method, key, {**valid, name: wrong}, name, reason
            )
        too_long = _too_long_value(field)
        if too_long is not None:
            reason = (
                "items must be at most"
                if "item_max_length" in field
                else "must be at most"
            )
            _assert_rejected(
                endpoint, method, key, {**valid, name: too_long}, name, reason
            )
        if field.get("not_blank"):
            blank = BLANK_TEXT if field["type"] == "str" else {}
            _assert_rejected(
                endpoint, method, key, {**valid, name: blank}, name, "must not be blank"
            )
        if field.get("item_not_blank"):
            _assert_rejected(
                endpoint,
                method,
                key,
                {**valid, name: ["tag", BLANK_TEXT]},
                name,
                "items must not be blank",
            )
        if "min_length" in field:
            too_short = "x" * (field["min_length"] - 1)
            _assert_rejected(
                endpoint,
                method,
                key,
                {**valid, name: too_short},
                name,
                f"must be at least {field['min_length']} characters",
            )
        if "pattern" in field:
            _assert_rejected(
                endpoint,
                method,
                key,
                {**valid, name: PATTERN_MISMATCH},
                name,
                field["pattern_reason"],
            )
        # В query-строке суррогата быть не может: её декодирует сам Flask.
        invalid_text = INVALID_TEXT_VALUES.get(field["type"])
        if invalid_text is not None and not is_query:
            _assert_rejected(
                endpoint,
                method,
                key,
                {**valid, name: invalid_text},
                name,
                "must be valid Unicode text",
            )
        if field["is_required"]:
            without_field = {k: v for k, v in valid.items() if k != name}
            _assert_rejected(endpoint, method, key, without_field, name, "is required")

"""
Этот файл служит для хранения общего для всех API-методов: Flask-приложения
`app`, чтения текущего db_url, и переиспользуемых хелперов разбора запроса и
построения ответа. Каждый метод — в своём файле в src/api/routes/, все они
регистрируются на этот же `app` (см. decisions/0004-rest-api.md).
"""

from flask import Flask, Response, request
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from werkzeug.exceptions import HTTPException
import json
import builtins

from .. import backend
from .. import request_status
from . import api_info

app = Flask(__name__)
app.register_blueprint(api_info.info)
cors = CORS(app)

# Устанавливается run_server() (см. api.py) перед запуском сервера.
db_url = None
_engine = None


@app.errorhandler(HTTPException)
def handle_http_exception(error: HTTPException) -> Response:
    """Отдаёт ошибки самого Flask (нет такого пути, метод не разрешён) в том же
    формате Problem Details, что и ошибки методов, а не HTML-страницей.

    Args:
        error: исключение Flask/Werkzeug.

    Returns:
        Ответ с кодом исключения. `type` равен "about:blank": так RFC 9457
        велит обозначать ошибку, смысл которой полностью задан HTTP-кодом.
        Берём `get_response()`, чтобы сохранить заголовки (например Allow у 405).
    """
    response = error.get_response()
    response.data = json.dumps(
        {
            "type": "about:blank",
            "title": error.name,
            "status": error.code,
            "detail": error.description,
        }
    )
    response.content_type = "application/problem+json"
    return response


def error_response(
    error_type: request_status.ErrorType, msg: str, errors: list = None
) -> Response:
    """Строит ответ с ошибкой заданного вида.

    Args:
        error_type: `request_status.ErrorType`, задаёт HTTP-код и поле `type`.
        msg: текст про этот конкретный случай (поле `detail`).
        errors: список неверных полей запроса, только для ошибок валидации.

    Returns:
        Ответ в формате Problem Details.
    """
    return request_status.problem_response(
        request_status.Status(
            request_status.StatusType.ERROR,
            error_type=error_type,
            msg=msg,
            errors=errors,
        )
    )


def json_response(data: dict, code: int = 200, location: str = None) -> Response:
    """Строит успешный JSON-ответ.

    Args:
        data: тело ответа.
        code: HTTP-код, по умолчанию 200.
        location: путь созданного ресурса для заголовка Location (ответы 201).

    Returns:
        Ответ с типом application/json.
    """
    headers = {"Location": location} if location else None
    return Response(
        json.dumps(data), status=code, mimetype="application/json", headers=headers
    )


def no_content() -> Response:
    """Строит успешный ответ без тела (204), когда возвращать клиенту нечего.

    Args:
        None

    Returns:
        Пустой ответ с кодом 204.
    """
    return Response(status=204)


def get_session() -> Session:
    """Открывает сессию SQLAlchemy, переиспользуя общий Engine между запросами.

    Args:
        None

    Returns:
        Session: новая сессия SQLAlchemy на текущий db_url.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(db_url)
    return Session(_engine)


def get_bearer_token() -> str:
    """Достаёт значение токена из заголовка Authorization: Bearer <token>.

    Args:
        None

    Returns:
        str: значение токена, либо "" — если заголовка нет или он не в
        формате "Bearer <token>".
    """
    auth_header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        return ""
    return auth_header[len(prefix) :]


def require_auth(session: Session) -> tuple:
    """Резолвит access token текущего запроса в username — для методов,
    доступных только авторизованным пользователям.

    Args:
        session: сессия SQLAlchemy, используется для проверки токена.

    Returns:
        Кортеж (str, None) — username, если токен валиден.
        Кортеж (None, str) — ответ с ошибкой 401, если токена нет, он не
        найден или истёк; вызывающий должен сразу вернуть этот ответ.
    """
    status, username = backend.resolve_token(session, get_bearer_token())
    if status.is_error:
        return None, request_status.problem_response(status)
    return username, None


def optional_auth(session: Session) -> tuple:
    """Резолвит access token текущего запроса в username — для методов,
    доступных и анонимно (тогда username == "unlogged_user").

    Args:
        session: сессия SQLAlchemy, используется для проверки токена, если
            заголовок Authorization присутствует.

    Returns:
        Кортеж (str, None) — username из токена, либо "unlogged_user", если
        заголовка Authorization нет вовсе.
        Кортеж (None, str) — ответ с ошибкой 401, если заголовок Authorization
        передан, но токен не найден/истёк (в отличие от отсутствия заголовка,
        это не считается анонимным запросом молча).
    """
    token = get_bearer_token()
    if not token:
        return "unlogged_user", None
    status, username = backend.resolve_token(session, token)
    if status.is_error:
        return None, request_status.problem_response(status)
    return username, None


def check_not_unlogged(username: str) -> Response | None:
    """Проверяет, что username не является неавторизованным пользователем.

    Args:
        username: значение поля username из тела запроса.

    Returns:
        Ответ с ошибкой, если username == "unlogged_user", иначе `None`.
    """
    if username == "unlogged_user":
        return error_response(
            request_status.ErrorType.InvalidParameters,
            "Unlogged user cannot use this method",
        )
    return None


def _stored_size(value: str | dict) -> int:
    """Считает размер значения в байтах в том виде, в каком оно попадёт в БД.

    dict хранится как результат json.dumps (см. db/article.py). Его нужно мерить
    именно так: json.dumps экранирует кириллицу, и один символ занимает 6 байт.

    Args:
        value: строка или словарь из запроса.

    Returns:
        Размер в байтах.
    """
    stored = json.dumps(value) if isinstance(value, dict) else value
    return len(stored.encode("utf8"))


def _check_limits(value: str | dict | list, element: dict) -> str | None:
    """Проверяет ограничения на размер значения, тип которого уже проверен.

    Args:
        value: значение из запроса.
        element: описание поля из api_info.

    Returns:
        Причина ошибки либо `None`, если значение подходит. Без этой проверки
        слишком длинное значение дошло бы до MySQL и вернулось как 500.
    """
    max_length = element.get("max_length")
    if max_length and len(value) > max_length:
        return f"must be at most {max_length} characters"
    max_bytes = element.get("max_bytes")
    if max_bytes and _stored_size(value) > max_bytes:
        return f"must be at most {max_bytes} bytes"
    item_max_length = element.get("item_max_length")
    if item_max_length and any(len(item) > item_max_length for item in value):
        return f"items must be at most {item_max_length} characters"
    return None


def check_structure(data: dict, pattern: list) -> list:
    """Проверяет параметры запроса на соответствие ожидаемой структуре.

    Проверяет все поля сразу, а не до первой ошибки, чтобы клиент мог показать
    пользователю все проблемы за один запрос.

    Args:
        data: параметры запроса.
        pattern: описание ожидаемых полей из api_info.

    Returns:
        Список неверных полей вида {"name", "reason"}; пустой, если всё верно.
    """
    errors = []
    for element in pattern:
        name = element["name"]
        if name not in data:
            if element["is_required"]:
                errors.append({"name": name, "reason": "is required"})
            continue
        value = data[name]
        if type(value) != getattr(builtins, element["type"]):
            errors.append({"name": name, "reason": f"must be {element['type']}"})
            continue
        if element["type"] == "list":
            allowed = [field["name"] for field in element.get("structure", [])]
            if allowed and any(item not in allowed for item in value):
                errors.append({"name": name, "reason": f"must be one of {allowed}"})
                continue
            item_type = getattr(builtins, element.get("item_type", ""), None)
            if item_type and any(type(item) != item_type for item in value):
                errors.append(
                    {"name": name, "reason": f"must contain {element['item_type']}"}
                )
                continue
        reason = _check_limits(value, element)
        if reason:
            errors.append({"name": name, "reason": reason})
    return errors


def _validated(data: dict, pattern: list) -> tuple:
    """Проверяет параметры и превращает результат в значение для метода.

    Args:
        data: параметры запроса.
        pattern: описание ожидаемых полей из api_info.

    Returns:
        Кортеж (dict, None) — параметры, если они верны.
        Кортеж (None, Response) — ответ 400, который метод должен сразу вернуть.
    """
    errors = check_structure(data, pattern)
    if errors:
        return None, error_response(
            request_status.ErrorType.InvalidParameters,
            "Wrong request parameters structure.",
            errors=errors,
        )
    return data, None


def read_body(pattern: list) -> tuple:
    """Читает и проверяет параметры из JSON-тела запроса (POST, PATCH, PUT).

    Args:
        pattern: описание ожидаемых полей из api_info.

    Returns:
        См. `_validated`. Тело, которое не является JSON-объектом, считается
        пустым: клиент получит 400 с перечнем обязательных полей, а не 500.
    """
    body = request.get_json(silent=True)
    return _validated(body if isinstance(body, dict) else {}, pattern)


def _parse_query_value(value: str, type_name: str) -> int | bool | str:
    """Приводит значение из query-строки к типу из схемы.

    В query-строке всё является строкой, поэтому типы приходится восстанавливать
    по схеме. Значение, которое привести нельзя, возвращается как есть, и его
    отвергает check_structure: так у ошибки один источник и один формат.

    Args:
        value: значение из query-строки.
        type_name: имя типа из схемы ("int", "bool", "str").

    Returns:
        Приведённое значение либо исходная строка.
    """
    if type_name == "bool":
        return {"true": True, "false": False}.get(value, value)
    if type_name == "int":
        try:
            return int(value)
        except ValueError:
            return value
    return value


def read_query(pattern: list) -> tuple:
    """Читает и проверяет параметры из query-строки (GET).

    Список передаётся повторением параметра: ?tag=a&tag=b.

    Args:
        pattern: описание ожидаемых полей из api_info.

    Returns:
        См. `_validated`.
    """
    data = {}
    for element in pattern:
        name = element["name"]
        if name not in request.args:
            continue
        if element["type"] == "list":
            item_type = element.get("item_type", "str")
            data[name] = [
                _parse_query_value(value, item_type)
                for value in request.args.getlist(name)
            ]
        else:
            data[name] = _parse_query_value(request.args[name], element["type"])
    return _validated(data, pattern)


def fill_default(data: dict, pattern: list) -> dict:
    """Дополняет data значениями по умолчанию для отсутствующих полей.

    Args:
        data: параметры запроса.
        pattern: описание полей из api_info.

    Returns:
        data, дополненный значениями из api_info.type_defaults там, где поле
        отсутствовало.
    """
    for value in pattern:
        if value["name"] not in data:
            data[value["name"]] = api_info.type_defaults[value["type"]]
    return data

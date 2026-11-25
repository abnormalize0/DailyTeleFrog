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
import re
import unicodedata

from .. import request_status
from ..db import auth
from . import api_info
from .errors import problem_response

app = Flask(__name__)
app.register_blueprint(api_info.info)
cors = CORS(app)

# Символы, которые не видны на экране: разделители (Z*), управляющие (Cc) и
# форматирующие (Cf), среди них нулевой пробел и BOM. Cn («не назначен») сюда не
# входит: в нём окажутся эмодзи новее базы Unicode этой версии Python. str.strip
# не подходит: он не считает пробелом ни U+200B, ни символы из списка ниже.
_BLANK_CATEGORIES = {"Zs", "Zl", "Zp", "Cc", "Cf"}
# Символы-заполнители и селекторы вариантов: по категории они буквы, знаки и символы,
# но выглядят как пустота, поэтому их приходится перечислять.
_INVISIBLE_CHARS = (
    set("\u034f\u115f\u1160\u17b4\u17b5\u180b\u180c\u180d\u180f\u2800\u3164\uffa0")
    | {chr(code) for code in range(0xFE00, 0xFE10)}
    | {chr(code) for code in range(0xE0100, 0xE01F0)}
)

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
    return problem_response(
        request_status.Status.error(
            error_type,
            msg,
            errors=errors,
        )
    )


def get_session() -> Session:
    """Открывает сессию SQLAlchemy, переиспользуя общий Engine между запросами.

    Args:
        None

    Returns:
        Session: новая сессия SQLAlchemy на текущий db_url.
    """
    global _engine
    if _engine is None:
        # READ COMMITTED вместо стандартного для MySQL REPEATABLE READ: запрос, который
        # дождался блокировки, должен увидеть результат предыдущего, а снимок из начала
        # транзакции этого не даёт. Блокирующее чтение вместо смены уровня не подходит:
        # при REPEATABLE READ оно блокирует промежуток индекса, и реакции разных
        # пользователей на одну статью приводили бы к взаимоблокировкам
        # (см. decisions/0009-api-atomicity.md).
        _engine = create_engine(db_url, isolation_level="READ COMMITTED")
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
    status, username = auth.resolve_access_token(session, get_bearer_token())
    if status.is_error:
        return None, problem_response(status)
    return username, None


def optional_auth(session: Session) -> tuple:
    """Резолвит access token текущего запроса в username — для методов,
    доступных и анонимно (тогда username равен `None`).

    Args:
        session: сессия SQLAlchemy, используется для проверки токена, если
            заголовок Authorization присутствует.

    Returns:
        Кортеж (str | None, None) — username из токена, либо `None`, если
        заголовка Authorization нет вовсе. См. decisions/0008-anonymous-user.md.
        Кортеж (None, str) — ответ с ошибкой 401, если заголовок Authorization
        передан, но токен не найден/истёк (в отличие от отсутствия заголовка,
        это не считается анонимным запросом молча).
    """
    token = get_bearer_token()
    if not token:
        return None, None
    status, username = auth.resolve_access_token(session, token)
    if status.is_error:
        return None, problem_response(status)
    return username, None


def _stored_size(value: str | dict) -> int:
    """Считает размер значения в байтах в том виде, в каком оно попадёт в БД.

    dict хранится как результат json.dumps(ensure_ascii=False) (см. db/article.py).
    Его нужно мерить именно так: служебные символы JSON тоже занимают место в колонке.

    Args:
        value: строка или словарь из запроса.

    Returns:
        Размер в байтах.
    """
    stored = json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value
    return len(stored.encode("utf8"))


def _contains_nul(value: object) -> bool:
    """Проверяет, есть ли NUL-байт (`\\x00`) в значении или его вложенных элементах.

    Проверку нельзя делать по строке `json.dumps(value)`: `json.dumps` экранирует
    `\\x00` в `\\\\u0000`, поэтому поиск `"\\x00"` пропустит NUL-байт, а поиск
    `"\\\\u0000"` даст ложное срабатывание на буквальную строку `r"\\u0000"`.

    Args:
        value: значение из запроса (строка, список, словарь или скаляр).

    Returns:
        `True`, если найден хотя бы один NUL-байт в строке, элементе списка
        или ключе/значении словаря, иначе `False`.
    """
    if isinstance(value, str):
        return "\x00" in value
    if isinstance(value, list):
        return any(_contains_nul(item) for item in value)
    if isinstance(value, dict):
        return any(
            _contains_nul(key) or _contains_nul(item) for key, item in value.items()
        )
    return False


def _is_valid_text(value: str | dict | list | int | bool) -> bool:
    """Проверяет, что все строки значения, в том числе вложенные и ключи словарей,
    не содержат NUL-байт (`\\x00`) и могут быть записаны в UTF-8.

    JSON допускает одиночный суррогат вроде "\\ud800", Flask принимает его как
    строку Python, а упадёт такое значение только при хешировании пароля или записи
    в MySQL и вернётся клиенту как 500. NUL-байт формально валиден в UTF-8, но
    способен обрезать строки в C-инструментах и портить логи/вывод. Проверять
    надо здесь, на входе: так клиент получит понятную ошибку с именем поля на
    любом методе.

    Args:
        value: значение из запроса, тип которого уже проверен.

    Returns:
        `True`, если значение не содержит `\\x00` и кодируется в UTF-8, иначе `False`.
    """
    if _contains_nul(value):
        return False
    try:
        json.dumps(value, ensure_ascii=False).encode("utf8")
    except UnicodeEncodeError:
        return False
    return True


def _is_blank(value: str | dict) -> bool:
    """Проверяет, что значение выглядело бы для читателя как пустота.

    Args:
        value: строка или словарь из запроса.

    Returns:
        `True` для пустого словаря и для строки, в которой нет ни одного видимого
        символа, в том числе пустой, иначе `False`.
    """
    if isinstance(value, dict):
        return not value
    return all(
        char in _INVISIBLE_CHARS or unicodedata.category(char) in _BLANK_CATEGORIES
        for char in value
    )


def _check_limits(value: str | dict | list, element: dict) -> str | None:
    """Проверяет ограничения на размер и формат значения, тип которого уже проверен.

    Args:
        value: значение из запроса.
        element: описание поля из api_info.

    Returns:
        Причина ошибки либо `None`, если значение подходит. Без этой проверки
        слишком длинное значение дошло бы до MySQL и вернулось как 500. Длина
        проверяется раньше шаблона: её причина понятнее для слишком длинной строки.
    """
    max_length = element.get("max_length")
    if max_length and len(value) > max_length:
        return f"must be at most {max_length} characters"
    min_length = element.get("min_length")
    if min_length and len(value) < min_length:
        return f"must be at least {min_length} characters"
    if element.get("not_blank") and _is_blank(value):
        return "must not be blank"
    if element.get("item_not_blank") and any(_is_blank(item) for item in value):
        return "items must not be blank"
    pattern = element.get("pattern")
    if pattern and not re.fullmatch(pattern, value):
        return element["pattern_reason"]
    max_bytes = element.get("max_bytes")
    if max_bytes and _stored_size(value) > max_bytes:
        return f"must be at most {max_bytes} bytes"
    item_max_length = element.get("item_max_length")
    if item_max_length and any(len(item) > item_max_length for item in value):
        return f"items must be at most {item_max_length} characters"
    item_pattern = element.get("item_pattern")
    if item_pattern and any(not re.fullmatch(item_pattern, item) for item in value):
        return element["item_pattern_reason"]
    return None


def check_structure(data: dict, pattern: list) -> list:
    """Проверяет параметры запроса на соответствие ожидаемой структуре.

    Проверяет все поля сразу, а не до первой ошибки, чтобы клиент мог показать
    пользователю все проблемы за один запрос. Поля, отсутствующие в схеме,
    отклоняются как неизвестные.

    Args:
        data: параметры запроса.
        pattern: описание ожидаемых полей из api_info.

    Returns:
        Список неверных полей вида {"pointer", "detail"}; пустой, если всё верно.
    """
    errors = []
    for element in pattern:
        name = element["name"]
        pointer = f"/{name}"
        if name not in data:
            if element["is_required"]:
                errors.append({"pointer": pointer, "detail": "is required"})
            continue
        value = data[name]
        if type(value) != getattr(builtins, element["type"]):
            errors.append({"pointer": pointer, "detail": f"must be {element['type']}"})
            continue
        # Раньше проверки размера: _stored_size кодирует значение в UTF-8.
        if not _is_valid_text(value):
            errors.append({"pointer": pointer, "detail": "must be valid Unicode text"})
            continue
        allowed_scalar = element.get("allowed")
        if (
            allowed_scalar is not None
            and element["type"] != "list"
            and value not in allowed_scalar
        ):
            errors.append(
                {"pointer": pointer, "detail": f"must be one of {allowed_scalar}"}
            )
            continue
        if element["type"] == "list":
            allowed = [field["name"] for field in element.get("structure", [])]
            if allowed and any(item not in allowed for item in value):
                errors.append(
                    {"pointer": pointer, "detail": f"must be one of {allowed}"}
                )
                continue
            item_type = getattr(builtins, element.get("item_type", ""), None)
            if item_type and any(type(item) != item_type for item in value):
                errors.append(
                    {
                        "pointer": pointer,
                        "detail": f"must contain {element['item_type']}",
                    }
                )
                continue
        reason = _check_limits(value, element)
        if reason:
            errors.append({"pointer": pointer, "detail": reason})
    known_names = {element["name"] for element in pattern}
    for key in data:
        if key not in known_names:
            errors.append(_unknown_field_error(key))
    return errors


def _unknown_field_error(key: str) -> dict:
    """Строит ошибку валидации для неизвестного поля.

    Если имя ключа содержит NUL-байт или одиночный суррогат, который нельзя
    закодировать в UTF-8, не подставляет его в pointer, чтобы Status.errors
    всегда содержал валидный текст без NUL.

    Args:
        key: имя неизвестного поля.

    Returns:
        dict вида {"pointer", "detail"}.
    """
    if not _is_valid_text(key):
        return {
            "pointer": "",
            "detail": "unknown field name must be valid Unicode text",
        }
    return {"pointer": f"/{key}", "detail": "unknown field"}


def _unknown_query_errors() -> list:
    """Возвращает ошибки для всех query-параметров, когда метод их не принимает.

    Args:
        None

    Returns:
        Список ошибок вида {"pointer": "/<имя>", "detail": "unknown field"}.
    """
    return [_unknown_field_error(name) for name in request.args]


def _unexpected_body_errors() -> list:
    """Возвращает ошибки для тела запроса, когда метод не принимает тело.

    Если тело — непустой JSON-объект, перечисляет его ключи как unknown field;
    для пустого `{}`, не-объекта, битого JSON или сырого текста возвращает
    корневую ошибку (см. decisions/0011-validation-422-and-pointer-detail.md).

    Args:
        None

    Returns:
        Список ошибок вида {"pointer", "detail"}; пустой, если тело пустое.
    """
    if not request.get_data():
        return []
    body = request.get_json(silent=True)
    if isinstance(body, dict) and body:
        return [_unknown_field_error(key) for key in body]
    return [{"pointer": "", "detail": "request body is not allowed"}]


def _validated(data: dict, pattern: list, extra_errors: list | None = None) -> tuple:
    """Проверяет параметры и превращает результат в значение для метода.

    Args:
        data: параметры запроса.
        pattern: описание ожидаемых полей из api_info.
        extra_errors: дополнительные ошибки (например, лишние параметры из
            другого контейнера запроса).

    Returns:
        Кортеж (dict, None) — параметры, если они верны.
        Кортеж (None, Response) — ответ 422, который метод должен сразу вернуть.
    """
    errors = check_structure(data, pattern) + (extra_errors or [])
    if errors:
        return None, error_response(
            request_status.ErrorType.InvalidParameters,
            "Wrong request parameters structure",
            errors=errors,
        )
    return data, None


def read_body(pattern: list) -> tuple:
    """Читает и проверяет параметры из JSON-тела запроса (POST, PATCH, PUT).

    Query-строка у таких методов должна быть пустой: любые query-параметры
    отклоняются как неизвестные.

    Args:
        pattern: описание ожидаемых полей из api_info.

    Returns:
        Кортеж (dict, None) — параметры, если тело — JSON-объект и прошло проверку.
        Кортеж (None, Response) — ответ 400 /errors/bad-request, если тело
        не разобралось в JSON-объект, либо 422 /errors/validation при ошибках
        значений полей (см. decisions/0011-validation-422-and-pointer-detail.md).
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, error_response(
            request_status.ErrorType.BadRequest,
            "Request body must be a JSON object",
        )
    return _validated(body, pattern, _unknown_query_errors())


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

    Список передаётся повторением параметра: ?tag=a&tag=b. Тело запроса у
    таких методов должно быть пустым.

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
    # Неизвестные query-параметры тоже передаём в check_structure, чтобы все
    # ошибки структуры собирались в одном месте и в одном формате.
    for name in request.args:
        if name not in data:
            data[name] = request.args[name]
    return _validated(data, pattern, _unexpected_body_errors())


def require_no_params() -> Response | None:
    """Проверяет, что в запросе нет ни query-параметров, ни тела запроса.

    Используется методами с пустой схемой в api_info, чтобы лишние параметры
    не игнорировались молча.

    Args:
        None

    Returns:
        Ответ 422 /errors/validation, если переданы query-параметры или тело,
        иначе `None`.
    """
    _, error = _validated({}, [], _unknown_query_errors() + _unexpected_body_errors())
    return error


def fill_default(data: dict, pattern: list) -> dict:
    """Дополняет data значениями по умолчанию для отсутствующих полей.

    Args:
        data: параметры запроса.
        pattern: описание полей из api_info.

    Returns:
        data, дополненный результатами вызова фабрик из api_info.type_defaults
        там, где поле отсутствовало (чтобы изменяемые типы получали новый
        независимый экземпляр).
    """
    for value in pattern:
        if value["name"] not in data:
            data[value["name"]] = api_info.type_defaults[value["type"]]()
    return data

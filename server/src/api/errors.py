"""
Этот файл служит для преобразования доменных статусов ошибок (`Status`, `ErrorType`)
в HTTP-ответы формата Problem Details (RFC 9457).

Отделён от `src/api/shared.py`, потому что `problem_response` используется и в
маршрутах `src/api/`, и в декораторе `src/log.py::safe_api`: общий модуль
позволяет избежать циклических импортов и не тянуть Flask в `src/request_status.py`
и `src/db/`.
"""

import json

from flask import Response

from ..request_status import ErrorType, Status

# Одна таблица для slug, title и HTTP-кода, чтобы код ответа и `type` нельзя
# было рассинхронизировать (см. decisions/0004-rest-api.md и
# decisions/0011-validation-422-and-pointer-detail.md).
ERROR_HTTP_MAP: dict[ErrorType, tuple[str, str, int]] = {
    ErrorType.BadRequest: ("bad-request", "Bad request", 400),
    ErrorType.InvalidParameters: ("validation", "Invalid request parameters", 422),
    ErrorType.InvalidToken: ("invalid-token", "Missing or invalid token", 401),
    ErrorType.InvalidCredentials: ("invalid-credentials", "Invalid credentials", 401),
    ErrorType.Forbidden: ("forbidden", "Forbidden", 403),
    ErrorType.NotFound: ("not-found", "Resource not found", 404),
    ErrorType.Conflict: ("conflict", "Resource conflict", 409),
    ErrorType.UnexpectedError: ("internal-error", "Internal server error", 500),
}


def problem_details(status: Status) -> dict:
    """Собирает тело ответа с ошибкой в формате Problem Details (RFC 9457).

    Args:
        status: `Status` с ошибкой.

    Returns:
        dict с полями type, title, status, detail и, для ошибок валидации,
        errors. `type` относительный: стандарт не требует, чтобы по нему
        открывалась страница, он лишь идентифицирует вид ошибки.
    """
    if status.error_type is None:
        raise ValueError("OK status does not have Problem Details")
    slug, title, http_code = ERROR_HTTP_MAP[status.error_type]
    problem = {
        "type": f"/errors/{slug}",
        "title": title,
        "status": http_code,
        "detail": status.msg,
    }
    if status.errors:
        problem["errors"] = status.errors
    return problem


def problem_response(status: Status) -> Response:
    """Строит HTTP-ответ с ошибкой из `Status`.

    Args:
        status: `Status` с ошибкой.

    Returns:
        Flask-`Response` с типом application/problem+json и кодом ошибки.
    """
    body = problem_details(status)
    return Response(
        json.dumps(body),
        status=body["status"],
        mimetype="application/problem+json",
    )

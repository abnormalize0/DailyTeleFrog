"""
Этот файл служит для хранения unit-тестов src/api/errors.py: таблицы соответствия
`ErrorType` HTTP-кодам и формату Problem Details (RFC 9457), а также построения
HTTP-ответов `problem_details` и `problem_response`.
"""

import json

import pytest

from src.api.errors import ERROR_HTTP_MAP, problem_details, problem_response
from src.request_status import ErrorType, Status


def test_error_type_table() -> None:
    # Таблица повторена в тесте намеренно: клиент опирается на эти значения,
    # и случайная правка ERROR_HTTP_MAP не должна проходить незамеченной.
    assert ERROR_HTTP_MAP == {
        ErrorType.BadRequest: ("bad-request", "Bad request", 400),
        ErrorType.InvalidParameters: ("validation", "Invalid request parameters", 422),
        ErrorType.InvalidToken: ("invalid-token", "Missing or invalid token", 401),
        ErrorType.InvalidCredentials: (
            "invalid-credentials",
            "Invalid credentials",
            401,
        ),
        ErrorType.Forbidden: ("forbidden", "Forbidden", 403),
        ErrorType.NotFound: ("not-found", "Resource not found", 404),
        ErrorType.Conflict: ("conflict", "Resource conflict", 409),
        ErrorType.UnexpectedError: ("internal-error", "Internal server error", 500),
    }


def test_status_ok_rejects_problem_helpers() -> None:
    ok = Status.ok()
    with pytest.raises(ValueError, match="OK status"):
        problem_details(ok)
    with pytest.raises(ValueError, match="OK status"):
        problem_response(ok)


def test_problem_details_fields() -> None:
    status = Status.error(ErrorType.Conflict, "Already exists")

    assert problem_details(status) == {
        "type": "/errors/conflict",
        "title": "Resource conflict",
        "status": 409,
        "detail": "Already exists",
    }


def test_problem_details_includes_errors_only_when_present() -> None:
    errors = [{"pointer": "/title", "detail": "is required"}]
    status = Status.error(ErrorType.InvalidParameters, "Bad", errors)

    assert problem_details(status)["errors"] == errors
    assert "errors" not in problem_details(Status.error(ErrorType.Forbidden, "Denied"))


def test_problem_response() -> None:
    status = Status.error(ErrorType.InvalidToken, "Expired")

    response = problem_response(status)

    assert response.status_code == 401
    assert response.mimetype == "application/problem+json"
    assert json.loads(response.get_data(as_text=True)) == problem_details(status)

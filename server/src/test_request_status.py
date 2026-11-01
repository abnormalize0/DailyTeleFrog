"""
Этот файл служит для хранения unit-тестов src/request_status.py: таблицы видов
ошибок и сборки тела ответа в формате Problem Details (RFC 9457).
"""

import json

from src import request_status
from src.request_status import ErrorType, Status, StatusType


def test_error_type_table() -> None:
    # Таблица повторена в тесте намеренно: клиент опирается на эти значения,
    # и случайная правка ErrorType не должна проходить незамеченной.
    assert {error.slug: error.http_code for error in ErrorType} == {
        "validation": 400,
        "invalid-token": 401,
        "invalid-credentials": 401,
        "forbidden": 403,
        "not-found": 404,
        "conflict": 409,
        "internal-error": 500,
    }


def test_status_is_error() -> None:
    assert Status(StatusType.ERROR, ErrorType.NotFound).is_error
    assert not Status(StatusType.OK).is_error


def test_status_ok_ignores_error_fields() -> None:
    status = Status(StatusType.OK, ErrorType.NotFound, msg="ignored", errors=[{}])

    assert not status.is_error
    assert status._error_type is None
    assert status._msg is None
    assert status._errors is None


def test_problem_fields() -> None:
    status = Status(StatusType.ERROR, ErrorType.Conflict, msg="Already exists")

    assert status.http_code == 409
    assert status.problem() == {
        "type": "/errors/conflict",
        "title": "Resource conflict",
        "status": 409,
        "detail": "Already exists",
    }


def test_problem_includes_errors_only_when_present() -> None:
    errors = [{"name": "title", "reason": "is required"}]
    status = Status(StatusType.ERROR, ErrorType.InvalidParameters, "Bad", errors)

    assert status.problem()["errors"] == errors
    assert "errors" not in Status(StatusType.ERROR, ErrorType.Forbidden).problem()


def test_problem_response() -> None:
    status = Status(StatusType.ERROR, ErrorType.InvalidToken, msg="Expired")

    response = request_status.problem_response(status)

    assert response.status_code == 401
    assert response.mimetype == "application/problem+json"
    assert json.loads(response.get_data(as_text=True)) == status.problem()


def test_not_found() -> None:
    status = request_status.not_found("article with id", 7)

    assert status.http_code == 404
    assert status.problem()["detail"] == "Cannot find article with id: 7"

"""
Этот файл служит для хранения unit-тестов src/request_status.py: таблицы видов
ошибок, фабрик и валидации инвариантов `Status`, а также сборки тела ответа в
формате Problem Details (RFC 9457).
"""

import json
import pytest

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


def test_status_factories() -> None:
    ok = Status.ok()
    assert not ok.is_error
    assert ok._error_type is None
    assert ok._msg is None
    assert ok._errors is None

    errors = [{"name": "title", "reason": "is required"}]
    err = Status.error(ErrorType.InvalidParameters, "Bad", errors=errors)
    assert err.is_error
    assert err._error_type == ErrorType.InvalidParameters
    assert err._msg == "Bad"
    assert err._errors == errors


def test_status_is_error() -> None:
    assert Status.error(ErrorType.NotFound, "Missing").is_error
    assert not Status.ok().is_error


@pytest.mark.parametrize(
    "bad_status_type",
    [True, False, 0, "OK", 1, None],
)
def test_status_init_rejects_non_status_type(bad_status_type: object) -> None:
    with pytest.raises(TypeError, match="StatusType"):
        Status(bad_status_type)  # type: ignore[arg-type]


def test_status_init_requires_error_type_for_error() -> None:
    with pytest.raises(TypeError, match="ErrorType"):
        Status(StatusType.ERROR, msg="Missing")
    with pytest.raises(TypeError, match="ErrorType"):
        Status(StatusType.ERROR, "not-found", msg="Missing")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ErrorType"):
        Status.error("not-found", "Missing")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_msg", [None, 123])
def test_status_error_rejects_non_str_msg(bad_msg: object) -> None:
    with pytest.raises(TypeError, match="msg must be a str"):
        Status.error(ErrorType.NotFound, bad_msg)  # type: ignore[arg-type]


@pytest.mark.parametrize("blank_msg", ["", "   ", "\n\t"])
def test_status_error_rejects_blank_msg(blank_msg: str) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        Status.error(ErrorType.NotFound, blank_msg)


def test_status_error_rejects_non_list_errors() -> None:
    with pytest.raises(TypeError, match="list or None"):
        Status.error(
            ErrorType.InvalidParameters,
            "Bad",
            errors="oops",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"error_type": ErrorType.NotFound},
        {"msg": "ignored"},
        {"msg": ""},
        {"errors": [{}]},
        {"errors": []},
        {"error_type": ErrorType.NotFound, "msg": "ignored", "errors": [{}]},
    ],
)
def test_status_ok_rejects_error_fields(kwargs: dict) -> None:
    with pytest.raises(ValueError, match="OK status"):
        Status(StatusType.OK, **kwargs)


def test_status_ok_rejects_error_accessors() -> None:
    ok = Status.ok()
    with pytest.raises(ValueError, match="OK status"):
        _ = ok.http_code
    with pytest.raises(ValueError, match="OK status"):
        ok.problem()
    with pytest.raises(ValueError, match="OK status"):
        request_status.problem_response(ok)


def test_problem_fields() -> None:
    status = Status.error(ErrorType.Conflict, "Already exists")

    assert status.http_code == 409
    assert status.problem() == {
        "type": "/errors/conflict",
        "title": "Resource conflict",
        "status": 409,
        "detail": "Already exists",
    }


def test_problem_includes_errors_only_when_present() -> None:
    errors = [{"name": "title", "reason": "is required"}]
    status = Status.error(ErrorType.InvalidParameters, "Bad", errors)

    assert status.problem()["errors"] == errors
    assert "errors" not in Status.error(ErrorType.Forbidden, "Denied").problem()


def test_problem_response() -> None:
    status = Status.error(ErrorType.InvalidToken, "Expired")

    response = request_status.problem_response(status)

    assert response.status_code == 401
    assert response.mimetype == "application/problem+json"
    assert json.loads(response.get_data(as_text=True)) == status.problem()


def test_not_found() -> None:
    status = request_status.not_found("article with id", 7)

    assert status.http_code == 404
    assert status.problem()["detail"] == "Cannot find article with id: 7"

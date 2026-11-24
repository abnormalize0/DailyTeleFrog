"""
Этот файл служит для хранения unit-тестов src/request_status.py: фабрик и
валидации инвариантов `Status`, хелпера `not_found`, а также проверки отсутствия
прямых и транзитивных импортов Flask в доменных модулях и слое БД.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from src import request_status
from src.request_status import ErrorType, Status, StatusType

SERVER_ROOT = Path(__file__).resolve().parent.parent.parent


def test_status_factories() -> None:
    ok = Status.ok()
    assert not ok.is_error
    assert ok.error_type is None
    assert ok.msg is None
    assert ok.errors is None

    errors = [{"pointer": "/title", "detail": "is required"}]
    err = Status.error(ErrorType.InvalidParameters, "Bad", errors=errors)
    assert err.is_error
    assert err.error_type == ErrorType.InvalidParameters
    assert err.msg == "Bad"
    assert err.errors == errors

    root_err = Status.error(
        ErrorType.InvalidParameters,
        "Bad",
        errors=[{"pointer": "", "detail": "request is invalid"}],
    )
    assert root_err.errors == [{"pointer": "", "detail": "request is invalid"}]


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
    with pytest.raises(TypeError, match="list"):
        Status.error(
            ErrorType.InvalidParameters,
            "Bad",
            errors="oops",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "bad_errors",
    [
        None,
        [],
        ["not-a-dict"],
        [{"name": "title", "reason": "is required"}],
        [{"pointer": "/title"}],
        [{"pointer": "/title", "detail": "ok", "extra": 1}],
        [{"pointer": 123, "detail": "is required"}],
        [{"pointer": "/title", "detail": 123}],
        [{"pointer": "title", "detail": "is required"}],
        [{"pointer": "   ", "detail": "is required"}],
        [{"pointer": "/title", "detail": ""}],
        [{"pointer": "/title", "detail": "   "}],
    ],
)
def test_status_invalid_parameters_requires_valid_errors(bad_errors: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        Status.error(
            ErrorType.InvalidParameters,
            "Bad",
            errors=bad_errors,  # type: ignore[arg-type]
        )


def test_status_non_validation_error_rejects_errors() -> None:
    for error_type in (ErrorType.BadRequest, ErrorType.NotFound):
        with pytest.raises(ValueError, match="InvalidParameters"):
            Status.error(
                error_type,
                "Bad",
                errors=[{"pointer": "/title", "detail": "is required"}],
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


def test_not_found() -> None:
    status = request_status.not_found("article with id", 7)

    assert status.error_type == ErrorType.NotFound
    assert status.msg == "Cannot find article with id: 7"


def test_domain_and_db_modules_do_not_import_flask() -> None:
    # Проверяем в чистом процессе, чтобы уже загруженные pytest/api тесты не
    # загрязняли sys.modules.
    code = (
        "import sys\n"
        "from src import backend, request_status\n"
        "from src.db import article, auth, comment, rows, scheme, user\n"
        "assert 'flask' not in sys.modules, 'flask must not be imported'\n"
        "assert 'werkzeug' not in sys.modules, 'werkzeug must not be imported'\n"
        "assert 'src.api' not in sys.modules, 'src.api must not be imported'\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=SERVER_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

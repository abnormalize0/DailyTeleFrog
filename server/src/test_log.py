"""
Этот файл служит для хранения unit-тестов src/log.py: маскирования секретов в логе
и декораторов API-методов. Запросы создаются через test_request_context: декораторам
нужен только контекст Flask, а не работающий сервер.
"""

import json
import logging
from collections.abc import Callable

import pytest
from flask import Flask, Response
from werkzeug.datastructures import Headers

from src import config, log

SECRET = "secret-value"


def test_redact_body_masks_every_sensitive_field() -> None:
    body = {
        "username": "frog",
        "password": SECRET,
        "previous_password": SECRET,
        "new_password": SECRET,
        "refresh_token": SECRET,
    }

    assert log._redact_body(body) == {
        "username": "frog",
        "password": "***",
        "previous_password": "***",
        "new_password": "***",
        "refresh_token": "***",
    }


def test_redact_body_keeps_non_dict() -> None:
    assert log._redact_body(["password"]) == ["password"]
    assert log._redact_body(None) is None


def test_redact_headers() -> None:
    headers = Headers({"Authorization": f"Bearer {SECRET}", "Accept": "*/*"})

    assert log._redact_headers(headers) == {"Authorization": "***", "Accept": "*/*"}


def test_redact_headers_without_authorization() -> None:
    assert log._redact_headers(Headers({"Accept": "*/*"})) == {"Accept": "*/*"}


def _run_logged_request(
    caplog: pytest.LogCaptureFixture, handler: Callable[[], Response]
) -> Response:
    """Выполняет handler под log_request как запрос с секретами в теле и заголовке.

    Args:
        caplog: fixture pytest, перехватывает записи лога.
        handler: обработчик, который оборачивается в log_request.

    Returns:
        Ответ обработчика.
    """
    # Логгер настраивает start.py, поэтому без сервера его уровень надо задать тут.
    with caplog.at_level(logging.INFO, logger=config.log_server_api.path):
        with Flask(__name__).test_request_context(
            json={"username": "frog", "password": SECRET},
            headers={"Authorization": f"Bearer {SECRET}"},
        ):
            return log.log_request(handler)()


def test_log_request_hides_secrets_and_success_body(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def handler() -> Response:
        return Response(json.dumps({"access_token": "issued-token"}), status=200)

    response = _run_logged_request(caplog, handler)

    assert response.status_code == 200
    assert "frog" in caplog.text
    assert SECRET not in caplog.text
    assert "issued-token" not in caplog.text


def test_log_request_writes_error_body(caplog: pytest.LogCaptureFixture) -> None:
    def handler() -> Response:
        return Response("wrong request", status=400)

    _run_logged_request(caplog, handler)

    assert "wrong request" in caplog.text


def test_log_request_survives_broken_json() -> None:
    def handler() -> Response:
        return Response(status=204)

    with Flask(__name__).test_request_context(
        data="{broken", content_type="application/json"
    ):
        assert log.log_request(handler)().status_code == 204


def test_safe_api_passes_result() -> None:
    expected = Response(status=204)

    assert log.safe_api(lambda: expected)() is expected


def test_safe_api_turns_exception_into_500(caplog: pytest.LogCaptureFixture) -> None:
    def handler() -> Response:
        raise RuntimeError("internal detail")

    response = log.safe_api(handler)()

    assert response.status_code == 500
    assert response.mimetype == "application/problem+json"
    assert json.loads(response.get_data(as_text=True))["detail"] == "Unexpected error"
    # Traceback нужен в логе, а клиент не должен видеть внутренности сервера.
    assert "internal detail" in caplog.text
    assert "internal detail" not in response.get_data(as_text=True)


def test_wrappers_keep_function_name() -> None:
    # Flask регистрирует маршрут по имени функции: если декоратор его потеряет,
    # все методы получат имя wrapper и сервер упадёт на старте.
    def api_example() -> None:
        pass

    timer = log.timer(config.log_server_api)

    assert timer(api_example).__name__ == "api_example"
    assert log.log_request(api_example).__name__ == "api_example"
    assert log.safe_api(api_example).__name__ == "api_example"

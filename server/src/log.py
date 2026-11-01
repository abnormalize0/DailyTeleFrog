"""
Этот файл служит для хранения декораторов, которые используются для системы логгирования на сервере.
"""

import logging
import traceback
from collections.abc import Callable
from datetime import datetime
from typing import Any

from flask import Response, request
from werkzeug.datastructures import Headers

from . import config
from . import request_status

# Поля тела запроса и заголовок, которые нельзя писать в лог в открытом виде.
_SENSITIVE_BODY_FIELDS = {
    "password",
    "previous_password",
    "new_password",
    "refresh_token",
}
_REDACTED = "***"


def _redact_body(body: Any) -> Any:
    """Маскирует чувствительные поля тела запроса перед логированием.

    Args:
        body: тело запроса (dict) или None/что угодно ещё.

    Returns:
        dict с теми же ключами, но значениями "***" у полей из
        _SENSITIVE_BODY_FIELDS; если body не dict, возвращается как есть.
    """
    if not isinstance(body, dict):
        return body
    return {
        key: (_REDACTED if key in _SENSITIVE_BODY_FIELDS else value)
        for key, value in body.items()
    }


def _redact_headers(headers: Headers) -> dict:
    """Маскирует заголовок Authorization (токен) перед логированием.

    Args:
        headers: request.headers (Werkzeug Headers).

    Returns:
        dict заголовков с замаскированным Authorization, если он есть.
    """
    redacted = dict(headers)
    if "Authorization" in redacted:
        redacted["Authorization"] = _REDACTED
    return redacted


def timer(log_file: config.DynamicPath) -> Callable:
    """Строит декоратор, логирующий время выполнения обернутой функции.

    Args:
        log_file: путь к файлу лога.

    Returns:
        Декоратор для функции.
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Response:
            logger = logging.getLogger(log_file.path)
            start = datetime.now()

            result = func(*args, **kwargs)

            end = datetime.now()
            exec_time = end - start
            exec_time_str = str(exec_time)
            logger.info(f"Processed request in {exec_time_str}: {func.__name__}")
            return result

        # timer used in server/api.py
        # @app.route registers url path using wrapper name, so i change name to avoid name collision
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def log_request(func: Callable) -> Callable:
    """Оборачивает func логированием тела, заголовков запроса и результата.

    Args:
        func: оборачиваемая функция.

    Returns:
        Обертка над func.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Response:
        logger = logging.getLogger(config.log_server_api.path)
        logger.info(f"Got request {func.__name__}")
        # silent=True: на битом JSON здесь нельзя падать, иначе вместо 400 от
        # shared.read_body клиент получит 500 от safe_api.
        body = request.get_json(silent=True)
        logger.info(f"Body: {_redact_body(body) if body is not None else 'Empty'}")
        logger.info(f"Query: {request.args.to_dict(flat=False)}")
        logger.info(f"Headers: {_redact_headers(request.headers)}")
        result = func(*args, **kwargs)
        # Тело пишем только у ошибок: успешные ответы /auth/login и /auth/refresh
        # содержат токены, которым в логе не место.
        details = result.get_data(as_text=True) if result.status_code >= 400 else ""
        logger.info(f"Result: {result.status} {details}\n\n\n\n")
        return result

    # @app.route registers url path using wrapper name, so i change name to avoid name collision
    wrapper.__name__ = func.__name__
    return wrapper


def safe_api(func: Callable) -> Callable:
    """Оборачивает func перехватом исключений вместо падения запроса.

    Args:
        func: оборачиваемая функция.

    Returns:
        Обертка над func: при исключении логирует traceback и возвращает
        ответ 500 в формате Problem Details вместо повторного выброса исключения.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Response:
        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            logger = logging.getLogger(config.log_server_api.path)
            logger.error(traceback.format_exc())
            return request_status.problem_response(
                request_status.Status(
                    request_status.StatusType.ERROR,
                    request_status.ErrorType.UnexpectedError,
                    msg="Unexpected error",
                )
            )

    wrapper.__name__ = func.__name__
    return wrapper

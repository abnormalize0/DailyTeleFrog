"""
Этот файл служит для хранения типа статуса и необходимых для него перечислений.
"""

import json
import enum

from flask import Response


class ErrorType(enum.Enum):
    """Виды ошибок API. Значение — (slug, title, HTTP-код): одна таблица, из
    которой строятся поля Problem Details (RFC 9457), чтобы код ответа и `type`
    нельзя было рассинхронизировать. См. decisions/0004-rest-api.md.
    """

    InvalidParameters = ("validation", "Invalid request parameters", 400)
    InvalidToken = ("invalid-token", "Missing or invalid token", 401)
    # Отдельно от InvalidToken: клиент на invalid-token обновляет токены через
    # /auth/refresh, а неверный пароль при входе так не лечится.
    InvalidCredentials = ("invalid-credentials", "Invalid credentials", 401)
    Forbidden = ("forbidden", "Forbidden", 403)
    NotFound = ("not-found", "Resource not found", 404)
    Conflict = ("conflict", "Resource conflict", 409)
    UnexpectedError = ("internal-error", "Internal server error", 500)

    def __init__(self, slug: str, title: str, http_code: int) -> None:
        """Раскладывает значение перечисления по именованным полям.

        Args:
            slug: последняя часть URI в поле `type`.
            title: короткое описание вида ошибки, одинаковое для всех её случаев.
            http_code: HTTP-код ответа.

        Returns:
            None
        """
        self.slug = slug
        self.title = title
        self.http_code = http_code


class StatusType(enum.Enum):
    ERROR = 0
    OK = 1


class Status:
    _status_type = None
    _error_type = None
    _msg = None
    _errors = None

    def __init__(
        self,
        is_error: StatusType,
        error_type: ErrorType = None,
        msg: str = None,
        errors: list = None,
    ) -> None:
        """Инициализирует объект статуса операции.

        Args:
            is_error: `StatusType` — OK или ERROR.
            error_type: `ErrorType`, обязателен при is_error == ERROR.
            msg: текст про этот конкретный случай, используется при is_error == ERROR.
            errors: список неверных полей запроса вида {"name", "reason"}, только
                для ошибок валидации.

        Returns:
            None
        """
        self._status_type = is_error

        if self.is_error:
            self._error_type = error_type
            self._msg = msg
            self._errors = errors

    @property
    def is_error(self) -> bool:
        """Проверяет, является ли статус ошибкой.

        Args:
            None

        Returns:
            `True`, если статус — ошибка, иначе `False`.
        """
        return not bool(self._status_type.value)

    @property
    def http_code(self) -> int:
        """Возвращает HTTP-код ошибки.

        Args:
            None

        Returns:
            HTTP-код из таблицы `ErrorType`.
        """
        return self._error_type.http_code

    def problem(self) -> dict:
        """Собирает тело ответа с ошибкой в формате Problem Details (RFC 9457).

        Args:
            None

        Returns:
            dict с полями type, title, status, detail и, для ошибок валидации,
            errors. `type` относительный: стандарт не требует, чтобы по нему
            открывалась страница, он лишь идентифицирует вид ошибки.
        """
        problem = {
            "type": f"/errors/{self._error_type.slug}",
            "title": self._error_type.title,
            "status": self._error_type.http_code,
            "detail": self._msg,
        }
        if self._errors:
            problem["errors"] = self._errors
        return problem


def problem_response(status: Status) -> Response:
    """Строит HTTP-ответ с ошибкой из `Status`.

    Живёт здесь, а не в api/shared.py, потому что нужна ещё и log.safe_api, а
    log.py не должен зависеть от слоя api.

    Args:
        status: `Status` с ошибкой.

    Returns:
        Flask-`Response` с типом application/problem+json и кодом ошибки.
    """
    return Response(
        json.dumps(status.problem()),
        status=status.http_code,
        mimetype="application/problem+json",
    )


def not_found(entity: str, id_value: int | str) -> Status:
    """Строит NotFound-статус для случая, когда сущность не найдена в БД.

    Args:
        entity: описание сущности и поля поиска, например "user with username"
            или "article with id".
        id_value: значение идентификатора, по которому сущность не найдена.

    Returns:
        `Status` с типом ERROR, error_type NotFound и сообщением
        "Cannot find {entity}: {id_value}".
    """
    return Status(
        StatusType.ERROR,
        error_type=ErrorType.NotFound,
        msg=f"Cannot find {entity}: {id_value}",
    )

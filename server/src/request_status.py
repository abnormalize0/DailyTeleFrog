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
    def __init__(
        self,
        status_type: StatusType,
        error_type: ErrorType | None = None,
        msg: str | None = None,
        errors: list | None = None,
    ) -> None:
        """Инициализирует объект статуса операции и проверяет его инварианты.

        Предпочтительнее использовать фабрики `Status.ok()` и `Status.error(...)`.

        Args:
            status_type: `StatusType` — OK или ERROR.
            error_type: `ErrorType`, обязателен при `status_type == StatusType.ERROR`.
            msg: текст про этот конкретный случай, используется при ERROR.
            errors: список неверных полей запроса вида {"name", "reason"}, только
                для ошибок валидации.

        Returns:
            None
        """
        if not isinstance(status_type, StatusType):
            raise TypeError("status_type must be a StatusType")
        if status_type == StatusType.OK:
            if error_type is not None or msg is not None or errors is not None:
                raise ValueError("OK status must not have error_type, msg, or errors")
        else:
            if not isinstance(error_type, ErrorType):
                raise TypeError("error_type must be an ErrorType for ERROR status")
            if not isinstance(msg, str):
                raise TypeError("msg must be a str for ERROR status")
            if not msg.strip():
                raise ValueError("msg must be a non-empty string for ERROR status")
            if errors is not None and not isinstance(errors, list):
                raise TypeError("errors must be a list or None")

        self._status_type = status_type
        self._error_type = error_type
        self._msg = msg
        self._errors = errors

    @classmethod
    def ok(cls) -> "Status":
        """Создаёт успешный статус без полей ошибки.

        Args:
            None

        Returns:
            `Status` с типом `StatusType.OK`.
        """
        return cls(StatusType.OK)

    @classmethod
    def error(
        cls,
        error_type: ErrorType,
        msg: str,
        errors: list | None = None,
    ) -> "Status":
        """Создаёт статус ошибки с обязательными типом и сообщением.

        Args:
            error_type: вид ошибки из таблицы `ErrorType`.
            msg: понятное пользователю описание ошибки (поле `detail`).
            errors: список неверных полей запроса, только для ошибок валидации.

        Returns:
            `Status` с типом `StatusType.ERROR`.
        """
        return cls(StatusType.ERROR, error_type=error_type, msg=msg, errors=errors)

    @property
    def is_error(self) -> bool:
        """Проверяет, является ли статус ошибкой.

        Args:
            None

        Returns:
            `True`, если статус — ошибка, иначе `False`.
        """
        return self._status_type == StatusType.ERROR

    @property
    def http_code(self) -> int:
        """Возвращает HTTP-код ошибки.

        Args:
            None

        Returns:
            HTTP-код из таблицы `ErrorType`.
        """
        if self._error_type is None:
            raise ValueError("OK status does not have an HTTP error code")
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
        if self._error_type is None:
            raise ValueError("OK status does not have Problem Details")
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
    return Status.error(ErrorType.NotFound, f"Cannot find {entity}: {id_value}")

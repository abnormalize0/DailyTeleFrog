"""
Этот файл служит для хранения доменных статусов операций (`Status`, `StatusType`,
`ErrorType`) без привязки к Flask и HTTP. Маппинг видов ошибок в HTTP-коды и
ответы Problem Details находится на HTTP-слое в `src/api/errors.py`.
"""

import enum


class ErrorType(enum.Enum):
    """Доменные виды ошибок операций.

    HTTP-коды и поля Problem Details (RFC 9457) сопоставляются с ними в
    `src/api/errors.py` (см. decisions/0004-rest-api.md), чтобы нижние слои
    (`src/db/`, `src/backend.py`) не зависели от веб-фреймворка.
    """

    InvalidParameters = enum.auto()
    InvalidToken = enum.auto()
    # Отдельно от InvalidToken: клиент на invalid-token обновляет токены через
    # /auth/refresh, а неверный пароль при входе так не лечится.
    InvalidCredentials = enum.auto()
    Forbidden = enum.auto()
    NotFound = enum.auto()
    Conflict = enum.auto()
    UnexpectedError = enum.auto()


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
    def error_type(self) -> ErrorType | None:
        """Возвращает вид ошибки или `None` для успешного статуса.

        Args:
            None

        Returns:
            `ErrorType` при ошибке, иначе `None`.
        """
        return self._error_type

    @property
    def msg(self) -> str | None:
        """Возвращает текст описания ошибки или `None` для успешного статуса.

        Args:
            None

        Returns:
            Строка сообщения при ошибке, иначе `None`.
        """
        return self._msg

    @property
    def errors(self) -> list | None:
        """Возвращает список ошибок полей или `None`.

        Args:
            None

        Returns:
            Список словарей ошибок полей, если передан, иначе `None`.
        """
        return self._errors


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

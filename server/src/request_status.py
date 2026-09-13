"""
Этот файл служит для хранения типа статуса и необходимых для него перечислений.
"""

import json
import enum


class ErrorType(enum.Enum):
    ValueError = 0
    OptionError = 1
    UnexpectedError = 2


class StatusType(enum.Enum):
    ERROR = 0
    OK = 1


class Status:
    _status_type = None
    _error_type = None
    _msg = None

    def __init__(self, is_error: StatusType, error_type: ErrorType = None, msg=None):
        """Инициализирует объект статуса операции.

        Args:
            is_error: `StatusType` — OK или ERROR.
            error_type: `ErrorType`, обязателен при is_error == ERROR.
            msg: текст ошибки, используется при is_error == ERROR.

        Returns:
            None
        """
        self._status_type = is_error

        if not bool(self._status_type.value):
            self._error_type = error_type.name
            self._msg = msg

    def __dict__(self):
        """Собирает статус в виде словаря.

        Args:
            None

        Returns:
            dict с полем "type", и, если статус — ошибка, дополнительно
            "error_type" и "message".
        """
        status = {"type": self._status_type.name}

        if self.is_error:
            status["error_type"] = self._error_type
            status["message"] = self._msg

        return status

    def __iter__(self):
        """Позволяет получать словарь статуса через `dict(status)`.

        Args:
            None

        Returns:
            Итератор по парам (ключ, значение) словаря статуса.
        """
        iters = self.__dict__().items()
        for k, v in iters:
            yield k, v

    def __str__(self):
        """Сериализует статус в JSON.

        Args:
            None

        Returns:
            JSON-строка со статусом.
        """
        status = dict(self)
        return json.dumps(status)

    @property
    def is_error(self):
        """Проверяет, является ли статус ошибкой.

        Args:
            None

        Returns:
            `True`, если статус — ошибка, иначе `False`.
        """
        return not bool(self._status_type.value)

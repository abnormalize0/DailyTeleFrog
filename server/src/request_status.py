import json
import enum

class ErrorType(enum.Enum):
    ValueError = 0
    OptionError = 1

class StatusType(enum.Enum):
    ERROR = 0
    OK = 1

class Status():
    _status_type = None
    _error_type = None
    _msg = None

    def __init__(self, is_error:StatusType, error_type:ErrorType=None, msg=None):
        self._status_type = is_error

        if not bool(self._status_type.value):
            self._error_type = error_type.name
            self._msg = msg

    def __dict__(self):
        status = {
            'type': self._status_type.name
        }

        if self.is_error:
            status['error_type'] = self._error_type
            status['message'] = self._msg

        return status

    def __iter__(self):
        iters = self.__dict__().items()
        for k, v in iters:
            yield k, v

    def __str__(self):
        status = dict(self)
        return json.dumps(status)

    @property
    def is_error(self):
        return not bool(self._status_type.value)
from src.repository.user import get_user, save_user
from src.request_status import Status, StatusType, ErrorType
from datetime import datetime

def login(username, password):
    if username is None or password is None:
        return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError)

    return get_user(username, password)


def register(username, password, email):
    if username is None or password is None or email is None:
        return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError)

    creation_time = datetime.now()

    return save_user(username, password, email, creation_time)

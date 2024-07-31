from src.repository.user import UserRepository
from src.request_status import Status, StatusType, ErrorType


class UserService:

    @staticmethod
    def login(username, password):
        if username is None or password is None:
            return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError)

        return UserRepository.get_user(username, password)

    @staticmethod
    def register(username, password, email):
        if username is None or password is None or email is None:
            return None, Status(StatusType.ERROR, msg='The fields are wrong')

        return UserRepository.save_user(username, password, email)

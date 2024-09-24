import json
import re
from src.repository.user import UserRepository
from src.request_status import Status, StatusType, ErrorType
from validate_email import validate_email


class UserService:
    username_regex = re.compile(r'^[a-zA-Z0-9_-]{6,32}$')
    password_regex = re.compile(r'^[a-zA-Z0-9!@#$%^&*+=<>?~`|,.]{8,24}$')

    @staticmethod
    def login(username, password):
        if username is None or password is None:
            return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError)

        user, error = UserRepository.get_user(username, password)

        if user is None:
            return user, error

        auth_token, error = user.encode_auth_token()
        if auth_token:
            return json.dumps({
                "auth_token": auth_token
            }), Status(StatusType.OK)
        return json.dumps({"auth_token": None}), error

    def register(self, username, password, email):
        if username is None or password is None or email is None:
            return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError, msg='The fields are wrong')

        if not self.username_regex.match(username):
            return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError, msg='The username format is not '
                                                                                       'compliant')

        if not self.password_regex.match(password):
            return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError, msg='The password format is not '
                                                                                       'compliant')

        if not validate_email(email):
            return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError, msg='The email format is not '
                                                                                       'compliant')

        user, error = UserRepository.save_user(username, password, email)

        if user is None:
            return user, error

        auth_token, error = user.encode_auth_token()
        if auth_token:
            return json.dumps({}), Status(StatusType.OK)
        return json.dumps({"user": None, "auth_token": None}), error

import json
from src.repository.user import UserRepository
from src.request_status import Status, StatusType, ErrorType


class UserService:

    @staticmethod
    def login(username, password):
        if username is None or password is None:
            return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError)

        user, error = UserRepository.get_user(username, password)

        auth_token, error = user.encode_auth_token()
        if auth_token:
            return json.dumps({
                "user": user.to_json(),
                "auth_token": auth_token
            }), Status(StatusType.OK)
        return json.dumps({"user": None, "auth_token": None}), error

    @staticmethod
    def register(username, password, email):
        if username is None or password is None or email is None:
            return None, Status(StatusType.ERROR, msg='The fields are wrong')

        user = UserRepository.save_user(username, password, email)
        auth_token, error = user.encode_auth_token()
        if auth_token:
            return json.dumps({'user': user.to_json(), 'auth_token': auth_token}), Status(StatusType.OK)
        return json.dumps({"user": None, "auth_token": None}), error

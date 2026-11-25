"""
Этот файл служит для хранения API-метода POST /auth/login — проверка пароля и
выпуск пары токенов авторизации. Это действие, а не ресурс, поэтому путь
намеренно не «ресурсный» (см. decisions/0004-rest-api.md).
"""

from flask.typing import ResponseReturnValue

from ... import backend
from ... import request_status
from ... import config
from ... import log
from .. import api_info
from ..shared import (
    app,
    error_response,
    fill_default,
    get_session,
    problem_response,
    read_body,
)


@app.route("/auth/login", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_auth_login_post() -> ResponseReturnValue:
    """Проверяет пароль пользователя и выпускает пару токенов авторизации
    (используется при входе в систему).

    Принимает (JSON-тело запроса, см. api_info.auth_login_post):
        - username (str, опционально) — по кому искать пользователя.
        - email (str, опционально) — по кому искать пользователя (альтернатива username).
        - password (str, обязательно) — пароль для проверки.

        Должно быть указано ровно одно из username/email.

    Отдает:
        200 и JSON:
        - access_token (str) — короткоживущий токен (см.
          config.access_token_lifetime_ms), передаётся в заголовке
          Authorization: Bearer <access_token> на все защищённые методы.
        - refresh_token (str) — долгоживущий токен (см.
          config.refresh_token_lifetime_ms) для получения новой пары токенов через
          /auth/refresh, когда access_token истечёт.

    Ошибки:
        - 400 /errors/bad-request — если тело не является корректным JSON-объектом
          или отсутствует подходящий Content-Type.
        - 422 /errors/validation — если параметры тела запроса нарушают схему
          api_info.auth_login_post, либо переданы оба ключа username и email (даже с
          пустым значением одного из них), либо не передан ни один непустой
          идентификатор.
        - 401 /errors/invalid-credentials — если пароль не совпадает с паролем
          найденного пользователя, либо пользователь с таким username/email не
          найден (одно и то же сообщение для обоих случаев, чтобы не раскрывать
          существование аккаунта).

    Контракт:
        При успехе выпускается новая пара токенов; предыдущие сессии (если были)
        не отзываются — можно быть залогиненным на нескольких устройствах сразу.
    """
    parameters, error = read_body(api_info.auth_login_post)
    if error:
        return error
    # Проверяем взаимное исключение до fill_default: иначе явная передача обоих
    # ключей с пустым значением одного из них ({"username": "a", "email": ""})
    # выглядела бы как передача одного идентификатора.
    if "username" in parameters and "email" in parameters:
        return error_response(
            request_status.ErrorType.InvalidParameters,
            "User cannot log in with both username and email",
            errors=[
                {
                    "pointer": "/username",
                    "detail": "cannot be used together with email",
                },
                {
                    "pointer": "/email",
                    "detail": "cannot be used together with username",
                },
            ],
        )
    parameters = fill_default(parameters, api_info.auth_login_post)
    if not parameters["username"] and not parameters["email"]:
        return error_response(
            request_status.ErrorType.InvalidParameters,
            "User must log in with username or email",
            errors=[
                {"pointer": "/username", "detail": "username or email is required"},
                {"pointer": "/email", "detail": "username or email is required"},
            ],
        )
    with get_session() as session:
        status, tokens = backend.login(session, parameters)
        if status.is_error:
            session.rollback()
            return problem_response(status)

        session.commit()
        return tokens

"""
Этот файл служит для хранения API-метода POST /auth/login — проверка пароля и
выпуск пары токенов авторизации. Это действие, а не ресурс, поэтому путь
намеренно не «ресурсный» (см. decisions/0004-rest-api.md).
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from .. import api_info
from ..shared import (
    app,
    check_not_unlogged,
    error_response,
    fill_default,
    get_session,
    json_response,
    read_body,
)


@app.route("/auth/login", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_auth_login_post() -> Response:
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
        - 400 /errors/validation — при некорректном теле запроса, если переданы и
          username, и email одновременно, если не передано ни то, ни другое, или
          если username == "unlogged_user".
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
    parameters = fill_default(parameters, api_info.auth_login_post)
    if parameters["username"] and parameters["email"]:
        return error_response(
            request_status.ErrorType.InvalidParameters,
            "User cant login via username and email.",
        )
    if not parameters["username"] and not parameters["email"]:
        return error_response(
            request_status.ErrorType.InvalidParameters,
            "User must login via username or email.",
        )
    unlogged_response = check_not_unlogged(parameters["username"])
    if unlogged_response:
        return unlogged_response
    with get_session() as session:
        status, tokens = backend.login(session, parameters)
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return json_response(tokens)

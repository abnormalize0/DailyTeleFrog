"""
Этот файл служит для хранения API-метода POST /auth/logout — отзыв токенов
текущей сессии.
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from .. import api_info
from ..shared import (
    app,
    get_bearer_token,
    get_session,
    no_content,
    read_body,
    require_auth,
)


@app.route("/auth/logout", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_auth_logout_post() -> Response:
    """Завершает текущую сессию: отзывает access и refresh токены.

    Принимает (JSON-тело запроса, см. api_info.auth_logout_post):
        - refresh_token (str, обязательно) — refresh token текущей сессии.

        Заголовок Authorization: Bearer <access_token> (обязательно) —
        access token текущей сессии.

    Отдает:
        204 без тела.

    Ошибки:
        - 400 /errors/validation — при некорректном теле запроса.
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          access token не найден или истёк.

    Контракт:
        Отзываются только переданные access_token/refresh_token (одна сессия);
        остальные сессии пользователя на других устройствах продолжают работать.
        Отозванный refresh_token повторно передавать можно: это не ошибка.
    """
    parameters, error = read_body(api_info.auth_logout_post)
    if error:
        return error
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status = backend.logout(
            session, get_bearer_token(), parameters["refresh_token"]
        )
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return no_content()

"""
Этот файл служит для хранения API-метода POST /auth/logout-all — отзыв всех
сессий пользователя на всех устройствах.
"""

from flask import Response

from ... import config
from ... import log
from ...db import auth
from ..shared import app, get_session, no_content, require_auth


@app.route("/auth/logout-all", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_auth_logout_all_post() -> Response:
    """Завершает все сессии пользователя: отзывает все его access и refresh токены.

    Принимает:
        Заголовок Authorization: Bearer <access_token> (обязательно) — определяет,
        чьи сессии завершаются.

    Отдает:
        204 без тела.

    Ошибки:
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.

    Контракт:
        Отзывается и токен текущей сессии, поэтому клиенту нужно войти заново.
        Повторный вызов с тем же токеном даст 401. Если нужно завершить только текущую
        сессию, используется /auth/logout.
    """
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        auth.revoke_all_tokens(session, username)
        session.commit()
        return no_content()

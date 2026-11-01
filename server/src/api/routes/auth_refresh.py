"""
Этот файл служит для хранения API-метода POST /auth/refresh — выпуск новой пары
токенов по refresh token (ротация).
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from .. import api_info
from ..shared import app, get_session, json_response, read_body


@app.route("/auth/refresh", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_auth_refresh_post() -> Response:
    """Выпускает новую пару токенов взамен истёкшего access token, по refresh token.

    Принимает (JSON-тело запроса, см. api_info.auth_refresh_post):
        - refresh_token (str, обязательно) — refresh token, выданный /auth/login
          или предыдущим вызовом этого же метода.

    Отдает:
        200 и JSON:
        - access_token (str) — новый access token.
        - refresh_token (str) — новый refresh token; переданный в запросе
          refresh_token отзывается сразу же и повторно использовать его нельзя
          (ротация).

    Ошибки:
        - 400 /errors/validation — при некорректном теле запроса.
        - 401 /errors/invalid-token — если refresh_token не найден или истёк
          (в этом случае нужно залогиниться заново через /auth/login).

    Контракт:
        Метод не требует access token — именно для этого случая (его истечения)
        он и существует.
    """
    parameters, error = read_body(api_info.auth_refresh_post)
    if error:
        return error
    with get_session() as session:
        status, tokens = backend.refresh_session(session, parameters["refresh_token"])
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return json_response(tokens)

"""
Этот файл служит для хранения API-методов пути /comments/{id}/like: лайк комментария
как ресурс, который ставится через PUT и снимается через DELETE.
"""

from flask import Response

from ... import config
from ... import log
from ... import request_status
from ...db import comment
from ..shared import app, get_session, no_content, require_auth


@app.route("/comments/<int:comment_id>/like", methods=["PUT"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_comments_like_put(comment_id: int) -> Response:
    """Ставит лайк авторизованного пользователя на комментарий.

    Принимает:
        - comment_id (int, в пути) — id комментария.

        Заголовок Authorization: Bearer <access_token> (обязательно) —
        определяет, кто ставит лайк.

    Отдает:
        204 без тела.

    Ошибки:
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.
        - 403 /errors/forbidden — если вызывающий является автором комментария.
        - 404 /errors/not-found — если комментария не существует.

    Контракт:
        Идемпотентен: повторный вызов ничего не меняет и тоже отдаёт 204.
        Существующий дизлайк этого же пользователя снимается автоматически
        (лайк и дизлайк взаимоисключающие).
    """
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status = comment.like(session, comment_id, username)
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return no_content()


@app.route("/comments/<int:comment_id>/like", methods=["DELETE"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_comments_like_delete(comment_id: int) -> Response:
    """Снимает лайк авторизованного пользователя с комментария.

    Принимает:
        - comment_id (int, в пути) — id комментария.

        Заголовок Authorization: Bearer <access_token> (обязательно) —
        определяет, чей лайк снимается.

    Отдает:
        204 без тела.

    Ошибки:
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.
        - 404 /errors/not-found — если комментария не существует.

    Контракт:
        Идемпотентен: если лайка нет, это не ошибка, ответ тоже 204.
    """
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status = comment.remove_like(session, comment_id, username)
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return no_content()

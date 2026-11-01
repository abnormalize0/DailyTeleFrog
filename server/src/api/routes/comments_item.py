"""
Этот файл служит для хранения API-методов пути /comments/{id}: выбранные поля
данных о комментарии (GET) и его удаление автором (DELETE).
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from ...db import comment as comment_db
from .. import api_info
from ..shared import (
    app,
    get_session,
    json_response,
    no_content,
    optional_auth,
    read_query,
    require_auth,
)


@app.route("/comments/<int:comment_id>", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_comments_item_get(comment_id: int) -> Response:
    """Возвращает выбранные поля данных о комментарии.

    Принимает:
        - comment_id (int, в пути) — id комментария.
        - requested_data (list, query-строка, обязательно, см.
          api_info.comments_item_get) — запрашиваемые поля, параметр повторяется:
          ?requested_data=likes&requested_data=rating. Допустимые значения: likes,
          dislikes, rating, creation_date, is_liked, is_disliked.

        Заголовок Authorization: Bearer <access_token> (опционально) — если
        передан и валиден, используется для is_liked/is_disliked; если не
        передан, эти поля всегда False.

    Отдает:
        200 и JSON с одним ключом на каждое поле из requested_data: likes (int),
        dislikes (int), rating (int = likes - dislikes), creation_date (int, мс с
        1970 года), is_liked (bool), is_disliked (bool). Если комментарий удалён,
        вместо этих полей только is_deleted (True).

    Ошибки:
        - 400 /errors/validation — если requested_data отсутствует или содержит
          имя поля не из допустимого списка.
        - 401 /errors/invalid-token — если заголовок Authorization передан, но
          токен не найден или истёк.
        - 404 /errors/not-found — если комментария не существует или удалена его
          статья.

    Контракт:
        Метод только читает данные, побочных эффектов не имеет. Поле возвращается в
        ответе, только если оно явно запрошено в requested_data.
    """
    parameters, error = read_query(api_info.comments_item_get)
    if error:
        return error
    with get_session() as session:
        username, auth_error = optional_auth(session)
        if auth_error:
            return auth_error
        status, data = backend.get_comment_data(
            session,
            comment_id,
            username,
            parameters["requested_data"],
        )
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return json_response(data)


@app.route("/comments/<int:comment_id>", methods=["DELETE"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_comments_item_delete(comment_id: int) -> Response:
    """Удаляет комментарий авторизованного пользователя.

    Принимает:
        - comment_id (int, в пути) — id комментария.

        Заголовок Authorization: Bearer <access_token> (обязательно) — вызывающий
        должен быть автором комментария.

    Отдает:
        204 без тела.

    Ошибки:
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.
        - 403 /errors/forbidden — если вызывающий не автор комментария.
        - 404 /errors/not-found — если комментария нет или удалена его статья.

    Контракт:
        Удаление мягкое (см. decisions/0005-soft-delete.md): в дереве комментариев
        остаётся заглушка без автора и текста, ответы на комментарий сохраняются.
        Отвечать на удалённый комментарий и ставить на него реакции нельзя. Повторный
        вызов автором не считается ошибкой.
    """
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status = comment_db.delete(session, comment_id, username)
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return no_content()

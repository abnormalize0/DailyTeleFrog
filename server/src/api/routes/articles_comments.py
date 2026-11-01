"""
Этот файл служит для хранения API-метода POST /articles/{id}/comments —
добавление комментария или ответа на комментарий.
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from .. import api_info
from ..shared import app, get_session, json_response, read_body, require_auth


@app.route("/articles/<int:article_id>/comments", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_articles_comments_post(article_id: int) -> Response:
    """Добавляет комментарий (или ответ на комментарий) к статье от имени
    авторизованного пользователя.

    Принимает:
        - article_id (int, в пути) — id статьи, к которой оставляют комментарий.
        JSON-тело запроса, см. api_info.articles_comments_post:
        - text (str, обязательно) — текст комментария.
        - parent (int, обязательно) — id комментария этой же статьи, на который
          отвечают, либо -1, если это комментарий верхнего уровня (не ответ).

        Заголовок Authorization: Bearer <access_token> (обязательно) —
        определяет автора комментария.

    Отдает:
        201, заголовок Location с путём комментария и JSON:
        - id (int) — id созданного комментария.

    Ошибки:
        - 400 /errors/validation — при некорректном теле запроса, если в text нет
          ни одного видимого символа или он длиннее api_info.TEXT_MAX_BYTES байт или если parent не равен -1 и не ссылается на
          существующий неудалённый комментарий именно этой статьи.
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.
        - 404 /errors/not-found — если статьи не существует или она удалена.

    Контракт:
        Комментарий создается с creation_date, выставленным сервером (текущее время
        в миллисекундах с 1970 года).
    """
    parameters, error = read_body(api_info.articles_comments_post)
    if error:
        return error
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status, comment_id = backend.add_comment(
            session=session,
            article_id=article_id,
            username=username,
            comment_text=parameters["text"],
            parent=parameters["parent"],
        )
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return json_response(
            {"id": comment_id}, 201, location=f"/comments/{comment_id}"
        )

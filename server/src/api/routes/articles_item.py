"""
Этот файл служит для хранения API-метода GET /articles/{id} — полная информация
о статье.
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from ..shared import app, get_session, json_response, optional_auth


@app.route("/articles/<int:article_id>", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_articles_item_get(article_id: int) -> Response:
    """Возвращает полную информацию о статье для отображения страницы статьи.

    Принимает:
        - article_id (int, в пути) — id запрашиваемой статьи.

        Заголовок Authorization: Bearer <access_token> (опционально) — если
        передан и валиден, используется для полей is_liked/is_disliked; если
        не передан, статья отдаётся как для неавторизованного пользователя
        (is_liked/is_disliked всегда False).

    Отдает:
        200 и JSON:
        - article (dict) со следующими ключами:
            - creation_date (int) — дата публикации, мс с 1970 года.
            - author_preview (dict) — предпоказ автора: avatar, nickname, description, username.
            - title (str), body (dict) — заголовок и тело статьи (структура тела —
              как было передано при публикации).
            - preview (dict) — контент предпоказа (как было передано при публикации).
            - likes (int), dislikes (int), rating (int = likes - dislikes).
            - comments_count (int).
            - comments (list) — дерево комментариев статьи.
            - is_liked (bool), is_disliked (bool) — лайкнул/дизлайкнул ли статью вызывающий.
            - tags (list[str]).

    Ошибки:
        - 401 /errors/invalid-token — если заголовок Authorization передан, но
          токен не найден или истёк.
        - 404 /errors/not-found — если статьи с таким id не существует.

    Контракт:
        Метод только читает данные, побочных эффектов не имеет.
    """
    with get_session() as session:
        username, auth_error = optional_auth(session)
        if auth_error:
            return auth_error
        status, article = backend.get_article(session, article_id, username)
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return json_response({"article": article})

"""
Этот файл служит для хранения API-методов пути /articles/{id}: полная информация
о статье (GET) и её удаление автором (DELETE).
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from ...db import article as article_db
from ..shared import (
    app,
    get_session,
    json_response,
    no_content,
    optional_auth,
    require_auth,
)


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
            - author_preview (dict) — предпоказ автора: avatar, nickname, description,
              username, is_deleted (False). Если аккаунт автора удалён, только
              is_deleted (True).
            - title (str), body (dict) — заголовок и тело статьи (структура тела —
              как было передано при публикации).
            - preview (dict) — контент предпоказа (как было передано при публикации).
            - likes (int), dislikes (int), rating (int = likes - dislikes).
            - comments_count (int) — без удалённых комментариев.
            - comments (list) — дерево комментариев статьи. Каждый узел: id, parent_id
              (-1 у верхнего уровня), is_deleted, answers (вложенные ответы) и, только
              у неудалённого комментария, author_username и text.
            - is_liked (bool), is_disliked (bool) — лайкнул/дизлайкнул ли статью вызывающий.
            - tags (list[str]).

    Ошибки:
        - 401 /errors/invalid-token — если заголовок Authorization передан, но
          токен не найден или истёк.
        - 404 /errors/not-found — если статьи с таким id не существует или она удалена.

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


@app.route("/articles/<int:article_id>", methods=["DELETE"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_articles_item_delete(article_id: int) -> Response:
    """Удаляет статью авторизованного пользователя.

    Принимает:
        - article_id (int, в пути) — id статьи.

        Заголовок Authorization: Bearer <access_token> (обязательно) — вызывающий
        должен быть автором статьи.

    Отдает:
        204 без тела.

    Ошибки:
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.
        - 403 /errors/forbidden — если вызывающий не автор статьи.
        - 404 /errors/not-found — если статьи нет, либо она удалена и вызывающий не
          её автор.

    Контракт:
        Удаление мягкое (см. decisions/0005-soft-delete.md): статья и всё, что внутри
        неё (комментарии, лайки, теги, предпоказ), перестают быть доступны в API.
        Повторный вызов автором не считается ошибкой.
    """
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status = article_db.delete(session, article_id, username)
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return no_content()

"""
Этот файл служит для хранения API-метода GET /articles/{id}/data — выбранные поля
данных о статье.
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from .. import api_info
from ..shared import app, get_session, json_response, optional_auth, read_query


@app.route("/articles/<int:article_id>/data", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_articles_data_get(article_id: int) -> Response:
    """Возвращает выбранные поля данных о статье.

    Принимает:
        - article_id (int, в пути) — id статьи.
        - requested_data (list, query-строка, обязательно, см.
          api_info.articles_data_get) — запрашиваемые поля, параметр повторяется:
          ?requested_data=likes&requested_data=rating. Допустимые значения: likes,
          dislikes, rating, comments_count, creation_date, is_liked, is_disliked.

        Заголовок Authorization: Bearer <access_token> (опционально) — если
        передан и валиден, используется для is_liked/is_disliked; если не
        передан, эти поля всегда False.

    Отдает:
        200 и JSON с одним ключом на каждое поле из requested_data: likes (int),
        dislikes (int), rating (int = likes - dislikes), comments_count (int),
        creation_date (int, мс с 1970 года), is_liked (bool),
        is_disliked (bool).

    Ошибки:
        - 400 /errors/validation — если requested_data отсутствует или содержит
          имя поля не из допустимого списка.
        - 401 /errors/invalid-token — если заголовок Authorization передан, но
          токен не найден или истёк.
        - 404 /errors/not-found — если статьи не существует.

    Контракт:
        Метод только читает данные, побочных эффектов не имеет. Поле возвращается в
        ответе, только если оно явно запрошено в requested_data.
    """
    parameters, error = read_query(api_info.articles_data_get)
    if error:
        return error
    with get_session() as session:
        username, auth_error = optional_auth(session)
        if auth_error:
            return auth_error
        status, data = backend.get_article_data(
            session,
            article_id,
            username,
            parameters["requested_data"],
        )
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return json_response(data)

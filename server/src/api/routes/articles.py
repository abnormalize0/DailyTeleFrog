"""
Этот файл служит для хранения API-методов пути /articles: публикация статьи
(POST) и лента статей с превью (GET).
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from .. import api_info
from ..shared import (
    app,
    error_response,
    fill_default,
    get_session,
    json_response,
    optional_auth,
    read_body,
    read_query,
    require_auth,
)


@app.route("/articles", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_articles_post() -> Response:
    """Публикует новую статью от имени авторизованного пользователя.

    Принимает (JSON-тело запроса, см. api_info.articles_post):
        - title (str, обязательно) — заголовок статьи.
        - body (dict, обязательно) — тело статьи в произвольной, определяемой
          frontend'ом структуре. Сервер не заглядывает внутрь и не меняет её,
          только сериализует в JSON-строку для хранения и разбирает обратно
          при чтении.
        - preview (dict, обязательно) — контент для предпоказа статьи в ленте,
          также произвольной структуры и без интерпретации сервером.
        - tags (list, опционально, по умолчанию []) — список тегов статьи.

        Заголовок Authorization: Bearer <access_token> (обязательно) —
        определяет автора статьи.

    Отдает:
        201, заголовок Location с путём статьи и JSON:
        - article_id (int) — id созданной статьи.

    Ошибки:
        - 400 /errors/validation — если в теле запроса отсутствует обязательное
          поле, у поля неверный тип, значение длиннее предела из
          api_info.articles_post (список полей в `errors`) или в tags есть
          одинаковые теги. Одинаковость определяет БД: сейчас теги, которые
          отличаются только регистром, тоже считаются одинаковыми.
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.

    Контракт:
        Статья создается в таблице articles с author_username = владелец токена и
        creation_date, выставленным сервером (текущее время в миллисекундах с 1970 года).
        preview сохраняется в отдельной таблице article_preview. Для каждого тега из
        tags создается отдельная строка в article_tags; порядок тегов не сохраняется.
        Если теги повторяются, статья не создаётся.
        Метод ничего не проверяет насчет уникальности title и не ограничивает
        количество статей на пользователя.
    """
    parameters, error = read_body(api_info.articles_post)
    if error:
        return error
    parameters = fill_default(parameters, api_info.articles_post)
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status, article_id = backend.post_article(
            session,
            username,
            parameters["title"],
            parameters["body"],
            parameters["preview"],
            parameters["tags"],
        )
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return json_response(
            {"article_id": article_id}, 201, location=f"/articles/{article_id}"
        )


@app.route("/articles", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_articles_get() -> Response:
    """Возвращает одну или несколько страниц ленты статей с превью каждой статьи.

    Принимает (query-строка, см. api_info.articles_get; список передаётся
    повторением параметра: ?indexes=0&indexes=1):
        - indexes (list[int], обязательно) — номера запрашиваемых страниц (нумерация
          с 0), каждая страница содержит до config.articles_per_page статей.
        - include_nonsub (bool: true/false, опционально, по умолчанию true) — если
          явно передано false, в выборку попадают только статьи от авторов/с тегами,
          на которые вызывающий подписан (см. Контракт).
        - sort_column (str, опционально) — "creation_date" или "rating"; по умолчанию
          "creation_date".
        - sort_direction (str, опционально) — "descending" или "ascending"; по умолчанию
          "descending".
        - upper_date, lower_date (int, опционально) — верхняя/нижняя граница
          creation_date (мс с 1970 года), применяются только когда sort_column == "creation_date".
        - upper_rating, lower_rating (int, опционально) — верхняя/нижняя граница rating,
          применяются только когда sort_column == "rating".
        - include_tags, include_authors (list, опционально) — ограничивают выборку:
          include_tags — статья должна содержать ВСЕ перечисленные теги;
          include_authors — автор статьи должен быть одним из перечисленных.
        - exclude_tags, exclude_authors (list, опционально) — исключают из выборки статьи
          с любым из перечисленных тегов или любым из перечисленных авторов.

        Заголовок Authorization: Bearer <access_token> (опционально) — если
        передан и валиден, влияет на автоматическое исключение заблокированных
        тегов/авторов, на фильтр include_nonsub и на поля is_liked/is_disliked;
        если не передан, лента формируется как для неавторизованного пользователя.

    Отдает:
        200 и JSON:
        - pages (dict) — ключи совпадают с запрошенными indexes (в виде строк, так
          как это JSON), значение — список превью статей страницы в порядке
          сортировки. Превью статьи содержит: id, title, creation_date,
          author_preview (avatar, nickname, description, username, is_deleted; у
          удалённого аккаунта только is_deleted), preview_content,
          likes, dislikes, rating, comments_count, tags, is_liked, is_disliked.

    Ошибки:
        - 400 /errors/validation — при неверных параметрах, в том числе если
          sort_column или sort_direction не равны одному из допустимых значений.
        - 401 /errors/invalid-token — если заголовок Authorization передан, но
          токен не найден или истёк.

    Контракт:
        Для авторизованного вызывающего из выборки всегда убираются статьи от
        заблокированных им авторов и статьи с заблокированными им тегами (это
        происходит независимо от exclude_tags/exclude_authors и не отключается).
        Если include_nonsub == False, дополнительно остаются только статьи, автор
        которых или хотя бы один тег которых входит в подписки вызывающего; если у
        него вообще нет подписок, выборка будет пустой. Страница с индексом,
        для которого не хватает статей (или который выходит за пределы отфильтрованной
        выборки), возвращается как пустой список, а не как ошибка.
    """
    parameters, error = read_query(api_info.articles_get)
    if error:
        return error
    parameters = fill_default(parameters, api_info.articles_get)

    sort_column = parameters.get("sort_column")
    if sort_column and sort_column not in ["creation_date", "rating"]:
        return error_response(
            request_status.ErrorType.InvalidParameters,
            'Parameter "sort_column" must have value "creation_date" or "rating"',
        )

    sort_direction = parameters.get("sort_direction")
    if sort_direction and sort_direction not in ["descending", "ascending"]:
        return error_response(
            request_status.ErrorType.InvalidParameters,
            'Parameter "sort_direction" must have value "descending" or "ascending"',
        )

    include = {}
    if parameters.get("include_tags"):
        include["tags"] = parameters["include_tags"]
    if parameters.get("include_authors"):
        include["authors"] = parameters["include_authors"]

    exclude = {}
    if parameters.get("exclude_tags"):
        exclude["tags"] = parameters["exclude_tags"]
    if parameters.get("exclude_authors"):
        exclude["authors"] = parameters["exclude_authors"]

    if sort_column == "rating":
        bounds = {
            "upper": parameters.get("upper_rating"),
            "lower": parameters.get("lower_rating"),
        }
    else:
        bounds = {
            "upper": parameters.get("upper_date"),
            "lower": parameters.get("lower_date"),
        }

    with get_session() as session:
        username, auth_error = optional_auth(session)
        if auth_error:
            return auth_error
        status, pages = backend.pages_get(
            session,
            username,
            parameters["indexes"],
            parameters["include_nonsub"],
            sort_column,
            sort_direction,
            include,
            exclude,
            bounds,
        )
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return json_response({"pages": pages})

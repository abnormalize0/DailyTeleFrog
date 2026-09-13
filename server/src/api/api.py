"""
Этот файл служит для хранения логики предобработки пользовательских запросов.
В предобработку входит проверка необходимых заголовков, параметров запроса и тела запроса при наличии.
В рамках предобработки этих полей выполняется преобразования к необходимым типам данных.

Пометка для добавления нового API метода:
1. Названия методов формируются следующим образом: api_%METHOD_NAME%_%REQUEST_TYPE%
Префикс api_ обрабатывается в тестах, поэтому он обязателен.
Остальная часть названия метода позволяет избежать дублирования названий функций.
2. Для каждого метода должен присутствовать тест в файле /server/test/test_api.py
и ответ на запрос OPTIONS в файле /server/src/api_info.py
3. Каждый запрос должен принимать на вход username заголовок.
По договоренности считаем, что в этом заголвке указан автор запроса.
Значение -1 характеризует неавторизванного пользователя.
4. Каждый API метод обязан возвращать статус операции.
5. Последовательность API методов должна быть одинаковой для этого файла, документации, тестов и запросов OPTIONS.
6. Каждый запрос должен быть декорирован таймером и логгированием принимаемых аргументов.
Логгирование аргументов позволит облегчить поиск проблем, когда такие возникнут.
Таймер позволит иметь конкретные значения времени выполнения запроса, что облегчит решение проблем аля "ВСЕ ТОРМОЗИТ!!!"
7. Для API методов типа POST обязательно должно присутсвовать тело запроса.
В этом теле располагаются данные, которые будут добавлены на сервер. Остальные параметры перечислены в заголовках.
"""

from flask import Flask, request
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import json
import os
import builtins

from .. import backend
from .. import request_status
from .. import config
from .. import log
from . import api_info

app = Flask(__name__)
app.register_blueprint(api_info.info)
cors = CORS(app)

global db_url


def check_list_elements(data, pattern):
    """Проверяет, что каждый элемент data есть среди допустимых имен в pattern.

    Args:
        data: список значений из запроса.
        pattern: список допустимых элементов вида {"name": ...}.

    Returns:
        `True`, если все элементы data найдены в pattern, иначе `False`.
    """
    for element in data:
        is_found = False
        for requested_element in pattern:
            if element != requested_element["name"]:
                continue
            else:
                is_found = True
        if is_found == False:
            return False
    return True


def check_structure(data, pattern):
    """Проверяет тело запроса data на соответствие ожидаемой структуре pattern.

    Args:
        data: тело запроса.
        pattern: описание ожидаемых полей из api_info.

    Returns:
        Кортеж (bool, `ErrorType`):
            - (`True`, `None`) — data соответствует pattern.
            - (`False`, OptionError) — отсутствует обязательное поле.
            - (`False`, ValueError) — у поля неверный тип значения.
    """
    for element in pattern:
        if element["is_required"] == False:
            if element["name"] not in data:
                continue
        if element["name"] not in data:
            return False, request_status.ErrorType.OptionError
        if not type(data[element["name"]]) == getattr(builtins, element["type"], None):
            return False, request_status.ErrorType.ValueError
        if element["type"] == "json":
            is_ok, error = check_structure(data[element["name"]], element["structure"])
            if not is_ok:
                return False, error
        if element["type"] == "list":
            if element["structure"]:
                is_ok = check_list_elements(data[element["name"]], element["structure"])
                if not is_ok:
                    return False, request_status.ErrorType.ValueError
    return True, None


def fill_default(data, pattern):
    """Дополняет data значениями по умолчанию для отсутствующих полей.

    Args:
        data: тело запроса.
        pattern: описание полей из api_info.

    Returns:
        data, дополненный значениями из api_info.type_defaults там, где поле
        отсутствовало.
    """
    for value in pattern:
        if value["name"] not in data:
            data[value["name"]] = api_info.type_defaults[value["type"]]
    return data


@app.route("/article", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_post():
    """Публикует новую статью от имени указанного пользователя.

    Принимает (JSON-тело запроса, см. api_info.article_post):
        - username (str, обязательно) — автор статьи.
        - title (str, обязательно) — заголовок статьи.
        - body (dict, обязательно) — тело статьи в произвольной, определяемой
          frontend'ом структуре. Сервер не заглядывает внутрь и не меняет её,
          только сериализует в JSON-строку для хранения и разбирает обратно
          при чтении.
        - preview (dict, обязательно) — контент для предпоказа статьи в ленте,
          также произвольной структуры и без интерпретации сервером.
        - tags (list, опционально, по умолчанию []) — список тегов статьи.

    Отдает (JSON):
        - status (dict) — статус операции.
        - article_id (int) — id созданной статьи (присутствует только при status.type == "OK").

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — если в теле
          запроса отсутствует обязательное поле или у присутствующего поля неверный тип.
        - ValueError "Unlogged user cannot use this method" — если username == "unlogged_user":
          неавторизованный пользователь не может публиковать статьи.

    Контракт:
        Статья создается в таблице articles с author_username = username и
        creation_date, выставленным сервером (текущее время в миллисекундах с 1970 года).
        preview сохраняется в отдельной таблице article_preview. Для каждого тега из
        tags создается отдельная строка в article_tags; порядок тегов не сохраняется.
        Метод ничего не проверяет насчет уникальности title и не ограничивает
        количество статей на пользователя.
    """
    is_right_structure, error = check_structure(request.json, api_info.article_post)
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    if request.json["username"] == "unlogged_user":
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=request_status.ErrorType.ValueError,
                        msg="Unlogged user cannot use this method",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.article_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, article_id = backend.post_article(
            session,
            parameters["username"],
            parameters["title"],
            parameters["body"],
            parameters["preview"],
            parameters["tags"],
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps(
            {
                "status": dict(request_status.Status(request_status.StatusType.OK)),
                "article_id": article_id,
            }
        )


@app.route("/article", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_get():
    """Возвращает полную информацию о статье для отображения страницы статьи.

    Принимает (JSON-тело запроса, см. api_info.article_get):
        - username (str, обязательно) — пользователь, от чьего имени просматривается
          статья (используется для полей is_liked/is_disliked); для неавторизованного
          пользователя передается "unlogged_user".
        - article_id (int, обязательно) — id запрашиваемой статьи.

    Отдает (JSON):
        - status (dict) — статус операции.
        - article (dict, только при status.type == "OK") со следующими ключами:
            - creation_date (int) — дата публикации, мс с 1970 года.
            - author_preview (dict) — предпоказ автора: avatar, nickname, description, username.
            - title (str), body (dict) — заголовок и тело статьи (структура тела —
              как было передано при публикации).
            - preview (dict) — контент предпоказа (как было передано при публикации).
            - likes (int), dislikes (int), rating (int = likes - dislikes).
            - comments_count (int).
            - comments (list) — дерево комментариев статьи (см. article/comment).
            - is_liked (bool), is_disliked (bool) — лайкнул/дизлайкнул ли статью username.
            - tags (list[str]).

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "Cannot find article with id: {article_id}" — если статьи с таким id не существует.

    Контракт:
        Метод только читает данные, побочных эффектов не имеет. Если username не лайкал/не
        дизлайкал статью, соответствующие поля будут False, включая случай
        username == "unlogged_user" (для него is_liked/is_disliked всегда False).
    """
    is_right_structure, error = check_structure(request.json, api_info.article_get)
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.article_get)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, article = backend.get_article(
            session, parameters["article_id"], parameters["username"]
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps(
            {
                "status": dict(request_status.Status(request_status.StatusType.OK)),
                "article": article,
            }
        )


@app.route("/article/like", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_like_post():
    """Ставит или убирает лайк пользователя на статье (toggle).

    Принимает (JSON-тело запроса, см. api_info.article_like_post):
        - username (str, обязательно) — кто ставит лайк.
        - article_id (int, обязательно) — id статьи.

    Отдает (JSON):
        - status (dict) — статус операции. Других полей нет.

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "Cannot find article with id: {article_id}" — если статьи не существует.
        - ValueError "User tries to like or dislike their own article" — если username
          является автором статьи.

    Контракт:
        Если username уже лайкал статью — лайк снимается. Если нет — лайк ставится,
        а существующий дизлайк этого же пользователя на этой статье автоматически
        снимается (лайк и дизлайк взаимоисключающие).
    """
    is_right_structure, error = check_structure(
        request.json, api_info.article_like_post
    )
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.article_like_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.article_like(
            session, parameters["article_id"], parameters["username"]
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps(
            {"status": dict(request_status.Status(request_status.StatusType.OK))}
        )


@app.route("/article/dislike", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_dislike_post():
    """Ставит или убирает дизлайк пользователя на статье (toggle).

    Принимает (JSON-тело запроса, см. api_info.article_dislike_post):
        - username (str, обязательно) — кто ставит дизлайк.
        - article_id (int, обязательно) — id статьи.

    Отдает (JSON):
        - status (dict) — статус операции. Других полей нет.

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "Cannot find article with id: {article_id}" — если статьи не существует.
        - ValueError "User tries to like or dislike their own article" — если username
          является автором статьи.

    Контракт:
        Если username уже дизлайкал статью — дизлайк снимается. Если нет — дизлайк
        ставится, а существующий лайк этого же пользователя на этой статье автоматически
        снимается (лайк и дизлайк взаимоисключающие).
    """
    is_right_structure, error = check_structure(
        request.json, api_info.article_dislike_post
    )
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.article_dislike_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.article_dislike(
            session, parameters["article_id"], parameters["username"]
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps(
            {"status": dict(request_status.Status(request_status.StatusType.OK))}
        )


@app.route("/article/comment", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_comment_post():
    """Добавляет комментарий (или ответ на комментарий) к статье.

    Принимает (JSON-тело запроса, см. api_info.article_comment_post):
        - username (str, обязательно) — автор комментария.
        - article_id (int, обязательно) — id статьи, к которой оставляют комментарий.
        - text (str, обязательно) — текст комментария.
        - root (int, обязательно) — id комментария этой же статьи, на который отвечают,
          либо -1, если это комментарий верхнего уровня (не ответ).

    Отдает (JSON):
        - status (dict) — статус операции.
        - id (int) — id созданного комментария (присутствует только при status.type == "OK").

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "Cannot find comment with id: {root}" — если root не равен -1 и не
          ссылается на существующий комментарий именно этой статьи.

    Контракт:
        Комментарий создается с creation_date, выставленным сервером (текущее время
        в миллисекундах с 1970 года).
    """
    is_right_structure, error = check_structure(
        request.json, api_info.article_comment_post
    )
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.article_comment_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, id = backend.add_comment(
            session=session,
            article_id=parameters["article_id"],
            username=parameters["username"],
            comment_text=parameters["text"],
            root=parameters["root"],
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps(
            {
                "status": dict(request_status.Status(request_status.StatusType.OK)),
                "id": id,
            }
        )


@app.route("/article/comment/like", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_comment_like_post():
    """Ставит или убирает лайк пользователя на комментарии (toggle).

    Принимает (JSON-тело запроса, см. api_info.article_comment_like_post):
        - username (str, обязательно) — кто ставит лайк.
        - comment_id (int, обязательно) — id комментария.

    Отдает (JSON):
        - status (dict) — статус операции. Других полей нет.

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "Cannot find comment with id: {comment_id}" — если комментария не существует.
        - ValueError "User tries to like or dislike their own comment" — если username
          является автором комментария.

    Контракт:
        Если username уже лайкал комментарий — лайк снимается. Если нет — лайк ставится,
        а существующий дизлайк этого же пользователя на этом комментарии автоматически
        снимается (лайк и дизлайк взаимоисключающие).
    """
    is_right_structure, error = check_structure(
        request.json, api_info.article_comment_like_post
    )
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.article_comment_like_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.comment_like(
            session, parameters["comment_id"], parameters["username"]
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps(
            {"status": dict(request_status.Status(request_status.StatusType.OK))}
        )


@app.route("/article/comment/dislike", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_comment_dislike_post():
    """Ставит или убирает дизлайк пользователя на комментарии (toggle).

    Принимает (JSON-тело запроса, см. api_info.article_comment_dislike_post):
        - username (str, обязательно) — кто ставит дизлайк.
        - comment_id (int, обязательно) — id комментария.

    Отдает (JSON):
        - status (dict) — статус операции. Других полей нет.

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "Cannot find comment with id: {comment_id}" — если комментария не существует.
        - ValueError "User tries to like or dislike their own comment" — если username
          является автором комментария.

    Контракт:
        Если username уже дизлайкал комментарий — дизлайк снимается. Если нет — дизлайк
        ставится, а существующий лайк этого же пользователя на этом комментарии
        автоматически снимается (лайк и дизлайк взаимоисключающие).
    """
    is_right_structure, error = check_structure(
        request.json, api_info.article_comment_dislike_post
    )
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.article_comment_dislike_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.comment_dislike(
            session, parameters["comment_id"], parameters["username"]
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps(
            {"status": dict(request_status.Status(request_status.StatusType.OK))}
        )


@app.route("/article/comment/data", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_comment_data_get():
    """Возвращает выбранные поля данных о комментарии.

    Принимает (JSON-тело запроса, см. api_info.article_comment_data_get):
        - username (str, обязательно) — пользователь, от чьего имени запрашиваются
          данные (используется для is_liked/is_disliked).
        - comment_id (int, обязательно) — id комментария.
        - requested_data (list, обязательно) — список запрашиваемых полей. Допустимые
          значения: likes, dislikes, rating, creation_date, is_liked, is_disliked.

    Отдает (JSON):
        - status (dict) — статус операции.
        - по одному ключу для каждого поля из requested_data (присутствуют только
          при status.type == "OK"): likes (int), dislikes (int), rating (int = likes -
          dislikes), creation_date (int, мс с 1970 года), is_liked (bool), is_disliked (bool).

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном
          теле запроса или если requested_data содержит имя поля не из допустимого списка.
        - ValueError "Cannot find comment with id: {comment_id}" — если комментария не существует.

    Контракт:
        Метод только читает данные, побочных эффектов не имеет. Поле возвращается в
        ответе, только если оно явно запрошено в requested_data.
    """
    is_right_structure, error = check_structure(
        request.json, api_info.article_comment_data_get
    )
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.article_comment_data_get)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, data = backend.get_comment_data(
            session,
            parameters["comment_id"],
            parameters["username"],
            parameters["requested_data"],
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        answer = {"status": dict(status)}
        answer.update(data)
        return json.dumps(answer)


@app.route("/article/data", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_data_get():
    """Возвращает выбранные поля данных о статье.

    Принимает (JSON-тело запроса, см. api_info.article_data_get):
        - username (str, обязательно) — пользователь, от чьего имени запрашиваются
          данные (используется для is_liked/is_disliked).
        - article_id (int, обязательно) — id статьи.
        - requested_data (list, обязательно) — список запрашиваемых полей. Допустимые
          значения: likes, dislikes, rating, comments_count, creation_date, is_liked, is_disliked.

    Отдает (JSON):
        - status (dict) — статус операции.
        - по одному ключу для каждого поля из requested_data (присутствуют только
          при status.type == "OK"): likes (int), dislikes (int), rating (int = likes -
          dislikes), comments_count (int), creation_date (int, мс с 1970 года),
          is_liked (bool), is_disliked (bool).

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном
          теле запроса или если requested_data содержит имя поля не из допустимого списка.
        - ValueError "Cannot find article with id: {article_id}" — если статьи не существует.

    Контракт:
        Метод только читает данные, побочных эффектов не имеет. Поле возвращается в
        ответе, только если оно явно запрошено в requested_data.
    """
    is_right_structure, error = check_structure(request.json, api_info.article_data_get)
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.article_data_get)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, data = backend.get_article_data(
            session,
            parameters["article_id"],
            parameters["username"],
            parameters["requested_data"],
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        answer = {"status": dict(status)}
        answer.update(data)
        return json.dumps(answer)


@app.route("/pages", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_pages_get():
    """Возвращает одну или несколько страниц ленты статей с превью каждой статьи.

    Принимает (JSON-тело запроса, см. api_info.pages_get):
        - username (str, обязательно) — пользователь, для которого формируется лента;
          для неавторизованного пользователя передается "unlogged_user". Влияет на
          автоматическое исключение заблокированных тегов/авторов, на фильтр
          include_nonsub и на поля is_liked/is_disliked в превью.
        - indexes (list[int], обязательно) — номера запрашиваемых страниц (нумерация
          с 0), каждая страница содержит до config.articles_per_page статей.
        - include_nonsub (bool, опционально, по умолчанию True) — если явно передано
          False, в выборку попадают только статьи от авторов/с тегами, на которые
          username подписан (см. Контракт).
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

    Отдает (JSON):
        - status (dict) — статус операции.
        - pages (dict, только при status.type == "OK") — ключи совпадают с запрошенными
          indexes (в виде строк, так как это JSON), значение — список превью статей
          страницы в порядке сортировки. Превью статьи содержит: id, title,
          creation_date, author_preview (avatar, nickname, description, username),
          preview_content, likes, dislikes, rating, comments_count, tags, is_liked, is_disliked.

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "Parameter \"sort_column\" must have value \"creation_date\" or \"rating\"" —
          если sort_column передан и не равен одному из этих двух значений.
        - ValueError "Parameter \"sort_direction\" must have value \"descending\" or \"ascending\"" —
          если sort_direction передан и не равен одному из этих двух значений.

    Контракт:
        Для авторизованного username (не "unlogged_user") из выборки всегда убираются
        статьи от заблокированных им авторов и статьи с заблокированными им тегами
        (это происходит независимо от exclude_tags/exclude_authors и не отключается).
        Если include_nonsub == False, дополнительно остаются только статьи, автор
        которых или хотя бы один тег которых входит в подписки username; если у
        username вообще нет подписок, выборка будет пустой. Страница с индексом,
        для которого не хватает статей (или который выходит за пределы отфильтрованной
        выборки), возвращается как пустой список, а не как ошибка.
    """
    is_right_structure, error = check_structure(request.json, api_info.pages_get)
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.pages_get)

    sort_column = parameters.get("sort_column")
    if sort_column and sort_column not in ["creation_date", "rating"]:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=request_status.ErrorType.ValueError,
                        msg='Parameter "sort_column" must have value "creation_date" or "rating"',
                    )
                )
            }
        )

    sort_direction = parameters.get("sort_direction")
    if sort_direction and sort_direction not in ["descending", "ascending"]:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=request_status.ErrorType.ValueError,
                        msg='Parameter "sort_direction" must have value "descending" or "ascending"',
                    )
                )
            }
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

    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, pages = backend.pages_get(
            session,
            parameters["username"],
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
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps({"status": dict(status), "pages": pages})


@app.route("/users", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_post():
    """Регистрирует нового пользователя.

    Принимает (JSON-тело запроса, см. api_info.users_post):
        - username (str, обязательно) — уникальный идентификатор пользователя,
          используемый во всех остальных методах API.
        - nickname (str, обязательно) — отображаемое имя.
        - email (str, обязательно).
        - password (str, обязательно) — хранится как есть, без хэширования.
        - avatar (str, опционально) — ссылка на аватар.
        - description (str, опционально) — текстовое описание профиля.

    Отдает (JSON):
        - status (dict) — статус операции. Других полей нет.

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "User with username {username} already exists" — если пользователь
          с таким username уже зарегистрирован.
        - ValueError "User with email {email} already exists" — если пользователь
          с таким email уже зарегистрирован.

    Контракт:
        username уникален и является первичным ключом пользователя (используется
        во всех внешних ключах, ссылающихся на пользователя). email также уникален.
        При регистрации автоматически проставляются creation_date (текущее время в
        миллисекундах с 1970 года) и запись в истории имен (name_history) с текущим
        nickname. Рейтинг нового пользователя равен 0 (вычисляется на лету по лайкам/
        дизлайкам его статей и комментариев, отдельно не хранится).
    """
    is_right_structure, error = check_structure(request.json, api_info.users_post)
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )

    parameters = fill_default(request.json, api_info.users_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.add_user(session, parameters)
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps(
            {"status": dict(request_status.Status(request_status.StatusType.OK))}
        )


@app.route("/users/data", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_data_get():
    """Возвращает выбранные поля данных о пользователе (для страницы профиля).

    Принимает (JSON-тело запроса, см. api_info.users_data_get):
        - username (str, обязательно) — пользователь, чей профиль запрашивается.
          Не может быть "unlogged_user".
        - requested_data (list, обязательно) — список запрашиваемых полей. Допустимые
          значения: nickname, email, name_history, avatar, sub_tags, blocked_tags,
          sub_users, blocked_users, description, creation_date, rating.

    Отдает (JSON):
        - status (dict) — статус операции.
        - по одному ключу для каждого поля из requested_data (присутствуют только
          при status.type == "OK"): nickname (str), email (str), name_history
          (list[str] — все прежние nickname пользователя, включая текущий),
          avatar (str), sub_tags/blocked_tags (list[str]), sub_users/blocked_users
          (list[str] — username'ы), description (str), creation_date (int, мс с
          1970 года), rating (int).

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном
          теле запроса или если requested_data содержит имя поля не из допустимого списка.
        - ValueError "Unlogged user cannot use this method" — если username == "unlogged_user".

    Контракт:
        Метод только читает данные, побочных эффектов не имеет. Поле возвращается в
        ответе, только если оно явно запрошено в requested_data.
    """
    is_right_structure, error = check_structure(request.json, api_info.users_data_get)
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    if request.json["username"] == "unlogged_user":
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=request_status.ErrorType.ValueError,
                        msg="Unlogged user cannot use this method",
                    )
                )
            }
        )
    parameters = fill_default(request.json, api_info.users_data_get)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, data = backend.get_user_data(
            session, parameters["username"], parameters["requested_data"]
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        answer = {"status": dict(status)}
        answer.update(data)
        return json.dumps(answer)


@app.route("/users/data", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_data_post():
    """Частично обновляет данные пользователя: только те поля, что переданы в запросе.

    Принимает (JSON-тело запроса, см. api_info.users_data_post):
        - username (str, обязательно) — кого обновляем. Не может быть "unlogged_user".
        - nickname (str, опционально).
        - email (str, опционально).
        - avatar (str, опционально).
        - description (str, опционально).
        - sub-tags (list[str], опционально) — теги, на которые username подписывается.
        - blocked-tags (list[str], опционально) — теги, которые username блокирует.
        - sub-users (list[str], опционально) — username'ы, на которых username подписывается.
        - blocked-users (list[str], опционально) — username'ы, которых username блокирует.

    Отдает (JSON):
        - status (dict) — статус операции. Других полей нет.

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "Unlogged user cannot use this method" — если username == "unlogged_user".

    Контракт:
        Обрабатываются только переданные в запросе поля, остальные остаются без
        изменений. Если передан nickname, он также добавляется в name_history
        пользователя. Подписка на тег/автора из sub-tags/sub-users автоматически
        снимает соответствующую блокировку (и наоборот для blocked-tags/blocked-users) —
        подписка и блокировка одного и того же тега/автора взаимоисключающие.
        Весь запрос применяется атомарно: если любое из полей (включая отдельный
        элемент списков sub-tags/blocked-tags/sub-users/blocked-users) вызывает
        ошибку, ни одно изменение из этого запроса не сохраняется.
    """
    is_right_structure, error = check_structure(request.json, api_info.users_data_post)
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    if request.json["username"] == "unlogged_user":
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=request_status.ErrorType.ValueError,
                        msg="Unlogged user cannot use this method",
                    )
                )
            }
        )
    # parameters = fill_default(request.json, api_info.users_data_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        username = request.json.pop("username")
        status = backend.update_user_info(session, username, request.json)
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps({"status": dict(status)})


@app.route("/users/password", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_password_post():
    """Меняет пароль пользователя.

    Принимает (JSON-тело запроса, см. api_info.user_password_post):
        - username (str, обязательно) — не может быть "unlogged_user".
        - previous_password (str, обязательно) — текущий пароль пользователя.
        - new_password (str, обязательно) — новый пароль.

    Отдает (JSON):
        - status (dict) — статус операции. Других полей нет.

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "Unlogged user cannot use this method" — если username == "unlogged_user".
        - ValueError "Incorrect password!" — если previous_password не совпадает с текущим
          паролем пользователя (в том числе если такого username вообще не существует).

    Контракт:
        Пароль обновляется, только если previous_password верно указан. Новый пароль
        сохраняется как есть, без хэширования.
    """
    is_right_structure, error = check_structure(
        request.json, api_info.user_password_post
    )
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )
    if request.json["username"] == "unlogged_user":
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=request_status.ErrorType.ValueError,
                        msg="Unlogged user cannot use this method",
                    )
                )
            }
        )
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        username = request.json.pop("username")
        previous_password = request.json.pop("previous_password")
        new_password = request.json.pop("new_password")
        status = backend.change_password(
            session, previous_password, new_password, username
        )
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps({"status": dict(status)})


@app.route("/login", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_login_get():
    """Проверяет пароль пользователя (используется при входе в систему).

    Принимает (JSON-тело запроса, см. api_info.login_get):
        - username (str, опционально) — по кому искать пользователя.
        - email (str, опционально) — по кому искать пользователя (альтернатива username).
        - password (str, обязательно) — пароль для проверки.

        Должно быть указано ровно одно из username/email.

    Отдает (JSON):
        - status (dict) — статус операции.
        - is-correct (bool, только при status.type == "OK") — True, если password
          совпадает с паролем найденного пользователя.

    Ошибки:
        - OptionError/ValueError "Wrong request parameters structure." — при некорректном теле запроса.
        - ValueError "User cant login via username and email." — если переданы и
          username, и email одновременно.
        - ValueError "User must login via username or email." — если не передано
          ни username, ни email.
        - ValueError "Unlogged user cannot use this method" — если username == "unlogged_user".

    Контракт:
        Если пользователь с указанным username/email не найден, метод не считается
        ошибкой: status.type остается "OK", а is-correct — False.
    """
    is_right_structure, error = check_structure(request.json, api_info.login_get)
    if not is_right_structure:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=error,
                        msg="Wrong request parameters structure.",
                    )
                )
            }
        )

    parameters = fill_default(request.json, api_info.login_get)
    if request.json["username"] and request.json["email"]:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=request_status.ErrorType.ValueError,
                        msg="User cant login via username and email.",
                    )
                )
            }
        )
    if not request.json["username"] and not request.json["email"]:
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=request_status.ErrorType.ValueError,
                        msg="User must login via username or email.",
                    )
                )
            }
        )
    if request.json["username"] == "unlogged_user":
        return json.dumps(
            {
                "status": dict(
                    request_status.Status(
                        request_status.StatusType.ERROR,
                        error_type=request_status.ErrorType.ValueError,
                        msg="Unlogged user cannot use this method",
                    )
                )
            }
        )
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, is_password_correct = backend.login(session, parameters)
        if status.is_error:
            session.rollback()
            return json.dumps({"status": dict(status)})

        session.commit()
        return json.dumps({"status": dict(status), "is-correct": is_password_correct})


def run_server(server_mode="production"):
    """Запускает Flask-сервер, выбрав URL базы данных из переменных окружения.

    Args:
        server_mode: "production" или "test".

    Returns:
        None
    """
    global db_url
    if server_mode == "test":
        db_url = os.getenv("MVP_DB_URL_TEST")
    else:
        db_url = os.getenv("MVP_DB_URL_PRODUCTION")
    app.run(host="0.0.0.0", port=5000)

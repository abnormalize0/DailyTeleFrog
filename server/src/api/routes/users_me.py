"""
Этот файл служит для хранения API-методов пути /users/me: чтение (GET), частичное
обновление (PATCH) и удаление (DELETE) собственного профиля авторизованного
пользователя.
Путь /users/me, а не /users/{username}: метод работает только с владельцем
токена, поэтому имя в пути ничего бы не значило и требовало бы лишней проверки.
"""

from flask import Response

from ... import backend
from ... import request_status
from ... import config
from ... import log
from .. import api_info
from ..shared import (
    app,
    get_session,
    json_response,
    no_content,
    read_body,
    read_query,
    require_auth,
)


@app.route("/users/me", methods=["GET"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_me_get() -> Response:
    """Возвращает выбранные поля данных собственного профиля авторизованного пользователя.

    Принимает:
        - requested_data (list, query-строка, обязательно, см.
          api_info.users_me_get) — запрашиваемые поля, параметр повторяется:
          ?requested_data=nickname&requested_data=email. Допустимые значения:
          nickname, email, name_history, avatar, sub_tags, blocked_tags, sub_users,
          blocked_users, description, creation_date, rating.

        Заголовок Authorization: Bearer <access_token> (обязательно) —
        определяет, чей профиль возвращается.

    Отдает:
        200 и JSON с одним ключом на каждое поле из requested_data: nickname (str),
        email (str), name_history (list[str] — прежние nickname пользователя без
        повторов и порядка; текущий nickname здесь только если пользователь к нему
        вернулся), avatar (str), sub_tags/blocked_tags (list[str]),
        sub_users/blocked_users (list[str] — username'ы), description (str),
        creation_date (int, мс с 1970 года), rating (int).

    Ошибки:
        - 400 /errors/validation — если requested_data отсутствует или содержит
          имя поля не из допустимого списка.
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.

    Контракт:
        Метод только читает данные, побочных эффектов не имеет. Поле возвращается в
        ответе, только если оно явно запрошено в requested_data. Всегда возвращает
        данные владельца токена — посмотреть чужой приватный профиль через этот
        метод нельзя (публичное превью автора отдаётся вместе со статьёй).
    """
    parameters, error = read_query(api_info.users_me_get)
    if error:
        return error
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status, data = backend.get_user_data(
            session, username, parameters["requested_data"]
        )
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return json_response(data)


@app.route("/users/me", methods=["PATCH"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_me_patch() -> Response:
    """Частично обновляет данные авторизованного пользователя: только те поля,
    что переданы в запросе.

    Принимает (JSON-тело запроса, см. api_info.users_me_patch):
        - nickname (str, опционально).
        - email (str, опционально).
        - avatar (str, опционально).
        - description (str, опционально).
        - sub-tags (list[str], опционально) — теги, на которые подписывается вызывающий.
        - blocked-tags (list[str], опционально) — теги, которые блокирует вызывающий.
        - sub-users (list[str], опционально) — username'ы, на которых подписывается вызывающий.
        - blocked-users (list[str], опционально) — username'ы, которых блокирует вызывающий.

        Заголовок Authorization: Bearer <access_token> (обязательно) —
        определяет, чьи данные обновляются.

    Отдает:
        204 без тела.

    Ошибки:
        - 400 /errors/validation — при некорректном теле запроса, если значение
          нарушает ограничения из api_info.users_me_patch (nickname и email
          проверяются как при регистрации, а в элементах sub-tags и blocked-tags
          должен быть видимый символ) или если sub-users/blocked-users
          содержит несуществующего или удалённого пользователя.
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.
        - 403 /errors/forbidden — если sub-users/blocked-users содержит самого
          вызывающего.
        - 409 /errors/conflict — если email занят другим пользователем.

    Контракт:
        Повторная подписка, блокировка или возврат к прежнему nickname не являются
        ошибкой: PATCH описывает нужное состояние, и оно уже достигнуто.
        Обрабатываются только переданные в запросе поля, остальные остаются без
        изменений. Если nickname меняется, прежний добавляется в name_history
        пользователя. Подписка на тег/автора из sub-tags/sub-users автоматически
        снимает соответствующую блокировку (и наоборот для blocked-tags/blocked-users) —
        подписка и блокировка одного и того же тега/автора взаимоисключающие.
        Весь запрос применяется атомарно: если любое из полей (включая отдельный
        элемент списков sub-tags/blocked-tags/sub-users/blocked-users) вызывает
        ошибку, ни одно изменение из этого запроса не сохраняется.
    """
    # fill_default здесь нельзя: подставленные значения выглядели бы как
    # переданные поля, и update_user_info затёр бы ими профиль.
    parameters, error = read_body(api_info.users_me_patch)
    if error:
        return error
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status = backend.update_user_info(session, username, parameters)
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return no_content()


@app.route("/users/me", methods=["DELETE"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_me_delete() -> Response:
    """Удаляет аккаунт авторизованного пользователя.

    Принимает (JSON-тело запроса, см. api_info.users_me_delete):
        - password (str, обязательно) — текущий пароль: одного токена недостаточно,
          чтобы украденная сессия не могла уничтожить аккаунт.

        Заголовок Authorization: Bearer <access_token> (обязательно) — определяет,
        чей аккаунт удаляется.

    Отдает:
        204 без тела.

    Ошибки:
        - 400 /errors/validation — при некорректном теле запроса.
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.
        - 403 /errors/forbidden — если password неверен.

    Контракт:
        Удаление мягкое (см. decisions/0005-soft-delete.md): войти в аккаунт больше
        нельзя, все токены отозваны, подписки и блокировки других пользователей на него
        сняты, username и email остаются занятыми. Статьи и комментарии аккаунта
        остаются доступны, в author_preview вместо его данных отдаётся
        is_deleted (True). Повторный вызов даст 401, потому что токен уже отозван:
        идемпотентность DELETE здесь недостижима.
    """
    parameters, error = read_body(api_info.users_me_delete)
    if error:
        return error
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status = backend.delete_user(session, parameters["password"], username)
        if status.is_error:
            session.rollback()
            return request_status.problem_response(status)

        session.commit()
        return no_content()

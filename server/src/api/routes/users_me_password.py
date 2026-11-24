"""
Этот файл служит для хранения API-метода PUT /users/me/password — смена пароля.
"""

from flask.typing import ResponseReturnValue

from ... import backend
from ... import config
from ... import log
from .. import api_info
from ..shared import (
    app,
    get_session,
    problem_response,
    read_body,
    require_auth,
)


@app.route("/users/me/password", methods=["PUT"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_me_password_put() -> ResponseReturnValue:
    """Меняет пароль авторизованного пользователя.

    Принимает (JSON-тело запроса, см. api_info.users_me_password_put):
        - previous_password (str, обязательно) — текущий пароль пользователя.
        - new_password (str, обязательно) — новый пароль.

        Заголовок Authorization: Bearer <access_token> (обязательно) —
        определяет, чей пароль меняется.

    Отдает:
        204 без тела.

    Ошибки:
        - 400 /errors/bad-request — если тело не является корректным JSON-объектом
          или отсутствует подходящий Content-Type.
        - 422 /errors/validation — при неверных значениях полей тела запроса, в том
          числе если new_password короче 8 или длиннее 128 символов.
        - 401 /errors/invalid-token — если заголовок Authorization отсутствует,
          токен не найден или истёк.
        - 403 /errors/forbidden — если previous_password не совпадает с текущим
          паролем пользователя.

    Контракт:
        Пароль обновляется, только если previous_password верно указан. Новый пароль
        хешируется перед сохранением (PBKDF2-HMAC-SHA256), как и при регистрации.
        При успехе отзываются все access и refresh токены пользователя, включая
        тот, которым был выполнен этот запрос — все устройства/вкладки должны
        авторизоваться заново через /auth/login.
    """
    parameters, error = read_body(api_info.users_me_password_put)
    if error:
        return error
    with get_session() as session:
        username, auth_error = require_auth(session)
        if auth_error:
            return auth_error
        status = backend.change_password(
            session,
            parameters["previous_password"],
            parameters["new_password"],
            username,
        )
        if status.is_error:
            session.rollback()
            return problem_response(status)

        session.commit()
        return "", 204

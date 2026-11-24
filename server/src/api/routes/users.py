"""
Этот файл служит для хранения API-метода POST /users — регистрация пользователя.
"""

from flask.typing import ResponseReturnValue

from ... import config
from ... import log
from ...db import user as user_db
from .. import api_info
from ..shared import (
    app,
    fill_default,
    get_session,
    problem_response,
    read_body,
)


@app.route("/users", methods=["POST"])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_post() -> ResponseReturnValue:
    """Регистрирует нового пользователя.

    Принимает (JSON-тело запроса, см. api_info.users_post):
        - username (str, обязательно) — уникальный идентификатор пользователя,
          используемый во всех остальных методах API.
        - nickname (str, обязательно) — отображаемое имя.
        - email (str, обязательно).
        - password (str, обязательно) — хешируется перед сохранением (PBKDF2-HMAC-SHA256).
        - avatar (str, опционально) — ссылка на аватар.
        - description (str, опционально) — текстовое описание профиля.

    Отдает:
        201 и JSON:
        - username (str) — идентификатор созданного пользователя. Заголовка
          Location нет: у пользователя нет публичного адреса, свой профиль
          доступен только как /users/me после входа.

    Ошибки:
        - 400 /errors/validation — при некорректном теле запроса, в том числе если
          значение нарушает ограничения из api_info.users_post: username короче 3
          символов или не из латинских букв, цифр, _ и -; в nickname нет видимых символов
          или есть управляющие; email не похож на адрес; password короче 8 или
          длиннее 128 символов.
        - 409 /errors/conflict — если пользователь с таким username или email уже
          зарегистрирован.

    Контракт:
        username уникален и является первичным ключом пользователя (используется
        во всех внешних ключах, ссылающихся на пользователя). email также уникален.
        При регистрации автоматически проставляется creation_date (текущее время в
        миллисекундах с 1970 года), история имен (name_history) пуста. Username и
        email удалённого аккаунта остаются занятыми. Рейтинг нового пользователя равен
        0 (вычисляется на лету по лайкам/дизлайкам его статей и комментариев, отдельно
        не хранится). Регистрация не
        выдаёт токены — после неё нужно отдельно авторизоваться через /auth/login.
    """
    parameters, error = read_body(api_info.users_post)
    if error:
        return error
    parameters = fill_default(parameters, api_info.users_post)
    with get_session() as session:
        status = user_db.add_user(
            session=session,
            username=parameters["username"],
            nickname=parameters["nickname"],
            password=parameters["password"],
            email=parameters["email"],
            avatar=parameters["avatar"],
            description=parameters["description"],
        )
        if status.is_error:
            session.rollback()
            return problem_response(status)

        session.commit()
        return {"username": parameters["username"]}, 201

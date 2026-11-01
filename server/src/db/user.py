"""
Этот файл служит для хранения логики работы с пользователями: регистрация,
проверка пароля, профиль, подписки/блок-листы на тегов и пользователей, рейтинг.
"""

from . import scheme
from sqlalchemy.orm import InstrumentedAttribute, Session
from typing import Any
import hashlib
import hmac
import os

from .. import request_status

# PBKDF2-HMAC-SHA256 — хеш пароля из стандартной библиотеки (hashlib), без
# сторонней зависимости (bcrypt/argon2 не в stdlib). 600 000 итераций — текущая
# рекомендация OWASP для этого алгоритма.
_PASSWORD_HASH_NAME = "sha256"
_PASSWORD_HASH_ITERATIONS = 600_000
_PASSWORD_SALT_BYTES = 16


def _hash_password(password: str) -> str:
    """Хеширует пароль в открытом виде для хранения в User.password.

    Args:
        password: пароль в открытом виде.

    Returns:
        Строка вида "<итерации>$<соль-hex>$<хеш-hex>": число итераций и соль
        хранятся вместе с хешем, чтобы _verify_password могла его повторить.
    """
    salt = os.urandom(_PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        _PASSWORD_HASH_NAME, password.encode("utf-8"), salt, _PASSWORD_HASH_ITERATIONS
    )
    return f"{_PASSWORD_HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    """Проверяет пароль в открытом виде против хеша из _hash_password.

    Args:
        password: пароль в открытом виде, введённый пользователем.
        stored: значение колонки User.password.

    Returns:
        `True`, если пароль совпадает, иначе `False`.
    """
    iterations, salt_hex, digest_hex = stored.split("$")
    salt = bytes.fromhex(salt_hex)
    computed = hashlib.pbkdf2_hmac(
        _PASSWORD_HASH_NAME, password.encode("utf-8"), salt, int(iterations)
    )
    # compare_digest вместо == — защита от timing-атак при сравнении хешей.
    return hmac.compare_digest(computed.hex(), digest_hex)


def _add_if_missing(session: Session, model: type, **columns: str) -> None:
    """Добавляет строку таблицы со связью или историей, если её ещё нет.

    Весь ключ этих таблиц составлен из самих значений строки, поэтому повторная
    вставка упала бы на первичном ключе и дала 500. Для клиента повтор не ошибка:
    PATCH описывает нужное состояние, и оно уже достигнуто.

    Args:
        session: сессия SQLAlchemy.
        model: класс таблицы из scheme.
        **columns: значения всех колонок первичного ключа.

    Returns:
        None
    """
    if session.query(model).filter_by(**columns).first() is None:
        session.add(model(**columns))


def _self_reference() -> request_status.Status:
    """Строит ошибку для подписки на себя или блокировки себя.

    Args:
        None

    Returns:
        `Status` с типом Forbidden: как и реакция на свою статью, это запрещённое
        действие над своим объектом, а не ошибка в формате запроса.
    """
    return request_status.Status(
        request_status.StatusType.ERROR,
        error_type=request_status.ErrorType.Forbidden,
        msg="User cannot subscribe to or block themselves",
    )


def _unknown_target_user(username: str) -> request_status.Status:
    """Строит ошибку для ссылки на несуществующего пользователя в теле запроса.

    Args:
        username: username из тела запроса.

    Returns:
        `Status` с типом InvalidParameters: 400, а не 404, потому что URL
        запроса существует, а неверна ссылка внутри тела (см. decisions/0004).
    """
    return request_status.Status(
        request_status.StatusType.ERROR,
        error_type=request_status.ErrorType.InvalidParameters,
        msg=f"Cannot find user with username: {username}",
    )


def is_user_not_exist(
    session: Session, username: str | None = None, email: str | None = None
) -> bool:
    """Проверяет, существует ли пользователь с указанным username или email.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя для поиска.
        email: email пользователя для поиска.

    Returns:
        `True`, если пользователь не найден, иначе `False`.
    """
    user = None
    if username:
        user = (
            session.query(scheme.User).where(scheme.User.username == username).scalar()
        )
    if email:
        user = session.query(scheme.User).where(scheme.User.email == email).scalar()
    return user is None


def add_user(
    session: Session,
    username: str,
    nickname: str,
    password: str,
    creation_date: int,
    email: str,
    avatar: str | None = None,
    description: str | None = None,
) -> request_status.Status:
    """Регистрирует нового пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: уникальный идентификатор пользователя.
        nickname: отображаемое имя.
        password: пароль в открытом виде (хешируется перед сохранением).
        creation_date: дата регистрации, мс с 1970 года.
        email: email пользователя.
        avatar: ссылка на аватар.
        description: описание профиля.

    Returns:
        `Status`:
            - OK — пользователь успешно создан.
            - Conflict — username или email уже заняты.
    """
    if not is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.Conflict,
            msg=f"User with username {username} already exists",
        )
    if not is_user_not_exist(session=session, email=email):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.Conflict,
            msg=f"User with email {email} already exists",
        )
    user = scheme.User(
        username=username,
        nickname=nickname,
        password=_hash_password(password),
        creation_date=creation_date,
        email=email,
        avatar=avatar,
        description=description,
    )
    old_name = scheme.UserNameHistory(
        username=username,
        old_name=nickname,
    )
    session.add_all((user, old_name))
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def get_username_by_email(session: Session, email: str) -> str | None:
    """Возвращает username пользователя с указанным email.

    Args:
        session: сессия SQLAlchemy.
        email: email пользователя.

    Returns:
        username (str), либо `None`, если пользователь с таким email не найден.
    """
    return (
        session.query(scheme.User.username).where(scheme.User.email == email).scalar()
    )


def check_password(
    session: Session,
    password: str,
    username: str | None = None,
    email: str | None = None,
) -> tuple[request_status.Status, bool]:
    """Проверяет пароль пользователя, найденного по username или email.

    Args:
        session: сессия SQLAlchemy.
        password: пароль для проверки.
        username: имя пользователя для поиска.
        email: email пользователя для поиска.

    Returns:
        Кортеж (`Status`, bool):
            - OK и `True`/`False` — совпадает ли password с паролем найденного
              пользователя.
            - OK и `False` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username, email=email):
        return request_status.Status(request_status.StatusType.OK), False
    user_password: str
    if username:
        user_password = (
            session.query(scheme.User.password)
            .where(scheme.User.username == username)
            .scalar()
        )
    if email:
        user_password = (
            session.query(scheme.User.password)
            .where(scheme.User.email == email)
            .scalar()
        )
    return (
        request_status.Status(request_status.StatusType.OK),
        _verify_password(password, user_password),
    )


def change_password(
    session: Session, password: str, username: str
) -> request_status.Status:
    """Меняет пароль пользователя.

    Args:
        session: сессия SQLAlchemy.
        password: новый пароль в открытом виде (хешируется перед сохранением).
        username: имя пользователя.

    Returns:
        `Status`:
            - OK — пароль успешно изменен.
            - NotFound — пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username)
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.password = _hash_password(password)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def update_email(session: Session, username: str, email: str) -> request_status.Status:
    """Обновляет email пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        email: новый email.

    Returns:
        `Status`:
            - OK — email успешно обновлен.
            - NotFound — пользователь не найден.
            - Conflict — email занят другим пользователем.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username)
    # Свой текущий email конфликтом не считается: повторный PATCH не должен падать.
    if get_username_by_email(session, email) not in (None, username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.Conflict,
            msg=f"User with email {email} already exists",
        )
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.email = email
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def update_nickname(
    session: Session, username: str, nickname: str
) -> request_status.Status:
    """Обновляет nickname пользователя и добавляет запись в name_history.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        nickname: новый nickname.

    Returns:
        `Status`:
            - OK — nickname успешно обновлен.
            - NotFound — пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username)
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.nickname = nickname
    # Возврат к прежнему nickname: запись о нём в истории уже есть.
    _add_if_missing(
        session, scheme.UserNameHistory, username=username, old_name=nickname
    )
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def update_description(
    session: Session, username: str, description: str
) -> request_status.Status:
    """Обновляет описание профиля пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        description: новое описание.

    Returns:
        `Status`:
            - OK — описание успешно обновлено.
            - NotFound — пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username)
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.description = description
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def update_avatar(
    session: Session, username: str, avatar: str
) -> request_status.Status:
    """Обновляет avatar пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        avatar: новая ссылка на avatar.

    Returns:
        `Status`:
            - OK — avatar успешно обновлен.
            - NotFound — пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username)
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.avatar = avatar
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def sub_user(session: Session, username: str, sub: str) -> request_status.Status:
    """Подписывает username на пользователя sub, снимая блокировку sub, если она была.

    Args:
        session: сессия SQLAlchemy.
        username: кто подписывается.
        sub: на кого подписываются.

    Returns:
        `Status`:
            - OK — подписка оформлена.
            - NotFound — username не найден.
            - Forbidden — sub совпадает с username.
            - InvalidParameters — sub не существует.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username)
    if sub == username:
        return _self_reference()
    if is_user_not_exist(session=session, username=sub):
        return _unknown_target_user(sub)
    block_user = (
        session.query(scheme.UserBlacklist)
        .where(
            scheme.UserBlacklist.username == username,
            scheme.UserBlacklist.blocked_user == sub,
        )
        .scalar()
    )
    if block_user:
        session.delete(block_user)
    _add_if_missing(
        session, scheme.UserSubscription, username=username, subscribed_user=sub
    )
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def block_user(
    session: Session, username: str, blocked_user: str
) -> request_status.Status:
    """Блокирует пользователя blocked_user для username, снимая подписку, если она была.

    Args:
        session: сессия SQLAlchemy.
        username: кто блокирует.
        blocked_user: кого блокируют.

    Returns:
        `Status`:
            - OK — блокировка оформлена.
            - NotFound — username не найден.
            - Forbidden — blocked_user совпадает с username.
            - InvalidParameters — blocked_user не существует.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username)
    if blocked_user == username:
        return _self_reference()
    if is_user_not_exist(session=session, username=blocked_user):
        return _unknown_target_user(blocked_user)
    sub_user = (
        session.query(scheme.UserSubscription)
        .where(
            scheme.UserSubscription.username == username,
            scheme.UserSubscription.subscribed_user == blocked_user,
        )
        .scalar()
    )
    if sub_user:
        session.delete(sub_user)
    _add_if_missing(
        session, scheme.UserBlacklist, username=username, blocked_user=blocked_user
    )
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def sub_tag(session: Session, username: str, tag_name: str) -> request_status.Status:
    """Подписывает username на тег tag_name, снимая блокировку тега, если она была.

    Args:
        session: сессия SQLAlchemy.
        username: кто подписывается.
        tag_name: на какой тег подписываются.

    Returns:
        `Status`:
            - OK — подписка оформлена.
            - NotFound — username не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username)
    block_tag = (
        session.query(scheme.TagBlacklist)
        .where(
            scheme.TagBlacklist.username == username,
            scheme.TagBlacklist.tag_name == tag_name,
        )
        .scalar()
    )
    if block_tag:
        session.delete(block_tag)
    _add_if_missing(
        session, scheme.TagSubscription, username=username, tag_name=tag_name
    )
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def block_tag(session: Session, username: str, tag_name: str) -> request_status.Status:
    """Блокирует тег tag_name для username, снимая подписку на тег, если она была.

    Args:
        session: сессия SQLAlchemy.
        username: кто блокирует.
        tag_name: какой тег блокируют.

    Returns:
        `Status`:
            - OK — блокировка оформлена.
            - NotFound — username не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username)
    sub_tag = (
        session.query(scheme.TagSubscription)
        .where(
            scheme.TagSubscription.username == username,
            scheme.TagSubscription.tag_name == tag_name,
        )
        .scalar()
    )
    if sub_tag:
        session.delete(sub_tag)
    _add_if_missing(session, scheme.TagBlacklist, username=username, tag_name=tag_name)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def get_rating(
    session: Session, username: str
) -> tuple[request_status.Status, int | None]:
    """Вычисляет рейтинг пользователя по лайкам/дизлайкам его статей и комментариев.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, int):
            - OK и рейтинг — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username), None
    user_articles = (
        session.query(scheme.Article.id)
        .where(scheme.Article.author_username == username)
        .all()
    )
    user_articles = [row[0] for row in user_articles]

    article_likes = (
        session.query(scheme.ArticleLike)
        .where(scheme.ArticleLike.article_id.in_(user_articles))
        .count()
    )
    article_dislikes = (
        session.query(scheme.ArticleDislike)
        .where(scheme.ArticleDislike.article_id.in_(user_articles))
        .count()
    )
    user_comments = (
        session.query(scheme.Comment.id)
        .where(scheme.Comment.author_username == username)
        .all()
    )
    user_comments = [row[0] for row in user_comments]
    comment_likes = (
        session.query(scheme.CommentLike)
        .where(scheme.CommentLike.comment_id.in_(user_comments))
        .count()
    )
    comment_dislikes = (
        session.query(scheme.CommentDislike)
        .where(scheme.CommentDislike.comment_id.in_(user_comments))
        .count()
    )
    return (
        request_status.Status(request_status.StatusType.OK),
        article_likes - article_dislikes + comment_likes - comment_dislikes,
    )


def _get_user_field(
    session: Session, username: str, column: InstrumentedAttribute
) -> tuple[request_status.Status, Any]:
    """Возвращает значение одной колонки пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        column: колонка scheme.User для выборки.

    Returns:
        Кортеж (`Status`, значение):
            - OK и значение колонки — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username), None
    value = session.query(column).where(scheme.User.username == username).scalar()
    return request_status.Status(request_status.StatusType.OK), value


def _get_user_list_field(
    session: Session,
    username: str,
    column: InstrumentedAttribute,
    where_column: InstrumentedAttribute,
) -> tuple[request_status.Status, list | None]:
    """Возвращает список значений одной колонки таблицы, связанной с пользователем.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        column: колонка со значениями для выборки (например, TagSubscription.tag_name).
        where_column: колонка связанной таблицы с username для фильтрации.

    Returns:
        Кортеж (`Status`, list):
            - OK и список значений — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username), None
    rows = session.query(column).where(where_column == username).all()
    return request_status.Status(request_status.StatusType.OK), [row[0] for row in rows]


def get_email(
    session: Session, username: str
) -> tuple[request_status.Status, str | None]:
    """Возвращает email пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, str):
            - OK и email — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_field(session, username, scheme.User.email)


def get_name_history(
    session: Session, username: str
) -> tuple[request_status.Status, list[str] | None]:
    """Возвращает историю nickname пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список nickname (включая текущий) — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_list_field(
        session,
        username,
        scheme.UserNameHistory.old_name,
        scheme.UserNameHistory.username,
    )


def get_nickname(
    session: Session, username: str
) -> tuple[request_status.Status, str | None]:
    """Возвращает текущий nickname пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, str):
            - OK и nickname — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_field(session, username, scheme.User.nickname)


def get_description(
    session: Session, username: str
) -> tuple[request_status.Status, str | None]:
    """Возвращает описание профиля пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, str):
            - OK и описание — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_field(session, username, scheme.User.description)


def get_avatar(
    session: Session, username: str
) -> tuple[request_status.Status, str | None]:
    """Возвращает ссылку на avatar пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, str):
            - OK и ссылка на avatar — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_field(session, username, scheme.User.avatar)


def get_sub_user(
    session: Session, username: str
) -> tuple[request_status.Status, list[str] | None]:
    """Возвращает username'ы, на которых подписан пользователь.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список username'ов — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_list_field(
        session,
        username,
        scheme.UserSubscription.subscribed_user,
        scheme.UserSubscription.username,
    )


def get_blacklist_user(
    session: Session, username: str
) -> tuple[request_status.Status, list[str] | None]:
    """Возвращает username'ы, заблокированные пользователем.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список username'ов — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_list_field(
        session,
        username,
        scheme.UserBlacklist.blocked_user,
        scheme.UserBlacklist.username,
    )


def get_sub_tag(
    session: Session, username: str
) -> tuple[request_status.Status, list[str] | None]:
    """Возвращает теги, на которые подписан пользователь.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список тегов — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_list_field(
        session,
        username,
        scheme.TagSubscription.tag_name,
        scheme.TagSubscription.username,
    )


def get_blacklist_tag(
    session: Session, username: str
) -> tuple[request_status.Status, list[str] | None]:
    """Возвращает теги, заблокированные пользователем.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список тегов — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_list_field(
        session,
        username,
        scheme.TagBlacklist.tag_name,
        scheme.TagBlacklist.username,
    )


def get_creation_date(
    session: Session, username: str
) -> tuple[request_status.Status, int | None]:
    """Возвращает дату регистрации пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, int):
            - OK и дата регистрации (мс с 1970 года) — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    return _get_user_field(session, username, scheme.User.creation_date)


def preview(
    session: Session, username: str
) -> tuple[request_status.Status, dict | None]:
    """Собирает краткое превью пользователя (avatar, nickname, description, username).

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, dict):
            - OK и превью — если пользователь найден.
            - NotFound и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.not_found("user with username", username), None

    row = (
        session.query(
            scheme.User.avatar,
            scheme.User.nickname,
            scheme.User.description,
            scheme.User.username,
        )
        .where(scheme.User.username == username)
        .first()
    )
    user_preview = {
        "avatar": row.avatar,
        "nickname": row.nickname,
        "description": row.description,
        "username": row.username,
    }
    return request_status.Status(request_status.StatusType.OK), user_preview

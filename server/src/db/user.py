from . import scheme
import time
from sqlalchemy import select, update, delete
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy.orm import Session

from .. import config
from .. import request_status


def is_user_not_exist(session: Session, username=None, email=None):
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
    username,
    nickname,
    password,
    creation_date,
    email,
    avatar=None,
    description=None,
):
    """Регистрирует нового пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: уникальный идентификатор пользователя.
        nickname: отображаемое имя.
        password: пароль (хранится как есть).
        creation_date: дата регистрации, мс с 1970 года.
        email: email пользователя.
        avatar: ссылка на аватар.
        description: описание профиля.

    Returns:
        `Status`:
            - OK — пользователь успешно создан.
            - ValueError — username или email уже заняты.
    """
    if not is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"User with username {username} already exists",
        )
    if not is_user_not_exist(session=session, email=email):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"User with email {email} already exists",
        )
    user = scheme.User(
        username=username,
        nickname=nickname,
        password=password,
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


def check_password(session: Session, password, username=None, email=None):
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
        password == user_password,
    )


def change_password(session: Session, password, username):
    """Меняет пароль пользователя.

    Args:
        session: сессия SQLAlchemy.
        password: новый пароль.
        username: имя пользователя.

    Returns:
        `Status`:
            - OK — пароль успешно изменен.
            - ValueError — пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find user with username: {username}",
        )
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.password = password
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def update_email(session: Session, username, email):
    """Обновляет email пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        email: новый email.

    Returns:
        `Status`:
            - OK — email успешно обновлен.
            - ValueError — пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find user with username: {username}",
        )
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.email = email
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def update_nickname(session: Session, username, nickname):
    """Обновляет nickname пользователя и добавляет запись в name_history.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        nickname: новый nickname.

    Returns:
        `Status`:
            - OK — nickname успешно обновлен.
            - ValueError — пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find user with username: {username}",
        )
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.nickname = nickname
    name_history = scheme.UserNameHistory(
        username=username,
        old_name=nickname,
    )
    session.add(name_history)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def update_description(session: Session, username, description):
    """Обновляет описание профиля пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        description: новое описание.

    Returns:
        `Status`:
            - OK — описание успешно обновлено.
            - ValueError — пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find user with username: {username}",
        )
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.description = description
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def update_avatar(session: Session, username, avatar):
    """Обновляет avatar пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.
        avatar: новая ссылка на avatar.

    Returns:
        `Status`:
            - OK — avatar успешно обновлен.
            - ValueError — пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find user with username: {username}",
        )
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.avatar = avatar
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def sub_user(session: Session, username, sub):
    """Подписывает username на пользователя sub, снимая блокировку sub, если она была.

    Args:
        session: сессия SQLAlchemy.
        username: кто подписывается.
        sub: на кого подписываются.

    Returns:
        `Status`:
            - OK — подписка оформлена.
            - ValueError — username не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find user with username: {username}",
        )
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
    subscription = scheme.UserSubscription(
        username=username,
        subscribed_user=sub,
    )
    session.add(subscription)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def block_user(session: Session, username, blocked_user):
    """Блокирует пользователя blocked_user для username, снимая подписку, если она была.

    Args:
        session: сессия SQLAlchemy.
        username: кто блокирует.
        blocked_user: кого блокируют.

    Returns:
        `Status`:
            - OK — блокировка оформлена.
            - ValueError — username не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find user with username: {username}",
        )
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
    blacklist = scheme.UserBlacklist(
        username=username,
        blocked_user=blocked_user,
    )
    session.add(blacklist)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def sub_tag(session: Session, username, tag_name):
    """Подписывает username на тег tag_name, снимая блокировку тега, если она была.

    Args:
        session: сессия SQLAlchemy.
        username: кто подписывается.
        tag_name: на какой тег подписываются.

    Returns:
        `Status`:
            - OK — подписка оформлена.
            - ValueError — username не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find user with username: {username}",
        )
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
    subscription = scheme.TagSubscription(
        username=username,
        tag_name=tag_name,
    )
    session.add(subscription)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def block_tag(session: Session, username, tag_name):
    """Блокирует тег tag_name для username, снимая подписку на тег, если она была.

    Args:
        session: сессия SQLAlchemy.
        username: кто блокирует.
        tag_name: какой тег блокируют.

    Returns:
        `Status`:
            - OK — блокировка оформлена.
            - ValueError — username не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find user with username: {username}",
        )
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
    user_blacklist = scheme.TagBlacklist(
        username=username,
        tag_name=tag_name,
    )
    session.add(user_blacklist)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def get_rating(session: Session, username):
    """Вычисляет рейтинг пользователя по лайкам/дизлайкам его статей и комментариев.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, int):
            - OK и рейтинг — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
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


def get_email(session: Session, username):
    """Возвращает email пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, str):
            - OK и email — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    email = (
        session.query(scheme.User.email)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), email


def get_name_history(session: Session, username):
    """Возвращает историю nickname пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список nickname (включая текущий) — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    name_history = (
        session.query(scheme.UserNameHistory.old_name)
        .where(scheme.UserNameHistory.username == username)
        .all()
    )
    name_history = [row[0] for row in name_history]
    return request_status.Status(request_status.StatusType.OK), name_history


def get_nickname(session: Session, username):
    """Возвращает текущий nickname пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, str):
            - OK и nickname — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    nickname = (
        session.query(scheme.User.nickname)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), nickname


def get_description(session: Session, username):
    """Возвращает описание профиля пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, str):
            - OK и описание — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    description = (
        session.query(scheme.User.description)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), description


def get_avatar(session: Session, username):
    """Возвращает ссылку на avatar пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, str):
            - OK и ссылка на avatar — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    avatar = (
        session.query(scheme.User.avatar)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), avatar


def get_sub_user(session: Session, username):
    """Возвращает username'ы, на которых подписан пользователь.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список username'ов — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    subscriptions = (
        session.query(scheme.UserSubscription.subscribed_user)
        .where(scheme.UserSubscription.username == username)
        .all()
    )
    subscriptions = [row[0] for row in subscriptions]
    return request_status.Status(request_status.StatusType.OK), subscriptions


def get_blacklist_user(session: Session, username):
    """Возвращает username'ы, заблокированные пользователем.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список username'ов — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    blacklist = (
        session.query(scheme.UserBlacklist.blocked_user)
        .where(scheme.UserBlacklist.username == username)
        .all()
    )
    blacklist = [row[0] for row in blacklist]
    return request_status.Status(request_status.StatusType.OK), blacklist


def get_sub_tag(session: Session, username):
    """Возвращает теги, на которые подписан пользователь.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список тегов — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    subscriptions = (
        session.query(scheme.TagSubscription.tag_name)
        .where(scheme.TagSubscription.username == username)
        .all()
    )
    subscriptions = [row[0] for row in subscriptions]
    return request_status.Status(request_status.StatusType.OK), subscriptions


def get_blacklist_tag(session: Session, username):
    """Возвращает теги, заблокированные пользователем.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список тегов — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    blacklist = (
        session.query(scheme.TagBlacklist.tag_name)
        .where(scheme.TagBlacklist.username == username)
        .all()
    )
    blacklist = [row[0] for row in blacklist]
    return request_status.Status(request_status.StatusType.OK), blacklist


def get_creation_date(session: Session, username):
    """Возвращает дату регистрации пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, int):
            - OK и дата регистрации (мс с 1970 года) — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )
    creation_date = (
        session.query(scheme.User.creation_date)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), creation_date


def preview(session: Session, username):
    """Собирает краткое превью пользователя (avatar, nickname, description, username).

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, dict):
            - OK и превью — если пользователь найден.
            - ValueError и `None` — если пользователь не найден.
    """
    if is_user_not_exist(session=session, username=username):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find user with username: {username}",
            ),
            None,
        )

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

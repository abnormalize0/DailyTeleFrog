"""
Этот файл служит для хранения логики выполнения запросов, не связанной с изменениями в базах данных.
"""

import json
import time

from sqlalchemy.orm import Session

from .db import user, article, comment, auth
from . import config
from . import request_status


def get_article(
    session: Session, article_id: int, username: str | None
) -> tuple[request_status.Status, dict | None]:
    """Собирает полную информацию о статье для страницы статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: пользователь, от чьего имени просматривается статья
            (используется для is_liked/is_disliked).

    Returns:
        Кортеж (`Status`, dict):
            - OK и данные статьи (см. api_articles_item_get) — при успехе.
            - ERROR и `None` — если статья или связанные данные не найдены.
    """
    status, article_info = article.get(session, article_id)
    if status.is_error:
        return status, None

    data = {
        "creation_date": article_info.creation_date,
        "title": article_info.title,
        "body": json.loads(article_info.body),
    }
    accessors = {
        "author_preview": lambda: user.preview(session, article_info.author_username),
        "preview": lambda: article.preview(session, article_id),
        "likes": lambda: article.likes_count(session, article_id),
        "dislikes": lambda: article.dislikes_count(session, article_id),
        "rating": lambda: article.rating(session, article_id),
        "comments_count": lambda: article.comments_count(session, article_id),
        "comments": lambda: comment.from_article(session, article_id),
        "is_liked": lambda: article.is_liked(session, article_id, username),
        "is_disliked": lambda: article.is_disliked(session, article_id, username),
        "tags": lambda: article.tags(session, article_id),
    }
    for key, accessor in accessors.items():
        status, data[key] = accessor()
        if status.is_error:
            return status, None

    return request_status.Status(request_status.StatusType.OK), data


def post_article(
    session: Session,
    author: str,
    title: str,
    body: dict,
    preview: dict,
    tags: list[str],
) -> tuple[request_status.Status, int | None]:
    """Публикует новую статью и создает её теги.

    Args:
        session: сессия SQLAlchemy.
        author: username автора.
        title: заголовок статьи.
        body: тело статьи.
        preview: контент предпоказа.
        tags: список тегов статьи.

    Returns:
        Кортеж (`Status`, int):
            - OK и id созданной статьи — при успехе.
            - InvalidParameters и `None` — если в tags есть одинаковые теги.
    """
    article_id = article.post(
        session=session, title=title, body=body, author=author, preview=preview
    )
    status = article.add_tags(session=session, tags=tags, article_id=article_id)
    if status.is_error:
        return status, None
    return status, article_id


def add_user(session: Session, user_info: dict) -> request_status.Status:
    """Регистрирует нового пользователя.

    Args:
        session: сессия SQLAlchemy.
        user_info: словарь с полями username, nickname, password, email,
            avatar, description.

    Returns:
        `Status`:
            - OK — пользователь успешно создан.
            - Conflict — username или email уже заняты.
    """
    status = user.add_user(
        session=session,
        username=user_info["username"],
        nickname=user_info["nickname"],
        password=user_info["password"],
        creation_date=round(time.time() * 1000),
        email=user_info["email"],
        avatar=user_info["avatar"],
        description=user_info["description"],
    )
    return status


def update_user_info(
    session: Session, username: str, data: dict
) -> request_status.Status:
    """Обновляет только те поля пользователя, что переданы в data.

    Args:
        session: сессия SQLAlchemy.
        username: кого обновляем.
        data: словарь с изменяемыми полями (avatar, sub-tags, blocked-tags,
            sub-users, blocked-users, nickname, email, description).

    Returns:
        `Status`:
            - OK — все переданные поля успешно применены.
            - ошибка первого поля, которое не удалось применить.
    """
    single_value_updaters = {
        "avatar": user.update_avatar,
        "nickname": user.update_nickname,
        "email": user.update_email,
        "description": user.update_description,
    }
    list_value_updaters = {
        "sub-tags": user.sub_tag,
        "blocked-tags": user.block_tag,
        "sub-users": user.sub_user,
        "blocked-users": user.block_user,
    }
    for key in data:
        if key in single_value_updaters:
            status = single_value_updaters[key](session, username, data[key])
            if status.is_error:
                return status
        elif key in list_value_updaters:
            updater = list_value_updaters[key]
            for value in data[key]:
                status = updater(session, username, value)
                if status.is_error:
                    return status
    return request_status.Status(request_status.StatusType.OK)


def _incorrect_password() -> request_status.Status:
    """Строит ошибку для неверного пароля при действии с собственным аккаунтом.

    Args:
        None

    Returns:
        `Status` с типом Forbidden: 403, а не 401, потому что токен валиден и клиент
        не должен пытаться его обновлять.
    """
    return request_status.Status(
        request_status.StatusType.ERROR,
        error_type=request_status.ErrorType.Forbidden,
        msg="Incorrect password",
    )


def delete_user(
    session: Session, password: str, username: str
) -> request_status.Status:
    """Удаляет аккаунт, если password верен, и отзывает все его токены, чтобы удалённым
    аккаунтом нельзя было пользоваться в уже открытых сессиях.

    Args:
        session: сессия SQLAlchemy.
        password: текущий пароль пользователя.
        username: имя пользователя.

    Returns:
        `Status`:
            - OK — аккаунт удалён.
            - Forbidden — password неверен.
            - NotFound — пользователь не найден.
    """
    status, is_same = user.check_password(session, password, username=username)
    if status.is_error:
        return status
    if not is_same:
        return _incorrect_password()
    status = user.delete(session, username)
    if status.is_error:
        return status
    auth.revoke_all_tokens(session, username)
    return status


def login(
    session: Session, parameters: dict
) -> tuple[request_status.Status, dict | None]:
    """Проверяет пароль пользователя и выпускает пару токенов авторизации.

    Args:
        session: сессия SQLAlchemy.
        parameters: словарь с полями password и username и/или email.

    Returns:
        Кортеж (`Status`, dict):
            - OK и {"access_token": str, "refresh_token": str} — при успехе.
            - InvalidCredentials и `None` — если пароль не совпадает или пользователь
              с таким username/email не найден (одно и то же сообщение для
              обоих случаев, чтобы не раскрывать существование аккаунта).
    """
    password = parameters["password"]
    username = parameters["username"]
    email = parameters["email"]
    status, is_password_correct = user.check_password(
        session=session, password=password, username=username, email=email
    )
    if status.is_error:
        return status, None
    if not is_password_correct:
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.InvalidCredentials,
                msg="Incorrect login or password",
            ),
            None,
        )
    if not username:
        username = user.get_username_by_email(session, email)
    auth.delete_expired_tokens(session, username)
    return request_status.Status(request_status.StatusType.OK), {
        "access_token": auth.create_access_token(session, username),
        "refresh_token": auth.create_refresh_token(session, username),
    }


def refresh_session(
    session: Session, refresh_token: str
) -> tuple[request_status.Status, dict | None]:
    """Выпускает новую пару токенов взамен действующего refresh token (ротация).

    Args:
        session: сессия SQLAlchemy.
        refresh_token: текущий refresh token.

    Returns:
        Кортеж (`Status`, dict):
            - OK и {"access_token": str, "refresh_token": str} — при успехе;
              переданный refresh_token отзывается и больше не действителен.
            - InvalidToken и `None` — если refresh_token не найден или истёк.
    """
    status, username = auth.resolve_refresh_token(session, refresh_token)
    if status.is_error:
        return status, None
    auth.revoke_refresh_token(session, refresh_token)
    auth.delete_expired_tokens(session, username)
    return request_status.Status(request_status.StatusType.OK), {
        "access_token": auth.create_access_token(session, username),
        "refresh_token": auth.create_refresh_token(session, username),
    }


def logout(
    session: Session, access_token: str, refresh_token: str
) -> request_status.Status:
    """Завершает сессию: отзывает переданные access и refresh токены.

    Args:
        session: сессия SQLAlchemy.
        access_token: access token текущей сессии.
        refresh_token: refresh token текущей сессии.

    Returns:
        `Status` — всегда OK; отзыв идемпотентен, уже отсутствующий токен
        просто игнорируется.
    """
    auth.revoke_access_token(session, access_token)
    auth.revoke_refresh_token(session, refresh_token)
    return request_status.Status(request_status.StatusType.OK)


def resolve_token(
    session: Session, access_token: str
) -> tuple[request_status.Status, str | None]:
    """Разрешает access token в username вызывающего — основа авторизации
    для всех защищённых API-методов.

    Args:
        session: сессия SQLAlchemy.
        access_token: значение access token (без префикса "Bearer ").

    Returns:
        Кортеж (`Status`, str) — OK и username, либо InvalidToken и `None`,
        если токен отсутствует, не найден или истёк.
    """
    return auth.resolve_access_token(session, access_token)


def change_password(
    session: Session, previous_password: str, new_password: str, username: str
) -> request_status.Status:
    """Меняет пароль пользователя, если previous_password верен, и отзывает
    все его токены (чтобы остальные сессии/устройства разлогинились).

    Args:
        session: сессия SQLAlchemy.
        previous_password: текущий пароль пользователя.
        new_password: новый пароль.
        username: имя пользователя.

    Returns:
        `Status`:
            - OK — пароль успешно изменен.
            - Forbidden — previous_password неверен.
            - NotFound — пользователь не найден.
    """
    status, is_same = user.check_password(session, previous_password, username=username)
    if status.is_error:
        return status
    if not is_same:
        return _incorrect_password()
    status = user.change_password(session, new_password, username)
    if status.is_error:
        return status
    auth.revoke_all_tokens(session, username)
    return status


def add_comment(
    session: Session, article_id: int, parent: int, comment_text: str, username: str
) -> tuple[request_status.Status, int | None]:
    """Добавляет комментарий (или ответ на комментарий) к статье.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        parent: id родительского комментария или -1 для комментария верхнего уровня.
        comment_text: текст комментария.
        username: автор комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и id созданного комментария — при успехе.
            - NotFound и `None` — если статьи нет: она указана в URL, поэтому
              это 404, а не падение на внешнем ключе с кодом 500.
            - InvalidParameters и `None` — если parent не найден или удалён.
    """
    if article.is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id), None
    return comment.add(session, article_id, parent, comment_text, username)


def get_comment_data(
    session: Session, comment_id: int, username: str | None, requested_data: list[str]
) -> tuple[request_status.Status, dict | None]:
    """Собирает выбранные поля данных о комментарии.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: пользователь, от чьего имени запрашиваются данные (для
            is_liked/is_disliked).
        requested_data: список запрашиваемых полей (likes, dislikes, rating,
            creation_date, is_liked, is_disliked).

    Returns:
        Кортеж (`Status`, dict):
            - OK и словарь с запрошенными полями.
            - OK и {"is_deleted": True} — если комментарий удалён: вместо данных
              отдаётся только статус, как заглушка в дереве комментариев.
            - NotFound и `None` — если комментария нет или удалена его статья.
    """
    if comment.is_deleted(session, comment_id):
        return request_status.Status(request_status.StatusType.OK), {"is_deleted": True}
    # Проверка сразу: is_liked/is_disliked для несуществующего объекта отдают
    # False, и без неё GET только этих полей вернул бы 200 вместо 404.
    if comment.is_comment_not_exist(session, comment_id):
        return request_status.not_found("comment with id", comment_id), None
    accessors = {
        "likes": lambda: comment.likes_count(session, comment_id),
        "dislikes": lambda: comment.dislikes_count(session, comment_id),
        "rating": lambda: comment.rating(session, comment_id),
        "creation_date": lambda: comment.creation_date(session, comment_id),
        "is_liked": lambda: comment.is_liked(session, comment_id, username),
        "is_disliked": lambda: comment.is_disliked(session, comment_id, username),
    }
    data = {}
    for key in requested_data:
        if key not in accessors:
            continue
        status, data[key] = accessors[key]()
        if status.is_error:
            return status, None
    return request_status.Status(request_status.StatusType.OK), data


def get_article_data(
    session: Session, article_id: int, username: str | None, requested_data: list[str]
) -> tuple[request_status.Status, dict | None]:
    """Собирает выбранные поля данных о статье.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: пользователь, от чьего имени запрашиваются данные (для
            is_liked/is_disliked).
        requested_data: список запрашиваемых полей (likes, dislikes, rating,
            comments_count, creation_date, tags, is_liked, is_disliked).

    Returns:
        Кортеж (`Status`, dict):
            - OK и словарь с запрошенными полями.
            - NotFound и `None` — если статьи нет.
    """
    # Проверка сразу, см. комментарий в get_comment_data.
    if article.is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id), None

    def get_creation_date() -> tuple[request_status.Status, int | None]:
        """Возвращает creation_date статьи как аксессор в формате (Status, значение).

        Args:
            None

        Returns:
            Кортеж (`Status`, int): OK и дата создания, либо NotFound и `None`.
        """
        status, article_info = article.get(session, article_id)
        if status.is_error:
            return status, None
        return status, article_info.creation_date

    accessors = {
        "likes": lambda: article.likes_count(session, article_id),
        "dislikes": lambda: article.dislikes_count(session, article_id),
        "rating": lambda: article.rating(session, article_id),
        "comments_count": lambda: article.comments_count(session, article_id),
        "creation_date": get_creation_date,
        "tags": lambda: article.tags(session, article_id),
        "is_liked": lambda: article.is_liked(session, article_id, username),
        "is_disliked": lambda: article.is_disliked(session, article_id, username),
    }
    data = {}
    for key in requested_data:
        if key not in accessors:
            continue
        status, data[key] = accessors[key]()
        if status.is_error:
            return status, None
    return request_status.Status(request_status.StatusType.OK), data


def get_user_data(
    session: Session, username: str, requested_data: list[str]
) -> tuple[request_status.Status, dict | None]:
    """Собирает выбранные поля данных о пользователе.

    Args:
        session: сессия SQLAlchemy.
        username: чей профиль запрашивается.
        requested_data: список запрашиваемых полей (avatar, name_history,
            sub_tags, blocked_tags, sub_users, blocked_users, nickname, email,
            description, creation_date, rating).

    Returns:
        Кортеж (`Status`, dict) — OK и словарь с запрошенными полями.
    """
    accessors = {
        "avatar": lambda: user.get_avatar(session, username),
        "name_history": lambda: user.get_name_history(session, username),
        "sub_tags": lambda: user.get_sub_tag(session, username),
        "blocked_tags": lambda: user.get_blacklist_tag(session, username),
        "sub_users": lambda: user.get_sub_user(session, username),
        "blocked_users": lambda: user.get_blacklist_user(session, username),
        "nickname": lambda: user.get_nickname(session, username),
        "email": lambda: user.get_email(session, username),
        "description": lambda: user.get_description(session, username),
        "creation_date": lambda: user.get_creation_date(session, username),
        "rating": lambda: user.get_rating(session, username),
    }
    data = {}
    for key in requested_data:
        if key not in accessors:
            continue
        status, data[key] = accessors[key]()
        if status.is_error:
            return status, None
    return request_status.Status(request_status.StatusType.OK), data


def get_article_preview(
    session: Session, article_id: int, username: str | None
) -> tuple[request_status.Status, dict | None]:
    """Собирает превью статьи для ленты.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: пользователь, для которого собирается превью (для
            is_liked/is_disliked).

    Returns:
        Кортеж (`Status`, dict) — OK и превью статьи (id, title, creation_date,
        author_preview, preview_content, likes, dislikes, rating,
        comments_count, tags, is_liked, is_disliked).
    """
    status, article_info = article.get(session, article_id)
    if status.is_error:
        return status, None

    data = {
        "id": article_id,
        "title": article_info.title,
        "creation_date": article_info.creation_date,
    }
    accessors = {
        "author_preview": lambda: user.preview(session, article_info.author_username),
        "preview_content": lambda: article.preview(session, article_id),
        "likes": lambda: article.likes_count(session, article_id),
        "dislikes": lambda: article.dislikes_count(session, article_id),
        "rating": lambda: article.rating(session, article_id),
        "comments_count": lambda: article.comments_count(session, article_id),
        "tags": lambda: article.tags(session, article_id),
        "is_liked": lambda: article.is_liked(session, article_id, username),
        "is_disliked": lambda: article.is_disliked(session, article_id, username),
    }
    for key, accessor in accessors.items():
        status, data[key] = accessor()
        if status.is_error:
            return status, None

    return request_status.Status(request_status.StatusType.OK), data


def pages_get(
    session: Session,
    username: str | None,
    indexes: list[int],
    include_nonsub: bool,
    sort_column: str,
    sort_direction: str,
    include: dict,
    exclude: dict,
    bounds: dict,
) -> tuple[request_status.Status, dict | None]:
    """Собирает страницы ленты статей с превью каждой статьи.

    Args:
        session: сессия SQLAlchemy.
        username: пользователь, для которого формируется лента.
        indexes: список индексов запрошенных страниц.
        include_nonsub: если `False`, оставляет только статьи по подпискам username.
        sort_column: "creation_date" или "rating".
        sort_direction: "ascending" или "descending".
        include: словарь с ключами "tags"/"authors" для включающего фильтра.
        exclude: словарь с ключами "tags"/"authors" для исключающего фильтра.
        bounds: словарь с ключами "upper"/"lower" — границы sort_column.

    Returns:
        Кортеж (`Status`, dict) — OK и словарь {индекс страницы: список превью
        статей}.
    """
    article_ids = article.pages_get(
        session,
        username,
        include_nonsub,
        sort_column,
        sort_direction,
        include,
        exclude,
        bounds,
    )

    pages = {}
    for index in indexes:
        start = index * config.articles_per_page
        end = start + config.articles_per_page
        previews = []
        for article_id in article_ids[start:end]:
            status, preview = get_article_preview(session, article_id, username)
            if status.is_error:
                return status, None
            previews.append(preview)
        pages[index] = previews
    return request_status.Status(request_status.StatusType.OK), pages

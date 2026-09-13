"""
Этот файл служит для хранения логики выполнения запросов, не связанной с изменениями в базах данных.
"""

import json
import time

from .db import user, article, comment
from . import config
from . import request_status


def get_article(session, article_id, username):
    """Собирает полную информацию о статье для страницы статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: пользователь, от чьего имени просматривается статья
            (используется для is_liked/is_disliked).

    Returns:
        Кортеж (`Status`, dict):
            - OK и данные статьи (см. api.api_article_get) — при успехе.
            - ERROR и `None` — если статья или связанные данные не найдены.
    """
    status, article_info = article.get(session, article_id)
    if status.is_error:
        return status, None
    status, author_preview = user.preview(session, article_info.author_username)
    if status.is_error:
        return status, None
    status, preview = article.preview(session, article_id)
    if status.is_error:
        return status, None
    status, likes = article.likes_count(session, article_id)
    if status.is_error:
        return status, None
    status, dislikes = article.dislikes_count(session, article_id)
    if status.is_error:
        return status, None
    status, rating = article.rating(session, article_id)
    if status.is_error:
        return status, None
    status, comments_count = article.comments_count(session, article_id)
    if status.is_error:
        return status, None
    status, comments = comment.from_article(session, article_id)
    if status.is_error:
        return status, None
    status, is_liked = article.is_liked(session, article_id, username)
    if status.is_error:
        return status, None
    status, is_disliked = article.is_disliked(session, article_id, username)
    if status.is_error:
        return status, None
    status, tags = article.tags(session, article_id)
    if status.is_error:
        return status, None
    return request_status.Status(request_status.StatusType.OK), {
        "creation_date": article_info.creation_date,
        "author_preview": author_preview,
        "title": article_info.title,
        "body": json.loads(article_info.body),
        "preview": preview,
        "likes": likes,
        "dislikes": dislikes,
        "rating": rating,
        "comments_count": comments_count,
        "comments": comments,
        "is_liked": is_liked,
        "is_disliked": is_disliked,
        "tags": tags,
    }


def post_article(session, author, title, body, preview, tags):
    """Публикует новую статью и создает её теги.

    Args:
        session: сессия SQLAlchemy.
        author: username автора.
        title: заголовок статьи.
        body: тело статьи.
        preview: контент предпоказа.
        tags: список тегов статьи.

    Returns:
        Кортеж (`Status`, int) — OK и id созданной статьи.
    """
    article_id = article.post(
        session=session, title=title, body=body, author=author, preview=preview
    )
    article.add_tags(session=session, tags=tags, article_id=article_id)
    return request_status.Status(request_status.StatusType.OK), article_id


def add_user(session, user_info):
    """Регистрирует нового пользователя.

    Args:
        session: сессия SQLAlchemy.
        user_info: словарь с полями username, nickname, password, email,
            avatar, description.

    Returns:
        `Status`:
            - OK — пользователь успешно создан.
            - ValueError — username или email уже заняты.
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


def update_user_info(session, username, data):
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
    for key in data:
        match key:
            case "avatar":
                status = user.update_avatar(session, username, data[key])
                if status.is_error:
                    return status
            case "sub-tags":
                for tag_name in data[key]:
                    status = user.sub_tag(session, username, tag_name)
                    if status.is_error:
                        return status
            case "blocked-tags":
                for tag_name in data[key]:
                    status = user.block_tag(session, username, tag_name)
                    if status.is_error:
                        return status
            case "sub-users":
                for sub in data[key]:
                    status = user.sub_user(session, username, sub)
                    if status.is_error:
                        return status
            case "blocked-users":
                for blocked_user in data[key]:
                    status = user.block_user(session, username, blocked_user)
                    if status.is_error:
                        return status
            case "nickname":
                status = user.update_nickname(session, username, data[key])
                if status.is_error:
                    return status
            case "email":
                status = user.update_email(session, username, data[key])
                if status.is_error:
                    return status
            case "description":
                status = user.update_description(session, username, data[key])
                if status.is_error:
                    return status
    return request_status.Status(request_status.StatusType.OK)


def login(session, parameters):
    """Проверяет пароль пользователя, найденного по username или email.

    Args:
        session: сессия SQLAlchemy.
        parameters: словарь с полями password и username и/или email.

    Returns:
        Кортеж (`Status`, bool):
            - OK и `True`/`False` — совпадает ли password с паролем
              найденного пользователя.
            - OK и `False` — если пользователь не найден.
    """
    password = parameters["password"]
    username = parameters["username"]
    email = parameters["email"]
    status, is_password_correct = user.check_password(
        session=session, password=password, username=username, email=email
    )
    return status, is_password_correct


def change_password(session, previous_password, new_password, username):
    """Меняет пароль пользователя, если previous_password верен.

    Args:
        session: сессия SQLAlchemy.
        previous_password: текущий пароль пользователя.
        new_password: новый пароль.
        username: имя пользователя.

    Returns:
        `Status`:
            - OK — пароль успешно изменен.
            - ValueError — previous_password неверен или пользователь не найден.
    """
    status, is_same = user.check_password(session, previous_password, username=username)
    if status.is_error:
        return status
    if not is_same:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg="Incorrect password!",
        )
    return user.change_password(session, new_password, username)


def article_dislike(session, article_id, username):
    """Ставит или снимает дизлайк username на статье.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: кто ставит дизлайк.

    Returns:
        `Status` операции.
    """
    status = article.dislike(session, article_id, username)
    return status


def article_like(session, article_id, username):
    """Ставит или снимает лайк username на статье.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: кто ставит лайк.

    Returns:
        `Status` операции.
    """
    status = article.like(session, article_id, username)
    return status


def comment_like(session, comment_id, username):
    """Ставит или снимает лайк username на комментарии.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: кто ставит лайк.

    Returns:
        `Status` операции.
    """
    status = comment.like(session, comment_id, username)
    return status


def comment_dislike(session, comment_id, username):
    """Ставит или снимает дизлайк username на комментарии.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: кто ставит дизлайк.

    Returns:
        `Status` операции.
    """
    status = comment.dislike(session, comment_id, username)
    return status


def add_comment(session, article_id, root, comment_text, username):
    """Добавляет комментарий (или ответ на комментарий) к статье.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        root: id родительского комментария или -1 для комментария верхнего уровня.
        comment_text: текст комментария.
        username: автор комментария.

    Returns:
        Кортеж (`Status`, int) — OK и id созданного комментария.
    """
    status, id = comment.add(session, article_id, root, comment_text, username)
    return status, id


def get_comment_data(session, comment_id, username, requested_data):
    """Собирает выбранные поля данных о комментарии.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: пользователь, от чьего имени запрашиваются данные (для
            is_liked/is_disliked).
        requested_data: список запрашиваемых полей (likes, dislikes, rating,
            creation_date, is_liked, is_disliked).

    Returns:
        Кортеж (`Status`, dict) — OK и словарь с запрошенными полями.
    """
    data: dict = {}
    for key in requested_data:
        match key:
            case "likes":
                status, data[key] = comment.likes_count(session, comment_id)
                if status.is_error:
                    return status, None
            case "dislikes":
                status, data[key] = comment.dislikes_count(session, comment_id)
                if status.is_error:
                    return status, None
            case "rating":
                status, data[key] = comment.rating(session, comment_id)
                if status.is_error:
                    return status, None
            case "creation_date":
                status, data[key] = comment.creation_date(session, comment_id)
                if status.is_error:
                    return status, None
            case "is_liked":
                status, data[key] = comment.is_liked(session, comment_id, username)
                if status.is_error:
                    return status, None
            case "is_disliked":
                status, data[key] = comment.is_disliked(session, comment_id, username)
                if status.is_error:
                    return status, None
    return request_status.Status(request_status.StatusType.OK), data


def get_article_data(session, article_id, username, requested_data):
    """Собирает выбранные поля данных о статье.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: пользователь, от чьего имени запрашиваются данные (для
            is_liked/is_disliked).
        requested_data: список запрашиваемых полей (likes, dislikes, rating,
            comments_count, creation_date, tags, is_liked, is_disliked).

    Returns:
        Кортеж (`Status`, dict) — OK и словарь с запрошенными полями.
    """
    data: dict = {}
    for key in requested_data:
        match key:
            case "likes":
                status, data[key] = article.likes_count(session, article_id)
                if status.is_error:
                    return status, None
            case "dislikes":
                status, data[key] = article.dislikes_count(session, article_id)
                if status.is_error:
                    return status, None
            case "rating":
                status, data[key] = article.rating(session, article_id)
                if status.is_error:
                    return status, None
            case "comments_count":
                status, data[key] = article.comments_count(session, article_id)
                if status.is_error:
                    return status, None
            case "creation_date":
                status, article_info = article.get(session, article_id)
                if status.is_error:
                    return status, None
                data[key] = article_info.creation_date
            case "tags":
                status, data[key] = article.tags(session, article_id)
                if status.is_error:
                    return status, None
            case "is_liked":
                status, data[key] = article.is_liked(session, article_id, username)
                if status.is_error:
                    return status, None
            case "is_disliked":
                status, data[key] = article.is_disliked(session, article_id, username)
                if status.is_error:
                    return status, None
    return request_status.Status(request_status.StatusType.OK), data


def get_user_data(session, username, requested_data):
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
    data: dict = {}
    for key in requested_data:
        match key:
            case "avatar":
                status, data[key] = user.get_avatar(session, username)
                if status.is_error:
                    return status, None
            case "name_history":
                status, data[key] = user.get_name_history(session, username)
                if status.is_error:
                    return status, None
            case "sub_tags":
                status, data[key] = user.get_sub_tag(session, username)
                if status.is_error:
                    return status, None
            case "blocked_tags":
                status, data[key] = user.get_blacklist_tag(session, username)
                if status.is_error:
                    return status, None
            case "sub_users":
                status, data[key] = user.get_sub_user(session, username)
                if status.is_error:
                    return status, None
            case "blocked_users":
                status, data[key] = user.get_blacklist_user(session, username)
                if status.is_error:
                    return status, None
            case "nickname":
                status, data[key] = user.get_nickname(session, username)
                if status.is_error:
                    return status, None
            case "email":
                status, data[key] = user.get_email(session, username)
                if status.is_error:
                    return status, None
            case "description":
                status, data[key] = user.get_description(session, username)
                if status.is_error:
                    return status, None
            case "creation_date":
                status, data[key] = user.get_creation_date(session, username)
                if status.is_error:
                    return status, None
            case "rating":
                status, data[key] = user.get_rating(session, username)
                if status.is_error:
                    return status, None
            case _:
                pass
    return request_status.Status(request_status.StatusType.OK), data


def get_article_preview(session, article_id, username):
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
    status, author_preview = user.preview(session, article_info.author_username)
    if status.is_error:
        return status, None
    status, preview_content = article.preview(session, article_id)
    if status.is_error:
        return status, None
    status, likes = article.likes_count(session, article_id)
    if status.is_error:
        return status, None
    status, dislikes = article.dislikes_count(session, article_id)
    if status.is_error:
        return status, None
    status, rating = article.rating(session, article_id)
    if status.is_error:
        return status, None
    status, comments_count = article.comments_count(session, article_id)
    if status.is_error:
        return status, None
    status, tags = article.tags(session, article_id)
    if status.is_error:
        return status, None
    status, is_liked = article.is_liked(session, article_id, username)
    if status.is_error:
        return status, None
    status, is_disliked = article.is_disliked(session, article_id, username)
    if status.is_error:
        return status, None
    return request_status.Status(request_status.StatusType.OK), {
        "id": article_id,
        "title": article_info.title,
        "creation_date": article_info.creation_date,
        "author_preview": author_preview,
        "preview_content": preview_content,
        "likes": likes,
        "dislikes": dislikes,
        "rating": rating,
        "comments_count": comments_count,
        "tags": tags,
        "is_liked": is_liked,
        "is_disliked": is_disliked,
    }


def pages_get(
    session,
    username,
    indexes,
    include_nonsub,
    sort_column,
    sort_direction,
    include,
    exclude,
    bounds,
):
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

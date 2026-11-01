"""
Этот файл служит для хранения логики работы с комментариями: добавление,
лайки/дизлайки и построение дерева ответов для статьи.
"""

from . import scheme
import time
from sqlalchemy import Row
from sqlalchemy.orm import Session

from .. import request_status


def is_comment_not_exist(session: Session, comment_id: int) -> bool:
    """Проверяет, существует ли комментарий с указанным id. Удалённый комментарий и
    комментарий удалённой статьи считаются несуществующими: лайкать их нельзя (см.
    decisions/0005-soft-delete.md).

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        `True`, если комментарий недоступен, иначе `False`.
    """
    comment = (
        session.query(scheme.Comment.id)
        .join(scheme.Article, scheme.Comment.article_id == scheme.Article.id)
        .where(
            scheme.Comment.id == comment_id,
            scheme.Comment.is_deleted.is_(False),
            scheme.Article.is_deleted.is_(False),
        )
        .scalar()
    )
    return comment is None


def is_deleted(session: Session, comment_id: int) -> bool:
    """Проверяет, отдаётся ли комментарий заглушкой. Комментарий удалённой статьи
    заглушкой не считается: он скрыт вместе со статьёй.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        `True`, если комментарий удалён, а его статья нет, иначе `False`.
    """
    comment = (
        session.query(scheme.Comment.id)
        .join(scheme.Article, scheme.Comment.article_id == scheme.Article.id)
        .where(
            scheme.Comment.id == comment_id,
            scheme.Comment.is_deleted.is_(True),
            scheme.Article.is_deleted.is_(False),
        )
        .scalar()
    )
    return comment is not None


def add(
    session: Session, article_id: int, parent_id: int, comment_text: str, username: str
) -> tuple[request_status.Status, int | None]:
    """Добавляет комментарий (или ответ на комментарий) к статье.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        parent_id: id родительского комментария этой же статьи, либо -1 для
            комментария верхнего уровня (в БД верхний уровень хранится как
            NULL — см. scheme.Comment.parent_id).
        comment_text: текст комментария.
        username: автор комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и id созданного комментария — при успехе.
            - InvalidParameters и `None` — если parent_id не -1 и не ссылается
              на существующий неудалённый комментарий этой статьи.
    """
    stored_parent_id = None if parent_id == -1 else parent_id
    if stored_parent_id is not None:
        parent_exists = (
            session.query(scheme.Comment)
            .where(
                scheme.Comment.id == stored_parent_id,
                scheme.Comment.article_id == article_id,
                scheme.Comment.is_deleted.is_(False),
            )
            .scalar()
        )
        if parent_exists is None:
            # 400, а не 404: URL запроса существует, неверна ссылка внутри тела.
            return (
                request_status.Status(
                    request_status.StatusType.ERROR,
                    error_type=request_status.ErrorType.InvalidParameters,
                    msg=f"Cannot find comment with id: {parent_id}",
                ),
                None,
            )
    comment = scheme.Comment(
        article_id=article_id,
        author_username=username,
        text=comment_text,
        parent_id=stored_parent_id,
        creation_date=round(time.time() * 1000),
    )
    session.add(comment)
    session.flush()
    return request_status.Status(request_status.StatusType.OK), comment.id


def delete(session: Session, comment_id: int, username: str) -> request_status.Status:
    """Мягко удаляет комментарий. Идемпотентно (это DELETE): автор может повторить
    вызов.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: кто удаляет.

    Returns:
        `Status`:
            - OK — комментарий удалён.
            - NotFound — комментария нет или удалена его статья.
            - Forbidden — вызывающий не автор комментария.
    """
    comment = (
        session.query(scheme.Comment)
        .join(scheme.Article, scheme.Comment.article_id == scheme.Article.id)
        .where(scheme.Comment.id == comment_id, scheme.Article.is_deleted.is_(False))
        .scalar()
    )
    if comment is None:
        return request_status.not_found("comment with id", comment_id)
    if comment.author_username != username:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.Forbidden,
            msg="User cannot delete someone else's comment",
        )
    comment.is_deleted = True
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def like(session: Session, comment_id: int, username: str) -> request_status.Status:
    """Ставит лайк username на комментарий, заодно снимая его дизлайк. Идемпотентно
    (это PUT): повторный вызов ничего не меняет.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: кто ставит лайк.

    Returns:
        `Status`:
            - OK — лайк стоит.
            - NotFound — комментарий не найден.
            - Forbidden — username является его автором.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.not_found("comment with id", comment_id)
    author_username = (
        session.query(scheme.Comment.author_username)
        .where(scheme.Comment.id == comment_id)
        .scalar()
    )
    if author_username == username:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.Forbidden,
            msg="User cannot like or dislike their own comment",
        )
    existing_like = (
        session.query(scheme.CommentLike)
        .where(
            scheme.CommentLike.comment_id == comment_id,
            scheme.CommentLike.username == username,
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.CommentDislike)
        .where(
            scheme.CommentDislike.comment_id == comment_id,
            scheme.CommentDislike.username == username,
        )
        .scalar()
    )
    if not existing_like:
        session.add(scheme.CommentLike(comment_id=comment_id, username=username))
    if existing_dislike:
        session.delete(existing_dislike)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def dislike(session: Session, comment_id: int, username: str) -> request_status.Status:
    """Ставит дизлайк username на комментарий, заодно снимая его лайк. Идемпотентно
    (это PUT): повторный вызов ничего не меняет.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: кто ставит дизлайк.

    Returns:
        `Status`:
            - OK — дизлайк стоит.
            - NotFound — комментарий не найден.
            - Forbidden — username является его автором.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.not_found("comment with id", comment_id)
    author_username = (
        session.query(scheme.Comment.author_username)
        .where(scheme.Comment.id == comment_id)
        .scalar()
    )
    if author_username == username:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.Forbidden,
            msg="User cannot like or dislike their own comment",
        )
    existing_like = (
        session.query(scheme.CommentLike)
        .where(
            scheme.CommentLike.comment_id == comment_id,
            scheme.CommentLike.username == username,
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.CommentDislike)
        .where(
            scheme.CommentDislike.comment_id == comment_id,
            scheme.CommentDislike.username == username,
        )
        .scalar()
    )
    if not existing_dislike:
        session.add(scheme.CommentDislike(comment_id=comment_id, username=username))
    if existing_like:
        session.delete(existing_like)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def remove_like(
    session: Session, comment_id: int, username: str
) -> request_status.Status:
    """Снимает лайк username с комментария. Идемпотентно (это DELETE): если лайка
    нет, это не ошибка. Проверка авторства не нужна: автор не может поставить
    лайк, значит снимать ему нечего.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: чей лайк снимается.

    Returns:
        `Status`:
            - OK — лайка больше нет.
            - NotFound — комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.not_found("comment with id", comment_id)
    session.query(scheme.CommentLike).where(
        scheme.CommentLike.comment_id == comment_id,
        scheme.CommentLike.username == username,
    ).delete()
    return request_status.Status(request_status.StatusType.OK)


def remove_dislike(
    session: Session, comment_id: int, username: str
) -> request_status.Status:
    """Снимает дизлайк username с комментария. Идемпотентно (это DELETE): если
    дизлайка нет, это не ошибка.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: чей дизлайк снимается.

    Returns:
        `Status`:
            - OK — дизлайка больше нет.
            - NotFound — комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.not_found("comment with id", comment_id)
    session.query(scheme.CommentDislike).where(
        scheme.CommentDislike.comment_id == comment_id,
        scheme.CommentDislike.username == username,
    ).delete()
    return request_status.Status(request_status.StatusType.OK)


def _tree_node(comment: Row, comments: list) -> dict:
    """Строит узел дерева комментариев вместе с его ответами.

    Args:
        comment: строка комментария из from_article.
        comments: плоский список всех комментариев статьи.

    Returns:
        dict с id, parent_id, is_deleted и answers. Автор и текст есть только у
        неудалённого комментария: заглушка лишь сохраняет ветку ответов.
    """
    node = {
        "id": comment.id,
        # -1 наружу для комментария верхнего уровня — см. scheme.Comment.parent_id.
        "parent_id": -1 if comment.parent_id is None else comment.parent_id,
        "is_deleted": comment.is_deleted,
        "answers": answers(comment.id, comments),
    }
    if not comment.is_deleted:
        node["author_username"] = comment.author_username
        node["text"] = comment.text
    return node


def answers(id: int, comments: list) -> list:
    """Рекурсивно строит дерево прямых и вложенных ответов на комментарий id.

    Args:
        id: id комментария, для которого собираются ответы.
        comments: плоский список всех комментариев статьи.

    Returns:
        Дерево ответов (list[dict]). Без `Status`: результат вкладывается прямо
        в JSON-ответ, а ошибиться здесь нечему, данные уже прочитаны.
    """
    return [
        _tree_node(comment, comments) for comment in comments if comment.parent_id == id
    ]


def from_article(
    session: Session, article_id: int
) -> tuple[request_status.Status, list]:
    """Строит дерево комментариев статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, list[dict]) — OK и список комментариев верхнего
        уровня, каждый со вложенным списком ответов.
    """
    comments = (
        session.query(
            scheme.Comment.author_username,
            scheme.Comment.id,
            scheme.Comment.parent_id,
            scheme.Comment.text,
            scheme.Comment.is_deleted,
        )
        .where(scheme.Comment.article_id == article_id)
        .all()
    )
    sorted_comments = [
        _tree_node(comment, comments)
        for comment in comments
        if comment.parent_id is None
    ]

    return request_status.Status(request_status.StatusType.OK), sorted_comments


def _count_likes(session: Session, comment_id: int) -> int:
    """Считает лайки комментария без проверки существования (для внутреннего переиспользования).

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Количество лайков.
    """
    return (
        session.query(scheme.CommentLike)
        .where(scheme.CommentLike.comment_id == comment_id)
        .count()
    )


def _count_dislikes(session: Session, comment_id: int) -> int:
    """Считает дизлайки комментария без проверки существования (для внутреннего переиспользования).

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Количество дизлайков.
    """
    return (
        session.query(scheme.CommentDislike)
        .where(scheme.CommentDislike.comment_id == comment_id)
        .count()
    )


def likes_count(
    session: Session, comment_id: int
) -> tuple[request_status.Status, int | None]:
    """Считает количество лайков комментария.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество лайков — если комментарий найден.
            - NotFound и `None` — если комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.not_found("comment with id", comment_id), None
    return request_status.Status(request_status.StatusType.OK), _count_likes(
        session, comment_id
    )


def dislikes_count(
    session: Session, comment_id: int
) -> tuple[request_status.Status, int | None]:
    """Считает количество дизлайков комментария.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество дизлайков — если комментарий найден.
            - NotFound и `None` — если комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.not_found("comment with id", comment_id), None
    return request_status.Status(request_status.StatusType.OK), _count_dislikes(
        session, comment_id
    )


def rating(
    session: Session, comment_id: int
) -> tuple[request_status.Status, int | None]:
    """Вычисляет рейтинг комментария (лайки минус дизлайки).

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и рейтинг — если комментарий найден.
            - NotFound и `None` — если комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.not_found("comment with id", comment_id), None
    rating_value = _count_likes(session, comment_id) - _count_dislikes(
        session, comment_id
    )
    return request_status.Status(request_status.StatusType.OK), rating_value


def creation_date(
    session: Session, comment_id: int
) -> tuple[request_status.Status, int | None]:
    """Возвращает дату создания комментария.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и дата создания (мс с 1970 года) — если комментарий найден.
            - NotFound и `None` — если комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.not_found("comment with id", comment_id), None
    date = (
        session.query(scheme.Comment.creation_date)
        .where(scheme.Comment.id == comment_id)
        .scalar()
    )

    return request_status.Status(request_status.StatusType.OK), date


def is_liked(
    session: Session, comment_id: int, username: str | None
) -> tuple[request_status.Status, bool]:
    """Проверяет, лайкнул ли username комментарий.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, bool):
            - OK и `True`/`False` — лайкнул ли username комментарий.
            - OK и `False` — если комментарий не существует.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(request_status.StatusType.OK), False
    return (
        request_status.Status(request_status.StatusType.OK),
        not session.query(scheme.CommentLike)
        .where(
            scheme.CommentLike.comment_id == comment_id,
            scheme.CommentLike.username == username,
        )
        .scalar()
        is None,
    )


def is_disliked(
    session: Session, comment_id: int, username: str | None
) -> tuple[request_status.Status, bool]:
    """Проверяет, дизлайкнул ли username комментарий.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, bool):
            - OK и `True`/`False` — дизлайкнул ли username комментарий.
            - OK и `False` — если комментарий не существует.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(request_status.StatusType.OK), False
    return (
        request_status.Status(request_status.StatusType.OK),
        not session.query(scheme.CommentDislike)
        .where(
            scheme.CommentDislike.comment_id == comment_id,
            scheme.CommentDislike.username == username,
        )
        .scalar()
        is None,
    )

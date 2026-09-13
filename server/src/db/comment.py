from . import scheme
import time
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import select, update, delete

from sqlalchemy import create_engine

from .. import request_status


def is_comment_not_exist(session: Session, comment_id):
    """Проверяет, существует ли комментарий с указанным id.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        `True`, если комментария не существует, иначе `False`.
    """
    comment = (
        session.query(scheme.Comment).where(scheme.Comment.id == comment_id).scalar()
    )
    return comment is None


def add(session: Session, article_id, root_id, comment_text, username):
    """Добавляет комментарий (или ответ на комментарий) к статье.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        root_id: id родительского комментария этой же статьи, либо -1 для
            комментария верхнего уровня.
        comment_text: текст комментария.
        username: автор комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и id созданного комментария — при успехе.
            - ValueError и `None` — если root_id не -1 и не ссылается на
              существующий комментарий этой статьи.
    """
    if root_id != -1:
        root_exists = (
            session.query(scheme.Comment)
            .where(
                scheme.Comment.id == root_id,
                scheme.Comment.article_id == article_id,
            )
            .scalar()
        )
        if root_exists is None:
            return (
                request_status.Status(
                    request_status.StatusType.ERROR,
                    error_type=request_status.ErrorType.ValueError,
                    msg=f"Cannot find comment with id: {root_id}",
                ),
                None,
            )
    comment = scheme.Comment(
        article_id=article_id,
        author_username=username,
        text=comment_text,
        root_id=root_id,
        creation_date=round(time.time() * 1000),
    )
    session.add(comment)
    session.flush()
    return request_status.Status(request_status.StatusType.OK), comment.id


def like(session: Session, comment_id, username):
    """Ставит лайк username на комментарий или снимает его, если он уже стоял
    (заодно снимая дизлайк того же пользователя).

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: кто ставит лайк.

    Returns:
        `Status`:
            - OK — лайк успешно поставлен/снят.
            - ValueError — комментарий не найден или username — его автор.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find comment with id: {comment_id}",
        )
    author_username = (
        session.query(scheme.Comment.author_username)
        .where(scheme.Comment.id == comment_id)
        .scalar()
    )
    if author_username == username:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg="User tries to like or dislike their own comment",
        )
    existing_like = (
        session.query(scheme.CommentLike)
        .where(
            scheme.CommentLike.comment_id == comment_id,
            scheme.CommentLike.author_username == username,
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.CommentDislike)
        .where(
            scheme.CommentDislike.comment_id == comment_id,
            scheme.CommentDislike.author_username == username,
        )
        .scalar()
    )
    if existing_like:
        session.delete(existing_like)
    else:
        like = scheme.CommentLike(comment_id=comment_id, author_username=username)
        session.add(like)
    if existing_dislike:
        session.delete(existing_dislike)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def dislike(session: Session, comment_id, username):
    """Ставит дизлайк username на комментарий или снимает его, если он уже стоял
    (заодно снимая лайк того же пользователя).

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.
        username: кто ставит дизлайк.

    Returns:
        `Status`:
            - OK — дизлайк успешно поставлен/снят.
            - ValueError — комментарий не найден или username — его автор.
    """
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find comment with id: {comment_id}",
        )
    author_username = (
        session.query(scheme.Comment.author_username)
        .where(scheme.Comment.id == comment_id)
        .scalar()
    )
    if author_username == username:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg="User tries to like or dislike their own comment",
        )
    existing_like = (
        session.query(scheme.CommentLike)
        .where(
            scheme.CommentLike.comment_id == comment_id,
            scheme.CommentLike.author_username == username,
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.CommentDislike)
        .where(
            scheme.CommentDislike.comment_id == comment_id,
            scheme.CommentDislike.author_username == username,
        )
        .scalar()
    )
    if existing_dislike:
        session.delete(existing_dislike)
    else:
        dislike = scheme.CommentDislike(comment_id=comment_id, author_username=username)
        session.add(dislike)
    if existing_like:
        session.delete(existing_like)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def answers(id, comments):
    """Рекурсивно строит дерево прямых и вложенных ответов на комментарий id.

    Args:
        id: id комментария, для которого собираются ответы.
        comments: плоский список комментариев (кортежи author_username, id,
            root_id, text).

    Returns:
        Кортеж (`Status`, list[dict]) — OK и дерево ответов.
    """
    comment_answers = []
    for i, comment in enumerate(comments):
        if comment[2] == id:
            comment_answers.append(
                {
                    "author_username": comment[0],
                    "id": comment[1],
                    "root_id": comment[2],
                    "text": comment[3],
                    "answers": answers(comment[1], comments),
                }
            )
    return request_status.Status(request_status.StatusType.OK), comment_answers


def from_article(session: Session, article_id):
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
            scheme.Comment.root_id,
            scheme.Comment.text,
        )
        .where(scheme.Comment.article_id == article_id)
        .all()
    )
    sorted_comments = []
    for comment in comments:
        if comment[2] == -1:
            sorted_comments.append(
                {
                    "author_username": comment[0],
                    "id": comment[1],
                    "root_id": comment[2],
                    "text": comment[3],
                    "answers": answers(comment[1], comments),
                }
            )

    return request_status.Status(request_status.StatusType.OK), sorted_comments


def likes_count(session: Session, comment_id):
    """Считает количество лайков комментария.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество лайков — если комментарий найден.
            - ValueError и `None` — если комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find comment with id: {comment_id}",
            ),
            None,
        )
    likes = (
        session.query(scheme.CommentLike)
        .where(scheme.CommentLike.comment_id == comment_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), likes


def dislikes_count(session: Session, comment_id):
    """Считает количество дизлайков комментария.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество дизлайков — если комментарий найден.
            - ValueError и `None` — если комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find comment with id: {comment_id}",
            ),
            None,
        )
    dislikes = (
        session.query(scheme.CommentDislike)
        .where(scheme.CommentDislike.comment_id == comment_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), dislikes


def rating(session: Session, comment_id):
    """Вычисляет рейтинг комментария (лайки минус дизлайки).

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и рейтинг — если комментарий найден.
            - ValueError и `None` — если комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find comment with id: {comment_id}",
            ),
            None,
        )
    likes = (
        session.query(scheme.CommentLike)
        .where(scheme.CommentLike.comment_id == comment_id)
        .count()
    )
    dislikes = (
        session.query(scheme.CommentDislike)
        .where(scheme.CommentDislike.comment_id == comment_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), likes - dislikes


def creation_date(session: Session, comment_id):
    """Возвращает дату создания комментария.

    Args:
        session: сессия SQLAlchemy.
        comment_id: id комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и дата создания (мс с 1970 года) — если комментарий найден.
            - ValueError и `None` — если комментарий не найден.
    """
    if is_comment_not_exist(session, comment_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find comment with id: {comment_id}",
            ),
            None,
        )
    date = (
        session.query(scheme.Comment.creation_date)
        .where(scheme.Comment.id == comment_id)
        .scalar()
    )

    return request_status.Status(request_status.StatusType.OK), date


def is_liked(session: Session, comment_id, username):
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
            scheme.CommentLike.author_username == username,
        )
        .scalar()
        is None,
    )


def is_disliked(session: Session, comment_id, username):
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
            scheme.CommentDislike.author_username == username,
        )
        .scalar()
        is None,
    )

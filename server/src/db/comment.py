"""
Этот файл служит для хранения логики работы с комментариями: добавление,
лайки/дизлайки и построение дерева ответов для статьи.
"""

from . import scheme
import time
from sqlalchemy.orm import Session

from .. import request_status


def is_comment_not_exist(session: Session, comment_id: int) -> bool:
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


def add(
    session: Session, article_id: int, root_id: int, comment_text: str, username: str
) -> tuple[request_status.Status, int | None]:
    """Добавляет комментарий (или ответ на комментарий) к статье.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        root_id: id родительского комментария этой же статьи, либо -1 для
            комментария верхнего уровня (в БД верхний уровень хранится как
            NULL — см. scheme.Comment.root_id).
        comment_text: текст комментария.
        username: автор комментария.

    Returns:
        Кортеж (`Status`, int):
            - OK и id созданного комментария — при успехе.
            - InvalidParameters и `None` — если root_id не -1 и не ссылается
              на существующий комментарий этой статьи.
    """
    stored_root_id = None if root_id == -1 else root_id
    if stored_root_id is not None:
        root_exists = (
            session.query(scheme.Comment)
            .where(
                scheme.Comment.id == stored_root_id,
                scheme.Comment.article_id == article_id,
            )
            .scalar()
        )
        if root_exists is None:
            # 400, а не 404: URL запроса существует, неверна ссылка внутри тела.
            return (
                request_status.Status(
                    request_status.StatusType.ERROR,
                    error_type=request_status.ErrorType.InvalidParameters,
                    msg=f"Cannot find comment with id: {root_id}",
                ),
                None,
            )
    comment = scheme.Comment(
        article_id=article_id,
        author_username=username,
        text=comment_text,
        root_id=stored_root_id,
        creation_date=round(time.time() * 1000),
    )
    session.add(comment)
    session.flush()
    return request_status.Status(request_status.StatusType.OK), comment.id


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
    if not existing_like:
        session.add(scheme.CommentLike(comment_id=comment_id, author_username=username))
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
    if not existing_dislike:
        session.add(
            scheme.CommentDislike(comment_id=comment_id, author_username=username)
        )
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
        scheme.CommentLike.author_username == username,
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
        scheme.CommentDislike.author_username == username,
    ).delete()
    return request_status.Status(request_status.StatusType.OK)


def answers(id: int, comments: list) -> list:
    """Рекурсивно строит дерево прямых и вложенных ответов на комментарий id.

    Args:
        id: id комментария, для которого собираются ответы.
        comments: плоский список комментариев (кортежи author_username, id,
            root_id, text).

    Returns:
        Дерево ответов (list[dict]). Без `Status`: результат вкладывается прямо
        в JSON-ответ, а ошибиться здесь нечему, данные уже прочитаны.
    """
    comment_answers = []
    for i, comment in enumerate(comments):
        if comment[2] == id:
            comment_answers.append(
                {
                    "author_username": comment[0],
                    "id": comment[1],
                    # -1 наружу для комментария верхнего уровня — см. scheme.Comment.root_id.
                    "root_id": -1 if comment[2] is None else comment[2],
                    "text": comment[3],
                    "answers": answers(comment[1], comments),
                }
            )
    return comment_answers


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
            scheme.Comment.root_id,
            scheme.Comment.text,
        )
        .where(scheme.Comment.article_id == article_id)
        .all()
    )
    sorted_comments = []
    for comment in comments:
        if comment[2] is None:
            sorted_comments.append(
                {
                    "author_username": comment[0],
                    "id": comment[1],
                    # -1 наружу для комментария верхнего уровня — см. scheme.Comment.root_id.
                    "root_id": -1,
                    "text": comment[3],
                    "answers": answers(comment[1], comments),
                }
            )

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
    session: Session, comment_id: int, username: str
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
            scheme.CommentLike.author_username == username,
        )
        .scalar()
        is None,
    )


def is_disliked(
    session: Session, comment_id: int, username: str
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
            scheme.CommentDislike.author_username == username,
        )
        .scalar()
        is None,
    )

from . import scheme
from .. import config
from .. import request_status
import json
import time
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from sqlalchemy import select, update, delete, or_, false


def is_article_not_exist(session: Session, article_id):
    """Проверяет, существует ли статья с указанным id.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        `True`, если статьи не существует, иначе `False`.
    """
    article = (
        session.query(scheme.Article).where(scheme.Article.id == article_id).scalar()
    )
    return article is None


def post(session, title, body, author, preview):
    """Создает статью и её предпоказ.

    Args:
        session: сессия SQLAlchemy.
        title: заголовок статьи.
        body: тело статьи (сериализуется в JSON).
        author: username автора.
        preview: контент предпоказа (сериализуется в JSON).

    Returns:
        id созданной статьи.
    """
    article = scheme.Article(
        title=title,
        body=json.dumps(body),
        author_username=author,
        creation_date=round(time.time() * 1000),
    )
    session.add(article)
    session.flush()
    article_preview = scheme.ArticlePreview(
        article_id=article.id,
        preview_content=json.dumps(preview),
    )
    session.add(article_preview)
    session.flush()
    return article.id


def add_tags(session, tags, article_id):
    """Создает по строке в article_tags для каждого тега из tags.

    Args:
        session: сессия SQLAlchemy.
        tags: список тегов.
        article_id: id статьи, которой принадлежат теги.

    Returns:
        None
    """
    for tag in tags:
        article_tag = scheme.ArticleTag(tag_name=tag, article_id=article_id)
        session.add(article_tag)
    session.flush()


def is_liked(session: Session, article_id, username):
    """Проверяет, лайкнул ли username статью.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, bool):
            - OK и `True`/`False` — лайкнул ли username статью.
            - OK и `False` — если статья не существует.
    """
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.OK), False
    return (
        request_status.Status(request_status.StatusType.OK),
        not session.query(scheme.ArticleLike)
        .where(
            scheme.ArticleLike.article_id == article_id,
            scheme.ArticleLike.author_username == username,
        )
        .scalar()
        is None,
    )


def is_disliked(session: Session, article_id, username):
    """Проверяет, дизлайкнул ли username статью.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: имя пользователя.

    Returns:
        Кортеж (`Status`, bool):
            - OK и `True`/`False` — дизлайкнул ли username статью.
            - OK и `False` — если статья не существует.
    """
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.OK), False
    return (
        request_status.Status(request_status.StatusType.OK),
        not session.query(scheme.ArticleDislike)
        .where(
            scheme.ArticleDislike.article_id == article_id,
            scheme.ArticleDislike.author_username == username,
        )
        .scalar()
        is None,
    )


def likes_count(session: Session, article_id):
    """Считает количество лайков статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество лайков — если статья найдена.
            - ValueError и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find article with id: {article_id}",
            ),
            None,
        )
    likes = (
        session.query(scheme.ArticleLike)
        .where(scheme.ArticleLike.article_id == article_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), likes


def dislikes_count(session: Session, article_id):
    """Считает количество дизлайков статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество дизлайков — если статья найдена.
            - ValueError и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find article with id: {article_id}",
            ),
            None,
        )
    dislikes = (
        session.query(scheme.ArticleDislike)
        .where(scheme.ArticleDislike.article_id == article_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), dislikes


def rating(session: Session, article_id):
    """Вычисляет рейтинг статьи (лайки минус дизлайки).

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, int):
            - OK и рейтинг — если статья найдена.
            - ValueError и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find article with id: {article_id}",
            ),
            None,
        )
    likes = (
        session.query(scheme.ArticleLike)
        .where(scheme.ArticleLike.article_id == article_id)
        .count()
    )
    dislikes = (
        session.query(scheme.ArticleDislike)
        .where(scheme.ArticleDislike.article_id == article_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), likes - dislikes


def comments_count(session: Session, article_id):
    """Считает количество комментариев статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество комментариев — если статья найдена.
            - ValueError и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find article with id: {article_id}",
            ),
            None,
        )
    comments_count = (
        session.query(scheme.Comment)
        .where(scheme.Comment.article_id == article_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), comments_count


def get(session: Session, article_id):
    """Возвращает ORM-объект статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, Article):
            - OK и объект статьи — если статья найдена.
            - ValueError и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find article with id: {article_id}",
            ),
            None,
        )
    article = (
        session.query(scheme.Article).where(scheme.Article.id == article_id).scalar()
    )
    return request_status.Status(request_status.StatusType.OK), article


def preview(session: Session, article_id):
    """Возвращает содержимое предпоказа статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, dict):
            - OK и содержимое предпоказа — если статья найдена.
            - ValueError и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find article with id: {article_id}",
            ),
            None,
        )
    preview = (
        session.query(scheme.ArticlePreview.preview_content)
        .where(scheme.ArticlePreview.article_id == article_id)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), json.loads(preview)


def tags(session: Session, article_id):
    """Возвращает теги статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список тегов — если статья найдена.
            - ValueError и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.ValueError,
                msg=f"Cannot find article with id: {article_id}",
            ),
            None,
        )
    tags = (
        session.query(scheme.ArticleTag.tag_name)
        .where(scheme.ArticleTag.article_id == article_id)
        .all()
    )
    return request_status.Status(request_status.StatusType.OK), [tag[0] for tag in tags]


def like(session: Session, article_id, username):
    """Ставит лайк username на статью или снимает его, если он уже стоял
    (заодно снимая дизлайк того же пользователя).

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: кто ставит лайк.

    Returns:
        `Status`:
            - OK — лайк успешно поставлен/снят.
            - ValueError — статья не найдена или username — её автор.
    """
    if is_article_not_exist(session, article_id):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find article with id: {article_id}",
        )
    author_username = (
        session.query(scheme.Article.author_username)
        .where(scheme.Article.id == article_id)
        .scalar()
    )
    if author_username == username:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg="User tries to like or dislike their own article",
        )
    existing_like = (
        session.query(scheme.ArticleLike)
        .where(
            scheme.ArticleLike.article_id == article_id,
            scheme.ArticleLike.author_username == username,
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.ArticleDislike)
        .where(
            scheme.ArticleDislike.article_id == article_id,
            scheme.ArticleDislike.author_username == username,
        )
        .scalar()
    )
    if existing_like:
        session.delete(existing_like)
    else:
        like = scheme.ArticleLike(article_id=article_id, author_username=username)
        session.add(like)
    if existing_dislike:
        session.delete(existing_dislike)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def dislike(session: Session, article_id, username):
    """Ставит дизлайк username на статью или снимает его, если он уже стоял
    (заодно снимая лайк того же пользователя).

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: кто ставит дизлайк.

    Returns:
        `Status`:
            - OK — дизлайк успешно поставлен/снят.
            - ValueError — статья не найдена или username — её автор.
    """
    if is_article_not_exist(session, article_id):
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg=f"Cannot find article with id: {article_id}",
        )
    author_username = (
        session.query(scheme.Article.author_username)
        .where(scheme.Article.id == article_id)
        .scalar()
    )
    if author_username == username:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.ValueError,
            msg="User tries to like or dislike their own article",
        )
    existing_like = (
        session.query(scheme.ArticleLike)
        .where(
            scheme.ArticleLike.article_id == article_id,
            scheme.ArticleLike.author_username == username,
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.ArticleDislike)
        .where(
            scheme.ArticleDislike.article_id == article_id,
            scheme.ArticleDislike.author_username == username,
        )
        .scalar()
    )
    if existing_dislike:
        session.delete(existing_dislike)
    else:
        dislike = scheme.ArticleDislike(article_id=article_id, author_username=username)
        session.add(dislike)
    if existing_like:
        session.delete(existing_like)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def _rating_expression():
    """Строит SQL-выражение рейтинга статьи (likes - dislikes).

    Args:
        None

    Returns:
        SQLAlchemy-выражение, пригодное для order_by/where на уровне запроса.
    """
    likes = (
        select(sqlfunc.count(scheme.ArticleLike.article_id))
        .where(scheme.ArticleLike.article_id == scheme.Article.id)
        .scalar_subquery()
    )
    dislikes = (
        select(sqlfunc.count(scheme.ArticleDislike.article_id))
        .where(scheme.ArticleDislike.article_id == scheme.Article.id)
        .scalar_subquery()
    )
    return likes - dislikes


def pages_get(
    session: Session,
    username,
    include_nonsub,
    sort_column,
    sort_direction,
    include,
    exclude,
    bounds,
):
    """Строит отсортированный и отфильтрованный список id статей для ленты.

    Args:
        session: сессия SQLAlchemy.
        username: пользователь, для которого формируется лента ("unlogged_user"
            для неавторизованного).
        include_nonsub: если `False`, оставляет только статьи по подпискам username.
        sort_column: "creation_date" или "rating".
        sort_direction: "ascending" или "descending".
        include: словарь с ключами "tags"/"authors" — статья должна им соответствовать.
        exclude: словарь с ключами "tags"/"authors" — статьи с ними исключаются.
        bounds: словарь с ключами "upper"/"lower" — границы sort_column.

    Returns:
        Список id статей в порядке сортировки (без пагинации — на страницы
        список режет backend.pages_get).
    """
    query = session.query(scheme.Article.id)

    is_logged_in = username != "unlogged_user"

    exclude_authors = set(exclude.get("authors") or [])
    exclude_tags = set(exclude.get("tags") or [])

    if is_logged_in:
        blocked_authors = (
            session.query(scheme.UserBlacklist.blocked_user)
            .where(scheme.UserBlacklist.username == username)
            .all()
        )
        exclude_authors.update(row[0] for row in blocked_authors)

        blocked_tags = (
            session.query(scheme.TagBlacklist.tag_name)
            .where(scheme.TagBlacklist.username == username)
            .all()
        )
        exclude_tags.update(row[0] for row in blocked_tags)

    if exclude_authors:
        query = query.where(scheme.Article.author_username.notin_(exclude_authors))
    if exclude_tags:
        query = query.where(
            scheme.Article.id.notin_(
                select(scheme.ArticleTag.article_id).where(
                    scheme.ArticleTag.tag_name.in_(exclude_tags)
                )
            )
        )

    include_authors = include.get("authors")
    if include_authors:
        query = query.where(scheme.Article.author_username.in_(include_authors))

    include_tags = include.get("tags")
    if include_tags:
        include_tags = set(include_tags)
        query = query.where(
            scheme.Article.id.in_(
                select(scheme.ArticleTag.article_id)
                .where(scheme.ArticleTag.tag_name.in_(include_tags))
                .group_by(scheme.ArticleTag.article_id)
                .having(
                    sqlfunc.count(scheme.ArticleTag.tag_name.distinct())
                    == len(include_tags)
                )
            )
        )

    if include_nonsub is False and is_logged_in:
        subscribed_authors = [
            row[0]
            for row in session.query(scheme.UserSubscription.subscribed_user)
            .where(scheme.UserSubscription.username == username)
            .all()
        ]
        subscribed_tags = [
            row[0]
            for row in session.query(scheme.TagSubscription.tag_name)
            .where(scheme.TagSubscription.username == username)
            .all()
        ]

        subscription_filters = []
        if subscribed_authors:
            subscription_filters.append(
                scheme.Article.author_username.in_(subscribed_authors)
            )
        if subscribed_tags:
            subscription_filters.append(
                scheme.Article.id.in_(
                    select(scheme.ArticleTag.article_id).where(
                        scheme.ArticleTag.tag_name.in_(subscribed_tags)
                    )
                )
            )

        if subscription_filters:
            query = query.where(or_(*subscription_filters))
        else:
            query = query.where(false())

    effective_sort_column = (
        sort_column if sort_column in ("rating", "creation_date") else "creation_date"
    )
    effective_sort_direction = (
        sort_direction
        if sort_direction in ("ascending", "descending")
        else "descending"
    )

    if bounds:
        upper = bounds.get("upper")
        lower = bounds.get("lower")
        if effective_sort_column == "rating":
            rating_expr = _rating_expression()
            if upper is not None:
                query = query.where(rating_expr < upper)
            if lower is not None:
                query = query.where(rating_expr > lower)
        else:
            if upper is not None:
                query = query.where(scheme.Article.creation_date < upper)
            if lower is not None:
                query = query.where(scheme.Article.creation_date > lower)

    if effective_sort_column == "rating":
        order_expr = _rating_expression()
    else:
        order_expr = scheme.Article.creation_date
    query = query.order_by(
        order_expr.desc()
        if effective_sort_direction == "descending"
        else order_expr.asc()
    )

    return [row[0] for row in query.all()]

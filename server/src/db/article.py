"""
Этот файл служит для хранения логики работы со статьями: публикация, лайки/дизлайки,
теги, превью и построение отфильтрованной/отсортированной ленты (pages_get).
"""

from . import scheme
from .. import request_status
import json
import time
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from sqlalchemy import ColumnElement, select, or_, false
from sqlalchemy.exc import IntegrityError


def is_article_not_exist(session: Session, article_id: int) -> bool:
    """Проверяет, существует ли статья с указанным id. Удалённая статья считается
    несуществующей: все методы работы со статьёй идут через эту проверку, поэтому к
    ней нельзя обратиться (см. decisions/0005-soft-delete.md).

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        `True`, если статьи не существует или она удалена, иначе `False`.
    """
    article = (
        session.query(scheme.Article)
        .where(scheme.Article.id == article_id, scheme.Article.is_deleted.is_(False))
        .scalar()
    )
    return article is None


def post(session: Session, title: str, body: dict, author: str, preview: dict) -> int:
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
        # ensure_ascii=False: иначе каждая русская буква хранилась бы как \uXXXX и
        # занимала 6 байт вместо 2.
        body=json.dumps(body, ensure_ascii=False),
        author_username=author,
        creation_date=round(time.time() * 1000),
    )
    session.add(article)
    session.flush()
    article_preview = scheme.ArticlePreview(
        article_id=article.id,
        preview_content=json.dumps(preview, ensure_ascii=False),
    )
    session.add(article_preview)
    session.flush()
    return article.id


def delete(session: Session, article_id: int, username: str) -> request_status.Status:
    """Мягко удаляет статью. Идемпотентно (это DELETE): автор может повторить вызов.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: кто удаляет.

    Returns:
        `Status`:
            - OK — статья удалена.
            - NotFound — статьи нет, либо она удалена и вызывающий не её автор:
              посторонний не должен узнать, что такая статья была.
            - Forbidden — статья не удалена и вызывающий не её автор.
    """
    article = (
        session.query(scheme.Article).where(scheme.Article.id == article_id).scalar()
    )
    is_author = article is not None and article.author_username == username
    if article is None or (article.is_deleted and not is_author):
        return request_status.not_found("article with id", article_id)
    if not is_author:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.Forbidden,
            msg="User cannot delete someone else's article",
        )
    article.is_deleted = True
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def add_tags(
    session: Session, tags: list[str], article_id: int
) -> request_status.Status:
    """Создает по строке в article_tags для каждого тега из tags.

    Дубликаты ловятся по первичному ключу, а не сравнением в Python: одинаковость
    тегов определяет правило сравнения колонки в БД (например, без учёта регистра),
    и повторять его в коде значило бы рано или поздно разойтись с ним.

    Args:
        session: сессия SQLAlchemy.
        tags: список тегов.
        article_id: id статьи, которой принадлежат теги.

    Returns:
        `Status`:
            - OK — теги созданы.
            - InvalidParameters — в tags есть одинаковые теги. Откат транзакции,
              в том числе самой статьи, делает API-метод.
    """
    session.add_all(
        scheme.ArticleTag(tag_name=tag, article_id=article_id) for tag in tags
    )
    try:
        session.flush()
    except IntegrityError:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.InvalidParameters,
            msg="Article tags must be unique",
            errors=[{"name": "tags", "reason": "must not contain duplicates"}],
        )
    return request_status.Status(request_status.StatusType.OK)


def is_liked(
    session: Session, article_id: int, username: str | None
) -> tuple[request_status.Status, bool]:
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
            scheme.ArticleLike.username == username,
        )
        .scalar()
        is None,
    )


def is_disliked(
    session: Session, article_id: int, username: str | None
) -> tuple[request_status.Status, bool]:
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
            scheme.ArticleDislike.username == username,
        )
        .scalar()
        is None,
    )


def _count_likes(session: Session, article_id: int) -> int:
    """Считает лайки статьи без проверки существования (для внутреннего переиспользования).

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Количество лайков.
    """
    return (
        session.query(scheme.ArticleLike)
        .where(scheme.ArticleLike.article_id == article_id)
        .count()
    )


def _count_dislikes(session: Session, article_id: int) -> int:
    """Считает дизлайки статьи без проверки существования (для внутреннего переиспользования).

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Количество дизлайков.
    """
    return (
        session.query(scheme.ArticleDislike)
        .where(scheme.ArticleDislike.article_id == article_id)
        .count()
    )


def likes_count(
    session: Session, article_id: int
) -> tuple[request_status.Status, int | None]:
    """Считает количество лайков статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество лайков — если статья найдена.
            - NotFound и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id), None
    return request_status.Status(request_status.StatusType.OK), _count_likes(
        session, article_id
    )


def dislikes_count(
    session: Session, article_id: int
) -> tuple[request_status.Status, int | None]:
    """Считает количество дизлайков статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество дизлайков — если статья найдена.
            - NotFound и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id), None
    return request_status.Status(request_status.StatusType.OK), _count_dislikes(
        session, article_id
    )


def rating(
    session: Session, article_id: int
) -> tuple[request_status.Status, int | None]:
    """Вычисляет рейтинг статьи (лайки минус дизлайки).

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, int):
            - OK и рейтинг — если статья найдена.
            - NotFound и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id), None
    rating_value = _count_likes(session, article_id) - _count_dislikes(
        session, article_id
    )
    return request_status.Status(request_status.StatusType.OK), rating_value


def comments_count(
    session: Session, article_id: int
) -> tuple[request_status.Status, int | None]:
    """Считает количество комментариев статьи, не считая удалённые: заглушка
    нужна только для сохранения ветки ответов.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, int):
            - OK и количество комментариев — если статья найдена.
            - NotFound и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id), None
    comments_count = (
        session.query(scheme.Comment)
        .where(
            scheme.Comment.article_id == article_id,
            scheme.Comment.is_deleted.is_(False),
        )
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), comments_count


def get(
    session: Session, article_id: int
) -> tuple[request_status.Status, scheme.Article | None]:
    """Возвращает ORM-объект статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, Article):
            - OK и объект статьи — если статья найдена.
            - NotFound и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id), None
    article = (
        session.query(scheme.Article).where(scheme.Article.id == article_id).scalar()
    )
    return request_status.Status(request_status.StatusType.OK), article


def preview(
    session: Session, article_id: int
) -> tuple[request_status.Status, dict | None]:
    """Возвращает содержимое предпоказа статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, dict):
            - OK и содержимое предпоказа — если статья найдена.
            - NotFound и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id), None
    preview = (
        session.query(scheme.ArticlePreview.preview_content)
        .where(scheme.ArticlePreview.article_id == article_id)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), json.loads(preview)


def tags(
    session: Session, article_id: int
) -> tuple[request_status.Status, list[str] | None]:
    """Возвращает теги статьи.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.

    Returns:
        Кортеж (`Status`, list[str]):
            - OK и список тегов — если статья найдена.
            - NotFound и `None` — если статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id), None
    tags = (
        session.query(scheme.ArticleTag.tag_name)
        .where(scheme.ArticleTag.article_id == article_id)
        .all()
    )
    return request_status.Status(request_status.StatusType.OK), [tag[0] for tag in tags]


def like(session: Session, article_id: int, username: str) -> request_status.Status:
    """Ставит лайк username на статью, заодно снимая его дизлайк. Идемпотентно
    (это PUT): повторный вызов ничего не меняет.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: кто ставит лайк.

    Returns:
        `Status`:
            - OK — лайк стоит.
            - NotFound — статья не найдена.
            - Forbidden — username является её автором.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id)
    author_username = (
        session.query(scheme.Article.author_username)
        .where(scheme.Article.id == article_id)
        .scalar()
    )
    if author_username == username:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.Forbidden,
            msg="User cannot like or dislike their own article",
        )
    existing_like = (
        session.query(scheme.ArticleLike)
        .where(
            scheme.ArticleLike.article_id == article_id,
            scheme.ArticleLike.username == username,
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.ArticleDislike)
        .where(
            scheme.ArticleDislike.article_id == article_id,
            scheme.ArticleDislike.username == username,
        )
        .scalar()
    )
    if not existing_like:
        session.add(scheme.ArticleLike(article_id=article_id, username=username))
    if existing_dislike:
        session.delete(existing_dislike)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def dislike(session: Session, article_id: int, username: str) -> request_status.Status:
    """Ставит дизлайк username на статью, заодно снимая его лайк. Идемпотентно
    (это PUT): повторный вызов ничего не меняет.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: кто ставит дизлайк.

    Returns:
        `Status`:
            - OK — дизлайк стоит.
            - NotFound — статья не найдена.
            - Forbidden — username является её автором.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id)
    author_username = (
        session.query(scheme.Article.author_username)
        .where(scheme.Article.id == article_id)
        .scalar()
    )
    if author_username == username:
        return request_status.Status(
            request_status.StatusType.ERROR,
            error_type=request_status.ErrorType.Forbidden,
            msg="User cannot like or dislike their own article",
        )
    existing_like = (
        session.query(scheme.ArticleLike)
        .where(
            scheme.ArticleLike.article_id == article_id,
            scheme.ArticleLike.username == username,
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.ArticleDislike)
        .where(
            scheme.ArticleDislike.article_id == article_id,
            scheme.ArticleDislike.username == username,
        )
        .scalar()
    )
    if not existing_dislike:
        session.add(scheme.ArticleDislike(article_id=article_id, username=username))
    if existing_like:
        session.delete(existing_like)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def remove_like(
    session: Session, article_id: int, username: str
) -> request_status.Status:
    """Снимает лайк username с статьи. Идемпотентно (это DELETE): если лайка
    нет, это не ошибка. Проверка авторства не нужна: автор не может поставить
    лайк, значит снимать ему нечего.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: чей лайк снимается.

    Returns:
        `Status`:
            - OK — лайка больше нет.
            - NotFound — статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id)
    session.query(scheme.ArticleLike).where(
        scheme.ArticleLike.article_id == article_id,
        scheme.ArticleLike.username == username,
    ).delete()
    return request_status.Status(request_status.StatusType.OK)


def remove_dislike(
    session: Session, article_id: int, username: str
) -> request_status.Status:
    """Снимает дизлайк username с статьи. Идемпотентно (это DELETE): если
    дизлайка нет, это не ошибка.

    Args:
        session: сессия SQLAlchemy.
        article_id: id статьи.
        username: чей дизлайк снимается.

    Returns:
        `Status`:
            - OK — дизлайка больше нет.
            - NotFound — статья не найдена.
    """
    if is_article_not_exist(session, article_id):
        return request_status.not_found("article with id", article_id)
    session.query(scheme.ArticleDislike).where(
        scheme.ArticleDislike.article_id == article_id,
        scheme.ArticleDislike.username == username,
    ).delete()
    return request_status.Status(request_status.StatusType.OK)


def _rating_expression() -> ColumnElement:
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
    username: str | None,
    include_nonsub: bool,
    sort_column: str,
    sort_direction: str,
    include: dict,
    exclude: dict,
    bounds: dict,
) -> list[int]:
    """Строит отсортированный и отфильтрованный список id статей для ленты.

    Args:
        session: сессия SQLAlchemy.
        username: пользователь, для которого формируется лента (`None` для
            неавторизованного).
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
    query = session.query(scheme.Article.id).where(scheme.Article.is_deleted.is_(False))

    is_logged_in = username is not None

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

    order_expr = (
        _rating_expression()
        if effective_sort_column == "rating"
        else scheme.Article.creation_date
    )

    if bounds:
        upper = bounds.get("upper")
        lower = bounds.get("lower")
        if upper is not None:
            query = query.where(order_expr < upper)
        if lower is not None:
            query = query.where(order_expr > lower)
    query = query.order_by(
        order_expr.desc()
        if effective_sort_direction == "descending"
        else order_expr.asc()
    )

    return [row[0] for row in query.all()]

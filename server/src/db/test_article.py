"""
Этот файл служит для хранения unit-тестов src/db/article.py на настоящей MySQL:
реакций, мягкого удаления, тегов и фильтров ленты.
"""

from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from src.db import article, scheme, user
from src.request_status import ErrorType
from src.test_helpers import assert_error_status


def _post(session: Session, author: str, creation_date: int = 0) -> int:
    """Создаёт статью с заданной датой, чтобы порядок в ленте не зависел от часов.

    Args:
        session: сессия SQLAlchemy.
        author: username автора.
        creation_date: дата создания, мс с 1970 года.

    Returns:
        id созданной статьи.
    """
    article_id = article.post(session, "title", {}, author, {})
    session.get(scheme.Article, article_id).creation_date = creation_date
    session.flush()
    return article_id


def _feed(session: Session, **overrides: object) -> list[int]:
    """Запрашивает ленту, задавая только важные для теста параметры.

    Args:
        session: сессия SQLAlchemy.
        **overrides: параметры article.pages_get, отличные от значений по умолчанию.

    Returns:
        Список id статей.
    """
    params = {
        "username": None,
        "include_nonsub": True,
        "sort_column": "creation_date",
        "sort_direction": "ascending",
        "include": {},
        "exclude": {},
        "bounds": {},
    }
    return article.pages_get(session, **{**params, **overrides})


def test_post_stores_cyrillic_without_escaping(
    session: Session, add_user: Callable
) -> None:
    add_user("author")

    article_id = article.post(session, "t", {"block": "жаба"}, "author", {})

    assert "жаба" in session.get(scheme.Article, article_id).body


def test_like_replaces_dislike_and_is_idempotent(
    session: Session, add_user: Callable
) -> None:
    add_user("author")
    add_user("reader")
    article_id = _post(session, "author")

    article.dislike(session, article_id, "reader")
    assert article.rating(session, article_id)[1] == -1

    assert not article.like(session, article_id, "reader").is_error
    assert not article.like(session, article_id, "reader").is_error
    assert article.rating(session, article_id)[1] == 1


def test_dislike_replaces_like(session: Session, add_user: Callable) -> None:
    add_user("author")
    add_user("reader")
    article_id = _post(session, "author")

    article.like(session, article_id, "reader")
    article.dislike(session, article_id, "reader")

    assert article.likes_count(session, article_id)[1] == 0
    assert article.dislikes_count(session, article_id)[1] == 1


def test_like_errors(session: Session, add_user: Callable) -> None:
    add_user("author")
    add_user("reader")
    article_id = _post(session, "author")

    for react in (article.like, article.dislike):
        assert_error_status(
            react(session, article_id, "author"),
            ErrorType.Forbidden,
            "User cannot like or dislike their own article",
        )
    assert article.rating(session, article_id)[1] == 0

    article.delete(session, article_id, "author")
    for react in (article.like, article.dislike, article.remove_like):
        assert_error_status(
            react(session, article_id, "reader"),
            ErrorType.NotFound,
            f"Cannot find article with id: {article_id}",
        )


def test_delete_unknown_article(session: Session) -> None:
    assert_error_status(
        article.delete(session, 0, "reader"),
        ErrorType.NotFound,
        "Cannot find article with id: 0",
    )


@pytest.mark.parametrize(
    "getter",
    [
        article.likes_count,
        article.dislikes_count,
        article.rating,
        article.comments_count,
        article.get,
        article.preview,
        article.tags,
    ],
)
def test_reads_of_unknown_article(session: Session, getter: Callable) -> None:
    status, value = getter(session, 0)

    assert_error_status(status, ErrorType.NotFound, "Cannot find article with id: 0")
    assert value is None


def test_delete_hides_article_from_strangers(
    session: Session, add_user: Callable
) -> None:
    add_user("author")
    add_user("reader")
    article_id = _post(session, "author")

    assert_error_status(
        article.delete(session, article_id, "reader"),
        ErrorType.Forbidden,
        "User cannot delete someone else's article",
    )
    assert not article.is_article_not_exist(session, article_id)
    assert not article.delete(session, article_id, "author").is_error

    assert article.is_article_not_exist(session, article_id)
    # Автору повтор разрешён (DELETE идемпотентен), а постороннему ответ не должен
    # выдавать, что такая статья вообще была.
    assert not article.delete(session, article_id, "author").is_error
    assert_error_status(
        article.delete(session, article_id, "reader"),
        ErrorType.NotFound,
        f"Cannot find article with id: {article_id}",
    )


def test_add_tags_rejects_duplicates_ignoring_case(
    session: Session, add_user: Callable
) -> None:
    add_user("author")
    article_id = _post(session, "author")

    status = article.add_tags(session, ["Frog", "frog"], article_id)

    assert_error_status(
        status, ErrorType.InvalidParameters, "Article tags must be unique"
    )
    assert status.problem()["errors"] == [
        {"name": "tags", "reason": "must not contain duplicates"}
    ]


def test_feed_skips_deleted(session: Session, add_user: Callable) -> None:
    add_user("author")
    kept = _post(session, "author")
    deleted = _post(session, "author")
    article.delete(session, deleted, "author")

    assert _feed(session) == [kept]


def test_feed_sorts_by_date(session: Session, add_user: Callable) -> None:
    add_user("author")
    old = _post(session, "author", creation_date=1)
    new = _post(session, "author", creation_date=2)

    assert _feed(session) == [old, new]
    assert _feed(session, sort_direction="descending") == [new, old]


def test_feed_sorts_by_rating(session: Session, add_user: Callable) -> None:
    add_user("author")
    add_user("reader")
    disliked = _post(session, "author")
    neutral = _post(session, "author")
    liked = _post(session, "author")
    article.like(session, liked, "reader")
    article.dislike(session, disliked, "reader")

    assert _feed(session, sort_column="rating") == [disliked, neutral, liked]


def test_feed_bounds_are_exclusive(session: Session, add_user: Callable) -> None:
    add_user("author")
    articles = [_post(session, "author", creation_date=date) for date in (1, 2, 3)]

    assert _feed(session, bounds={"lower": 1, "upper": 3}) == [articles[1]]


def test_feed_include_tags_requires_all(session: Session, add_user: Callable) -> None:
    add_user("author")
    both = _post(session, "author")
    one = _post(session, "author")
    article.add_tags(session, ["a", "b"], both)
    article.add_tags(session, ["a"], one)

    assert _feed(session, include={"tags": ["a", "b"]}) == [both]


def test_feed_exclude(session: Session, add_user: Callable) -> None:
    add_user("author")
    add_user("other")
    tagged = _post(session, "author")
    by_author = _post(session, "author")
    by_other = _post(session, "other")
    article.add_tags(session, ["a"], tagged)

    assert _feed(session, exclude={"tags": ["a"]}) == [by_author, by_other]
    assert _feed(session, exclude={"authors": ["author"]}) == [by_other]


def test_feed_applies_personal_blacklists(session: Session, add_user: Callable) -> None:
    add_user("reader")
    add_user("blocked")
    add_user("author")
    _post(session, "blocked")
    tagged = _post(session, "author")
    visible = _post(session, "author")
    article.add_tags(session, ["spoiler"], tagged)
    user.block_user(session, "reader", "blocked")
    user.block_tag(session, "reader", "spoiler")

    assert _feed(session, username="reader") == [visible]


def test_feed_user_named_unlogged_user_is_regular_user(
    session: Session, add_user: Callable
) -> None:
    # Анонимный запрос обозначается None, поэтому такое имя не отключает личные
    # фильтры, как было бы при сравнении со служебной строкой.
    add_user("unlogged_user")
    add_user("blocked")
    _post(session, "blocked")
    user.block_user(session, "unlogged_user", "blocked")

    assert _feed(session, username="unlogged_user") == []


def test_is_liked_for_anonymous_is_false(session: Session, add_user: Callable) -> None:
    add_user("author")
    add_user("reader")
    article_id = _post(session, "author")
    article.like(session, article_id, "reader")

    assert article.is_liked(session, article_id, None)[1] is False
    assert article.is_disliked(session, article_id, None)[1] is False


def test_feed_subscriptions_only(session: Session, add_user: Callable) -> None:
    add_user("reader")
    add_user("followed")
    add_user("other")
    by_author = _post(session, "followed")
    by_tag = _post(session, "other")
    _post(session, "other")
    article.add_tags(session, ["games"], by_tag)
    user.sub_user(session, "reader", "followed")
    user.sub_tag(session, "reader", "games")

    assert _feed(session, username="reader", include_nonsub=False) == [
        by_author,
        by_tag,
    ]


def test_feed_without_subscriptions_is_empty(
    session: Session, add_user: Callable
) -> None:
    add_user("reader")
    add_user("author")
    _post(session, "author")

    assert _feed(session, username="reader", include_nonsub=False) == []


def test_feed_anonymous_ignores_subscriptions_filter(
    session: Session, add_user: Callable
) -> None:
    add_user("author")
    article_id = _post(session, "author")

    assert _feed(session, include_nonsub=False) == [article_id]

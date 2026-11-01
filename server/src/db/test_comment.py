"""
Этот файл служит для хранения unit-тестов src/db/comment.py: сборки дерева
комментариев (без БД) и добавления, удаления и реакций на настоящей MySQL.
"""

from collections.abc import Callable
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from src.db import article, comment
from src.request_status import ErrorType
from src.test_helpers import assert_error_status


def _row(
    id: int, parent_id: int | None = None, is_deleted: bool = False
) -> SimpleNamespace:
    """Строит заменитель строки из comment.from_article: дереву нужны только поля.

    Args:
        id: id комментария.
        parent_id: id родителя или `None` для верхнего уровня.
        is_deleted: удалён ли комментарий.

    Returns:
        Объект с теми же атрибутами, что и строка запроса.
    """
    return SimpleNamespace(
        id=id,
        parent_id=parent_id,
        is_deleted=is_deleted,
        author_username="frog",
        text=f"text {id}",
    )


def test_tree_node_top_level_uses_minus_one() -> None:
    assert comment._tree_node(_row(1), [_row(1)]) == {
        "id": 1,
        "parent_id": -1,
        "is_deleted": False,
        "answers": [],
        "author_username": "frog",
        "text": "text 1",
    }


def test_tree_node_deleted_is_stub_with_answers() -> None:
    rows = [_row(1, is_deleted=True), _row(2, parent_id=1)]

    node = comment._tree_node(rows[0], rows)

    assert "text" not in node
    assert "author_username" not in node
    assert [answer["id"] for answer in node["answers"]] == [2]


def test_answers_are_nested() -> None:
    rows = [_row(1), _row(2, parent_id=1), _row(3, parent_id=2), _row(4, parent_id=1)]

    tree = comment.answers(1, rows)

    assert [node["id"] for node in tree] == [2, 4]
    assert [node["id"] for node in tree[0]["answers"]] == [3]
    assert tree[1]["answers"] == []


def test_from_article_returns_only_this_article(
    session: Session, add_user: Callable
) -> None:
    add_user("author")
    article_id = article.post(session, "t", {}, "author", {})
    other_id = article.post(session, "t", {}, "author", {})
    _, parent = comment.add(session, article_id, -1, "parent", "author")
    _, answer = comment.add(session, article_id, parent, "answer", "author")
    comment.add(session, other_id, -1, "other", "author")

    _, tree = comment.from_article(session, article_id)

    assert [node["id"] for node in tree] == [parent]
    assert [node["id"] for node in tree[0]["answers"]] == [answer]


def test_add_rejects_parent_from_other_article(
    session: Session, add_user: Callable
) -> None:
    add_user("author")
    article_id = article.post(session, "t", {}, "author", {})
    other_id = article.post(session, "t", {}, "author", {})
    _, foreign_parent = comment.add(session, other_id, -1, "text", "author")

    status, comment_id = comment.add(
        session, article_id, foreign_parent, "text", "author"
    )

    assert_error_status(
        status,
        ErrorType.InvalidParameters,
        f"Cannot find comment with id: {foreign_parent}",
    )
    assert comment_id is None


def test_add_rejects_deleted_parent(session: Session, add_user: Callable) -> None:
    add_user("author")
    article_id = article.post(session, "t", {}, "author", {})
    _, parent = comment.add(session, article_id, -1, "text", "author")
    comment.delete(session, parent, "author")

    status, _ = comment.add(session, article_id, parent, "text", "author")

    assert_error_status(
        status, ErrorType.InvalidParameters, f"Cannot find comment with id: {parent}"
    )


def test_delete_errors_and_idempotency(session: Session, add_user: Callable) -> None:
    add_user("author")
    add_user("reader")
    article_id = article.post(session, "t", {}, "author", {})
    _, comment_id = comment.add(session, article_id, -1, "text", "author")

    assert_error_status(
        comment.delete(session, comment_id, "reader"),
        ErrorType.Forbidden,
        "User cannot delete someone else's comment",
    )
    assert not comment.delete(session, comment_id, "author").is_error
    assert not comment.delete(session, comment_id, "author").is_error
    assert comment.is_deleted(session, comment_id)


def test_comment_of_deleted_article_is_hidden_not_stub(
    session: Session, add_user: Callable
) -> None:
    add_user("author")
    article_id = article.post(session, "t", {}, "author", {})
    _, comment_id = comment.add(session, article_id, -1, "text", "author")

    article.delete(session, article_id, "author")

    assert comment.is_comment_not_exist(session, comment_id)
    assert not comment.is_deleted(session, comment_id)
    assert_error_status(
        comment.delete(session, comment_id, "author"),
        ErrorType.NotFound,
        f"Cannot find comment with id: {comment_id}",
    )


def test_like_replaces_dislike(session: Session, add_user: Callable) -> None:
    add_user("author")
    add_user("reader")
    article_id = article.post(session, "t", {}, "author", {})
    _, comment_id = comment.add(session, article_id, -1, "text", "author")

    comment.dislike(session, comment_id, "reader")
    assert comment.rating(session, comment_id)[1] == -1

    comment.like(session, comment_id, "reader")
    assert comment.rating(session, comment_id)[1] == 1


def test_own_comment_reactions_are_forbidden(
    session: Session, add_user: Callable
) -> None:
    add_user("author")
    article_id = article.post(session, "t", {}, "author", {})
    _, comment_id = comment.add(session, article_id, -1, "text", "author")

    for react in (comment.like, comment.dislike):
        assert_error_status(
            react(session, comment_id, "author"),
            ErrorType.Forbidden,
            "User cannot like or dislike their own comment",
        )
    assert comment.rating(session, comment_id)[1] == 0


@pytest.mark.parametrize(
    "react",
    [comment.like, comment.dislike, comment.remove_like, comment.remove_dislike],
)
def test_reactions_on_unknown_comment(session: Session, react: Callable) -> None:
    assert_error_status(
        react(session, 0, "reader"),
        ErrorType.NotFound,
        "Cannot find comment with id: 0",
    )


@pytest.mark.parametrize(
    "getter",
    [
        comment.likes_count,
        comment.dislikes_count,
        comment.rating,
        comment.creation_date,
    ],
)
def test_reads_of_unknown_comment(session: Session, getter: Callable) -> None:
    status, value = getter(session, 0)

    assert_error_status(status, ErrorType.NotFound, "Cannot find comment with id: 0")
    assert value is None

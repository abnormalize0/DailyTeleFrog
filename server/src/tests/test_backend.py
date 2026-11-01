"""
Этот файл служит для хранения unit-тестов src/backend.py на настоящей MySQL: сборки
сценариев из нескольких шагов слоя db и ошибок, которые из них возвращаются.
"""

from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from src import backend
from src.db import article, auth, comment, scheme, user
from src.request_status import ErrorType
from src.tests.helpers import assert_error_status

PASSWORD = "password"


@pytest.fixture
def registered_username(session: Session) -> str:
    """Регистрирует пользователя с настоящим хешем пароля, нужным для входа.

    Args:
        session: fixture сессии.

    Returns:
        username созданного пользователя.
    """
    user.add_user(session, "frog", "Frog", PASSWORD, 0, "frog@test.test")
    return "frog"


def _credentials(**overrides: str) -> dict:
    """Строит параметры входа, как их собирает API-метод через fill_default.

    Args:
        **overrides: поля, заменяющие значения по умолчанию.

    Returns:
        Словарь с полями password, username и email.
    """
    return {"password": PASSWORD, "username": "", "email": "", **overrides}


def test_login_by_username_and_email(
    session: Session, registered_username: str
) -> None:
    for credentials in (
        _credentials(username=registered_username),
        _credentials(email="frog@test.test"),
    ):
        status, tokens = backend.login(session, credentials)

        assert not status.is_error
        assert (
            backend.resolve_token(session, tokens["access_token"])[1]
            == registered_username
        )


@pytest.mark.parametrize(
    "credentials",
    [
        {"username": "frog", "password": "wrong"},
        {"email": "frog@test.test", "password": "wrong"},
        {"username": "nobody"},
        {"email": "nobody@test.test"},
    ],
)
def test_login_failures_look_the_same(
    session: Session, registered_username: str, credentials: dict
) -> None:
    # Одинаковый ответ для неверного пароля и неизвестного логина: иначе по
    # сообщению можно было бы перебирать существующие аккаунты.
    status, tokens = backend.login(session, _credentials(**credentials))

    assert_error_status(
        status, ErrorType.InvalidCredentials, "Incorrect login or password"
    )
    assert tokens is None
    assert session.query(scheme.AccessToken).count() == 0


def test_login_to_deleted_account(session: Session, registered_username: str) -> None:
    user.delete(session, registered_username)

    status, _ = backend.login(session, _credentials(username=registered_username))

    assert_error_status(
        status, ErrorType.InvalidCredentials, "Incorrect login or password"
    )


def test_refresh_rotates_token(session: Session, registered_username: str) -> None:
    old_token = auth.create_refresh_token(session, registered_username)

    status, tokens = backend.refresh_session(session, old_token)

    assert not status.is_error
    assert tokens["refresh_token"] != old_token
    status, tokens = backend.refresh_session(session, old_token)
    assert_error_status(status, ErrorType.InvalidToken, "Missing or invalid token")
    assert tokens is None


def test_refresh_removes_expired_tokens(
    session: Session, registered_username: str
) -> None:
    expired = auth.create_refresh_token(session, registered_username)
    session.get(scheme.RefreshToken, expired).expires_at = 1
    session.flush()
    token = auth.create_refresh_token(session, registered_username)

    status, _ = backend.refresh_session(session, token)

    assert not status.is_error
    assert session.get(scheme.RefreshToken, expired) is None


def test_delete_user_with_wrong_password_changes_nothing(
    session: Session, registered_username: str
) -> None:
    token = auth.create_access_token(session, registered_username)

    status = backend.delete_user(session, "wrong", registered_username)

    assert_error_status(status, ErrorType.Forbidden, "Incorrect password")
    assert not user.is_user_not_exist(session, username=registered_username)
    assert not auth.resolve_access_token(session, token)[0].is_error


def test_delete_user_revokes_tokens(session: Session, registered_username: str) -> None:
    token = auth.create_access_token(session, registered_username)

    assert not backend.delete_user(session, PASSWORD, registered_username).is_error

    assert auth.resolve_access_token(session, token)[0].is_error


def test_change_password_with_wrong_password_changes_nothing(
    session: Session, registered_username: str
) -> None:
    token = auth.create_access_token(session, registered_username)

    status = backend.change_password(session, "wrong", "new", registered_username)

    assert_error_status(status, ErrorType.Forbidden, "Incorrect password")
    assert user.check_password(session, PASSWORD, username=registered_username)[1]
    assert not auth.resolve_access_token(session, token)[0].is_error


def test_change_password_revokes_tokens(
    session: Session, registered_username: str
) -> None:
    token = auth.create_access_token(session, registered_username)

    assert not backend.change_password(
        session, PASSWORD, "new", registered_username
    ).is_error

    assert user.check_password(session, "new", username=registered_username)[1]
    assert auth.resolve_access_token(session, token)[0].is_error


def test_update_user_info_stops_at_first_error(
    session: Session, add_user: Callable
) -> None:
    add_user("frog")

    status = backend.update_user_info(
        session, "frog", {"sub-users": ["nobody", "frog"], "avatar": "after error"}
    )

    assert_error_status(
        status, ErrorType.InvalidParameters, "Cannot find user with username: nobody"
    )
    assert user.get_avatar(session, "frog")[1] is None


def test_post_article_rejects_duplicate_tags(
    session: Session, add_user: Callable
) -> None:
    add_user("frog")

    status, article_id = backend.post_article(
        session, "frog", "title", {}, {}, ["Tag", "tag"]
    )

    assert_error_status(
        status, ErrorType.InvalidParameters, "Article tags must be unique"
    )
    assert article_id is None


def test_add_comment_to_unknown_article(session: Session, add_user: Callable) -> None:
    add_user("frog")

    status, comment_id = backend.add_comment(session, 0, -1, "text", "frog")

    assert_error_status(status, ErrorType.NotFound, "Cannot find article with id: 0")
    assert comment_id is None


@pytest.mark.parametrize(
    "call",
    [
        lambda session: backend.get_article(session, 0, "frog"),
        lambda session: backend.get_article_data(session, 0, "frog", ["is_liked"]),
        lambda session: backend.get_article_preview(session, 0, "frog"),
    ],
)
def test_reads_of_unknown_article(session: Session, call: Callable) -> None:
    status, data = call(session)

    assert_error_status(status, ErrorType.NotFound, "Cannot find article with id: 0")
    assert data is None


def test_comment_data_of_unknown_comment(session: Session) -> None:
    # is_liked сам по себе не ходит за комментарием и отдал бы False вместо 404.
    status, data = backend.get_comment_data(session, 0, "frog", ["is_liked"])

    assert_error_status(status, ErrorType.NotFound, "Cannot find comment with id: 0")
    assert data is None


def test_comment_data_of_deleted_comment_is_stub(
    session: Session, add_user: Callable
) -> None:
    add_user("frog")
    article_id = article.post(session, "t", {}, "frog", {})
    _, comment_id = comment.add(session, article_id, -1, "text", "frog")
    comment.delete(session, comment_id, "frog")

    status, data = backend.get_comment_data(session, comment_id, "frog", ["likes"])

    assert not status.is_error
    assert data == {"is_deleted": True}


def test_user_data_of_unknown_user(session: Session) -> None:
    status, data = backend.get_user_data(session, "nobody", ["email"])

    assert_error_status(
        status, ErrorType.NotFound, "Cannot find user with username: nobody"
    )
    assert data is None

"""
Этот файл служит для хранения unit-тестов src/db/user.py: хеширования паролей (без
БД), а также регистрации, мягкого удаления, подписок и рейтинга на настоящей MySQL.
"""

import hashlib
from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from src.db import article, comment, scheme, user
from src.request_status import ErrorType
from src.test_helpers import assert_error_status


def test_hash_password_format() -> None:
    iterations, salt, digest = user._hash_password("password").split("$")

    assert int(iterations) == user._PASSWORD_HASH_ITERATIONS
    assert len(salt) == user._PASSWORD_SALT_BYTES * 2
    # 32 байта SHA-256 в hex.
    assert len(digest) == 64


def test_hash_password_is_salted() -> None:
    assert user._hash_password("password") != user._hash_password("password")


def test_verify_password() -> None:
    stored = user._hash_password("пароль")

    assert user._verify_password("пароль", stored)
    assert not user._verify_password("другой", stored)


def test_verify_password_uses_stored_iterations() -> None:
    # Рост числа итераций в коде не должен ломать вход со старыми хешами.
    salt = b"salt"
    digest = hashlib.pbkdf2_hmac("sha256", b"password", salt, 1000)

    assert user._verify_password("password", f"1000${salt.hex()}${digest.hex()}")


def test_add_user_stores_only_hash(session: Session) -> None:
    status = user.add_user(session, "frog", "Frog", "password", 0, "frog@test.test")

    assert not status.is_error
    stored = session.query(scheme.User.password).filter_by(username="frog").scalar()
    assert "password" not in stored


def test_check_password(session: Session) -> None:
    user.add_user(session, "frog", "Frog", "password", 0, "frog@test.test")

    assert user.check_password(session, "password", username="frog")[1]
    assert user.check_password(session, "password", email="frog@test.test")[1]
    assert not user.check_password(session, "wrong", username="frog")[1]
    assert not user.check_password(session, "password", username="nobody")[1]


def test_add_user_conflicts_ignore_case(session: Session, add_user: Callable) -> None:
    # Без учёта регистра строки сравнивает MySQL (см. scheme/base.py), и такое
    # поведение нельзя проверить без настоящей базы.
    add_user("frog")

    same_username = user.add_user(session, "FROG", "n", "p", 0, "other@test.test")
    same_email = user.add_user(session, "other", "n", "p", 0, "FROG@test.test")

    assert_error_status(
        same_username, ErrorType.Conflict, "User with username FROG already exists"
    )
    assert_error_status(
        same_email, ErrorType.Conflict, "User with email FROG@test.test already exists"
    )


def test_delete_is_soft_and_keeps_names_taken(
    session: Session, add_user: Callable
) -> None:
    add_user("frog")

    assert not user.delete(session, "frog").is_error

    assert user.is_user_not_exist(session, username="frog")
    assert session.get(scheme.User, "frog").is_deleted
    assert_error_status(
        user.add_user(session, "frog", "n", "p", 0, "new@test.test"),
        ErrorType.Conflict,
        "User with username frog already exists",
    )
    assert_error_status(
        user.delete(session, "frog"),
        ErrorType.NotFound,
        "Cannot find user with username: frog",
    )


def test_delete_removes_relations_to_user(session: Session, add_user: Callable) -> None:
    add_user("frog")
    add_user("follower")
    add_user("blocker")
    user.sub_user(session, "follower", "frog")
    user.block_user(session, "blocker", "frog")
    user.sub_user(session, "frog", "follower")

    user.delete(session, "frog")

    assert session.query(scheme.UserBlacklist).count() == 0
    # Подписки самого удалённого аккаунта остаются: они ни на кого не влияют.
    assert [row.username for row in session.query(scheme.UserSubscription)] == ["frog"]


def test_update_nickname_history(session: Session, add_user: Callable) -> None:
    add_user("frog")

    # Смена, повтор того же значения, возврат к старому и вторая смена: возврат
    # упал бы на первичном ключе истории без проверки на существующую запись.
    for nickname in ["second", "second", "frog_nickname", "second"]:
        assert not user.update_nickname(session, "frog", nickname).is_error

    _, history = user.get_name_history(session, "frog")
    assert sorted(history) == ["frog_nickname", "second"]


def test_sub_user_replaces_block(session: Session, add_user: Callable) -> None:
    add_user("frog")
    add_user("toad")
    user.block_user(session, "frog", "toad")

    assert not user.sub_user(session, "frog", "toad").is_error
    # Повтор идемпотентен: PATCH описывает состояние, которое уже достигнуто.
    assert not user.sub_user(session, "frog", "toad").is_error

    assert session.query(scheme.UserBlacklist).count() == 0
    assert session.query(scheme.UserSubscription).count() == 1


def test_user_relations_errors(session: Session, add_user: Callable) -> None:
    add_user("frog")

    for action in (user.sub_user, user.block_user):
        assert_error_status(
            action(session, "nobody", "frog"),
            ErrorType.NotFound,
            "Cannot find user with username: nobody",
        )
        assert_error_status(
            action(session, "frog", "frog"),
            ErrorType.Forbidden,
            "User cannot subscribe to or block themselves",
        )
        assert_error_status(
            action(session, "frog", "nobody"),
            ErrorType.InvalidParameters,
            "Cannot find user with username: nobody",
        )


def test_get_rating_skips_deleted_content(session: Session, add_user: Callable) -> None:
    add_user("author")
    add_user("fan")
    add_user("hater")
    kept = article.post(session, "kept", {}, "author", {})
    deleted = article.post(session, "deleted", {}, "author", {})
    _, kept_comment = comment.add(session, kept, -1, "text", "author")
    _, deleted_comment = comment.add(session, kept, -1, "text", "author")

    article.like(session, kept, "fan")
    article.dislike(session, kept, "hater")
    comment.like(session, kept_comment, "fan")
    comment.dislike(session, kept_comment, "hater")
    # Реакции на удалённое обе положительные: разные знаки взаимно погасились бы,
    # и тест не заметил бы, что удалённое попало в подсчёт.
    article.like(session, deleted, "fan")
    comment.like(session, deleted_comment, "fan")
    article.delete(session, deleted, "author")
    comment.delete(session, deleted_comment, "author")

    assert user.get_rating(session, "author")[1] == 0


def test_cannot_subscribe_to_deleted_user(session: Session, add_user: Callable) -> None:
    add_user("frog")
    add_user("toad")
    user.delete(session, "toad")

    assert_error_status(
        user.sub_user(session, "frog", "toad"),
        ErrorType.InvalidParameters,
        "Cannot find user with username: toad",
    )


def test_update_email_conflict_keeps_old_value(
    session: Session, add_user: Callable
) -> None:
    add_user("frog")
    add_user("toad")

    assert_error_status(
        user.update_email(session, "frog", "TOAD@test.test"),
        ErrorType.Conflict,
        "User with email TOAD@test.test already exists",
    )
    assert user.get_email(session, "frog")[1] == "frog@test.test"
    # Свой email не конфликт: повторный PATCH не должен падать.
    assert not user.update_email(session, "frog", "frog@test.test").is_error


@pytest.mark.parametrize(
    "call",
    [
        lambda session: user.change_password(session, "new", "nobody"),
        lambda session: user.update_email(session, "nobody", "e@test.test"),
        lambda session: user.update_nickname(session, "nobody", "nickname"),
        lambda session: user.update_description(session, "nobody", "text"),
        lambda session: user.update_avatar(session, "nobody", "url"),
        lambda session: user.sub_tag(session, "nobody", "tag"),
        lambda session: user.block_tag(session, "nobody", "tag"),
    ],
)
def test_changes_of_unknown_user(session: Session, call: Callable) -> None:
    assert_error_status(
        call(session), ErrorType.NotFound, "Cannot find user with username: nobody"
    )


@pytest.mark.parametrize(
    "getter",
    [
        user.get_rating,
        user.get_email,
        user.get_name_history,
        user.get_nickname,
        user.get_description,
        user.get_avatar,
        user.get_sub_user,
        user.get_blacklist_user,
        user.get_sub_tag,
        user.get_blacklist_tag,
        user.get_creation_date,
    ],
)
def test_reads_of_unknown_user(session: Session, getter: Callable) -> None:
    status, value = getter(session, "nobody")

    assert_error_status(
        status, ErrorType.NotFound, "Cannot find user with username: nobody"
    )
    assert value is None

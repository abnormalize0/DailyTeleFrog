"""
Этот файл служит для хранения unit-тестов src/db/auth.py на настоящей MySQL. Здесь
проверяется истечение токенов: e2e-тест не может его вызвать, потому что по HTTP
срок жизни токена не изменить, а часа ждать нельзя.
"""

import time
from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from src import config
from src.db import auth, scheme
from src.request_status import ErrorType
from src.test_helpers import assert_error_status

TOKEN_KINDS = [
    (scheme.AccessToken, auth.create_access_token, auth.resolve_access_token),
    (scheme.RefreshToken, auth.create_refresh_token, auth.resolve_refresh_token),
]


def test_generate_token_fits_column() -> None:
    # Длина колонки String(64) зависит от этого значения.
    assert len(auth._generate_token()) == 64


def test_token_lifetimes(session: Session, add_user: Callable) -> None:
    add_user("frog")
    now = round(time.time() * 1000)

    access = auth.create_access_token(session, "frog")
    refresh = auth.create_refresh_token(session, "frog")

    access_expires = session.get(scheme.AccessToken, access).expires_at
    refresh_expires = session.get(scheme.RefreshToken, refresh).expires_at
    assert access_expires - now == pytest.approx(
        config.access_token_lifetime_ms, abs=5000
    )
    assert refresh_expires - now == pytest.approx(
        config.refresh_token_lifetime_ms, abs=5000
    )


@pytest.mark.parametrize("model, create, resolve", TOKEN_KINDS)
def test_resolve_valid_token(
    session: Session,
    add_user: Callable,
    model: type,
    create: Callable,
    resolve: Callable,
) -> None:
    add_user("frog")
    token = create(session, "frog")

    status, username = resolve(session, token)

    assert not status.is_error
    assert username == "frog"


@pytest.mark.parametrize("model, create, resolve", TOKEN_KINDS)
def test_expired_token_is_rejected_and_removed(
    session: Session,
    add_user: Callable,
    model: type,
    create: Callable,
    resolve: Callable,
) -> None:
    add_user("frog")
    token = create(session, "frog")
    session.get(model, token).expires_at = round(time.time() * 1000) - 1
    session.flush()

    status, username = resolve(session, token)

    assert_error_status(status, ErrorType.InvalidToken, "Missing or invalid token")
    assert username is None
    assert session.query(model).count() == 0


@pytest.mark.parametrize("token", ["", "unknown"])
def test_resolve_missing_token(session: Session, token: str) -> None:
    status, username = auth.resolve_access_token(session, token)

    assert_error_status(status, ErrorType.InvalidToken, "Missing or invalid token")
    assert username is None


def test_token_kinds_are_not_interchangeable(
    session: Session, add_user: Callable
) -> None:
    add_user("frog")
    access = auth.create_access_token(session, "frog")
    refresh = auth.create_refresh_token(session, "frog")

    for status, _ in (
        auth.resolve_refresh_token(session, access),
        auth.resolve_access_token(session, refresh),
    ):
        assert_error_status(status, ErrorType.InvalidToken, "Missing or invalid token")


def test_revoke_token(session: Session, add_user: Callable) -> None:
    add_user("frog")
    access = auth.create_access_token(session, "frog")
    refresh = auth.create_refresh_token(session, "frog")

    auth.revoke_access_token(session, access)
    auth.revoke_refresh_token(session, refresh)
    # Повторный отзыв молчит: logout не должен падать на уже отозванном токене.
    auth.revoke_access_token(session, access)
    auth.revoke_refresh_token(session, refresh)

    assert session.query(scheme.AccessToken).count() == 0
    assert session.query(scheme.RefreshToken).count() == 0


def test_revoke_all_tokens_touches_only_this_user(
    session: Session, add_user: Callable
) -> None:
    add_user("frog")
    add_user("toad")
    auth.create_access_token(session, "frog")
    auth.create_refresh_token(session, "frog")
    toad_access = auth.create_access_token(session, "toad")
    toad_refresh = auth.create_refresh_token(session, "toad")

    auth.revoke_all_tokens(session, "frog")

    assert [row.token for row in session.query(scheme.AccessToken)] == [toad_access]
    assert [row.token for row in session.query(scheme.RefreshToken)] == [toad_refresh]

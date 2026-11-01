"""
Этот файл служит для хранения логики токенов авторизации: выпуск access и
refresh токенов, их проверка и отзыв (logout, смена пароля, удаление аккаунта,
ротация refresh).
"""

import secrets
import time

from . import scheme
from .. import config
from .. import request_status
from sqlalchemy.orm import Session

# 32 случайных байта (secrets — криптостойкий генератор из stdlib) в hex дают
# 64 символа, ровно под String(64) в scheme.AccessToken/RefreshToken.
_TOKEN_BYTES = 32


def _generate_token() -> str:
    """Генерирует случайный непредсказуемый токен.

    Args:
        None

    Returns:
        Строка из 64 hex-символов.
    """
    return secrets.token_hex(_TOKEN_BYTES)


def create_access_token(session: Session, username: str) -> str:
    """Выпускает новый access token для пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя, для которого выпускается токен.

    Returns:
        Значение токена (str).
    """
    token = _generate_token()
    session.add(
        scheme.AccessToken(
            token=token,
            username=username,
            expires_at=round(time.time() * 1000) + config.access_token_lifetime_ms,
        )
    )
    session.flush()
    return token


def create_refresh_token(session: Session, username: str) -> str:
    """Выпускает новый refresh token для пользователя.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя, для которого выпускается токен.

    Returns:
        Значение токена (str).
    """
    token = _generate_token()
    session.add(
        scheme.RefreshToken(
            token=token,
            username=username,
            expires_at=round(time.time() * 1000) + config.refresh_token_lifetime_ms,
        )
    )
    session.flush()
    return token


def resolve_access_token(
    session: Session, token: str
) -> tuple[request_status.Status, str | None]:
    """Проверяет access token и возвращает username его владельца.

    Args:
        session: сессия SQLAlchemy.
        token: значение токена из заголовка Authorization.

    Returns:
        Кортеж (`Status`, str):
            - OK и username — если токен существует и не истёк.
            - InvalidToken и `None` — если токен отсутствует, не найден или истёк.
    """
    return _resolve_token(session, scheme.AccessToken, token)


def resolve_refresh_token(
    session: Session, token: str
) -> tuple[request_status.Status, str | None]:
    """Проверяет refresh token и возвращает username его владельца.

    Args:
        session: сессия SQLAlchemy.
        token: значение refresh token.

    Returns:
        Кортеж (`Status`, str):
            - OK и username — если токен существует и не истёк.
            - InvalidToken и `None` — если токен отсутствует, не найден или истёк.
    """
    return _resolve_token(session, scheme.RefreshToken, token)


def _resolve_token(
    session: Session, model: type, token: str
) -> tuple[request_status.Status, str | None]:
    """Общая проверка для AccessToken/RefreshToken: найден и не истёк ли токен.

    Args:
        session: сессия SQLAlchemy.
        model: scheme.AccessToken или scheme.RefreshToken.
        token: значение токена.

    Returns:
        Кортеж (`Status`, str):
            - OK и username — если токен существует и не истёк.
            - InvalidToken и `None` — если токен отсутствует, не найден или истёк.
    """
    if not token:
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.InvalidToken,
                msg="Missing or invalid token",
            ),
            None,
        )
    row = session.query(model).where(model.token == token).scalar()
    if row is None or row.expires_at < round(time.time() * 1000):
        if row is not None:
            # Просроченный токен больше никому не нужен — не ждём отдельной
            # уборки мусора, а удаляем сразу при первой же проверке.
            session.delete(row)
            session.flush()
        return (
            request_status.Status(
                request_status.StatusType.ERROR,
                error_type=request_status.ErrorType.InvalidToken,
                msg="Missing or invalid token",
            ),
            None,
        )
    return request_status.Status(request_status.StatusType.OK), row.username


def revoke_refresh_token(session: Session, token: str) -> None:
    """Удаляет refresh token (используется при ротации и logout).

    Args:
        session: сессия SQLAlchemy.
        token: значение токена. Если токена нет — тихо ничего не делает.

    Returns:
        None
    """
    row = (
        session.query(scheme.RefreshToken)
        .where(scheme.RefreshToken.token == token)
        .scalar()
    )
    if row is not None:
        session.delete(row)
        session.flush()


def revoke_access_token(session: Session, token: str) -> None:
    """Удаляет access token (используется при logout).

    Args:
        session: сессия SQLAlchemy.
        token: значение токена. Если токена нет — тихо ничего не делает.

    Returns:
        None
    """
    row = (
        session.query(scheme.AccessToken)
        .where(scheme.AccessToken.token == token)
        .scalar()
    )
    if row is not None:
        session.delete(row)
        session.flush()


def revoke_all_tokens(session: Session, username: str) -> None:
    """Удаляет все access и refresh токены пользователя (все сессии сразу).

    Используется при смене пароля, удалении аккаунта и /auth/logout-all: остальные
    устройства/вкладки должны залогиниться заново.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        None
    """
    session.query(scheme.AccessToken).where(
        scheme.AccessToken.username == username
    ).delete()
    session.query(scheme.RefreshToken).where(
        scheme.RefreshToken.username == username
    ).delete()
    session.flush()

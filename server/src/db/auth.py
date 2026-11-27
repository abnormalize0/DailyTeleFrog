"""
Этот файл служит для хранения логики токенов авторизации: выпуск access и
refresh токенов, их проверка и отзыв (logout, смена пароля, удаление аккаунта,
ротация refresh).
"""

import secrets
import time

from . import scheme
from .rows import lock_user
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
    username = username.lower()
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
    username = username.lower()
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
            - OK и username — если токен существует, не истёк и аккаунт не удалён.
            - InvalidToken и `None` — если токен отсутствует, не найден, истёк или
              аккаунт владельца удалён.
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
            - OK и username — если токен существует, не истёк и аккаунт не удалён.
            - InvalidToken и `None` — если токен отсутствует, не найден, истёк или
              аккаунт владельца удалён.
    """
    return _resolve_token(session, scheme.RefreshToken, token)


def _resolve_token(
    session: Session, model: type, token: str
) -> tuple[request_status.Status, str | None]:
    """Общая проверка для AccessToken/RefreshToken: токен найден, не истёк, а
    аккаунт владельца не помечен удалённым.

    Args:
        session: сессия SQLAlchemy.
        model: scheme.AccessToken или scheme.RefreshToken.
        token: значение токена.

    Returns:
        Кортеж (`Status`, str):
            - OK и username — если токен существует, не истёк и аккаунт не удалён.
            - InvalidToken и `None` — если токен отсутствует, не найден, истёк или
              аккаунт владельца удалён.
    """
    if not token:
        return (
            request_status.Status.error(
                request_status.ErrorType.InvalidToken,
                "Missing or invalid token",
            ),
            None,
        )
    # Выбираем скалярные колонки вместо ORM-объекта, чтобы при повторной проверке
    # под блокировкой в READ COMMITTED читать актуальное состояние БД, а не кэш
    # identity map. Проверка User.is_deleted выполняется в этом же запросе.
    row = (
        session.query(model.username, model.expires_at)
        .join(scheme.User, model.username == scheme.User.username)
        .where(model.token == token, scheme.User.is_deleted.is_(False))
        .first()
    )
    if row is None or row.expires_at < round(time.time() * 1000):
        return (
            request_status.Status.error(
                request_status.ErrorType.InvalidToken,
                "Missing or invalid token",
            ),
            None,
        )
    return request_status.Status.ok(), row.username.lower()


def delete_expired_tokens(session: Session, username: str) -> None:
    """Удаляет все просроченные токены пользователя.

    Вызывается при успешном выпуске новых токенов, а не при отказе в проверке: метод,
    ответивший ошибкой, ничего не меняет, поэтому удаление на этом пути откатилось бы
    (см. decisions/0009-api-atomicity.md).

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        None
    """
    username = username.lower()
    now = round(time.time() * 1000)
    for model in (scheme.AccessToken, scheme.RefreshToken):
        session.query(model).where(
            model.username == username, model.expires_at < now
        ).delete()
    session.flush()


def revoke_refresh_token(session: Session, token: str) -> None:
    """Удаляет refresh token (используется при ротации и logout).

    Args:
        session: сессия SQLAlchemy.
        token: значение токена. Если токена нет — тихо ничего не делает.

    Returns:
        None
    """
    # Массовый DELETE вместо SELECT + session.delete: при параллельных logout и
    # refresh/logout-all последний не падает с StaleDataError на уже удалённой строке.
    session.query(scheme.RefreshToken).where(
        scheme.RefreshToken.token == token
    ).delete()
    session.flush()


def revoke_access_token(session: Session, token: str) -> None:
    """Удаляет access token (используется при logout).

    Args:
        session: сессия SQLAlchemy.
        token: значение токена. Если токена нет — тихо ничего не делает.

    Returns:
        None
    """
    session.query(scheme.AccessToken).where(scheme.AccessToken.token == token).delete()
    session.flush()


def revoke_all_tokens(session: Session, username: str) -> None:
    """Удаляет все access и refresh токены пользователя (все сессии сразу).

    Перед удалением блокирует строку пользователя (FOR UPDATE), чтобы сериализоваться
    с параллельными login и refresh и не оставить активных токенов после отзыва.
    Используется при смене пароля, удалении аккаунта и /auth/logout-all: остальные
    устройства/вкладки должны залогиниться заново.

    Args:
        session: сессия SQLAlchemy.
        username: имя пользователя.

    Returns:
        None
    """
    username = username.lower()
    # Сериализуем отзыв с параллельным выпуском токенов (login / refresh).
    lock_user(session, username)
    session.query(scheme.AccessToken).where(
        scheme.AccessToken.username == username
    ).delete()
    session.query(scheme.RefreshToken).where(
        scheme.RefreshToken.username == username
    ).delete()
    session.flush()

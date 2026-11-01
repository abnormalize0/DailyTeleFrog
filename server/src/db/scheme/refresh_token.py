"""
Этот файл служит для хранения схемы таблицы refresh_tokens — долгоживущих
токенов для продления сессии без повторного ввода пароля (см.
decisions/0003-token-based-auth, db/auth.py).
"""

from sqlalchemy import ForeignKey, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # Случайная строка, тоже сама себе первичный ключ — как и у AccessToken.
    token: Mapped[str] = mapped_column(String(64), primary_key=True)

    # FK на users.username. ondelete="CASCADE" — та же причина, что и у
    # AccessToken (токен эфемерен). index=True — по той же причине, что и у
    # AccessToken: нужен быстрый поиск всех refresh-токенов пользователя при
    # отзыве всех сессий разом (см. db/auth.py::revoke_all_tokens).
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"), index=True
    )

    # Долгий срок жизни (~30 дней, см. config.refresh_token_lifetime_ms), но с
    # ротацией при каждом использовании: при вызове /auth/refresh эта строка
    # удаляется и создаётся новая — поэтому кража неиспользованного токена
    # (до следующего /auth/refresh легитимным клиентом) — единственное окно
    # атаки, а повторное предъявление уже использованного токена сразу
    # обнаруживается (его просто больше нет в таблице).
    expires_at: Mapped[int] = mapped_column(BigInteger)

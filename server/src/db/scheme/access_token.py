"""
Этот файл служит для хранения схемы таблицы access_tokens — короткоживущих
токенов авторизации (см. decisions/0003-token-based-auth, db/auth.py).
"""

from sqlalchemy import ForeignKey, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AccessToken(Base):
    __tablename__ = "access_tokens"

    # Случайная непредсказуемая строка (secrets.token_hex(32) — 64 hex-символа,
    # см. db/auth.py) — сам токен и есть первичный ключ, отдельный id не
    # нужен: значение уже уникально по построению (криптостойкий генератор) и
    # именно по нему ищут токен на каждый защищённый запрос.
    token: Mapped[str] = mapped_column(String(64), primary_key=True)

    # FK на users.username — токен не может существовать без владельца.
    # ondelete="CASCADE" — токен эфемерен, при удалении пользователя его
    # сессии просто перестают существовать, никакого продуктового вопроса
    # здесь нет (в отличие от авторства статей/комментариев).
    # По username ищем при отзыве всех сессий пользователя разом: смена пароля,
    # /auth/logout-all, удаление аккаунта (см. db/auth.py::revoke_all_tokens).
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"), index=True
    )

    # Мс с 1970 года, как и остальные даты в проекте. Короткий срок жизни
    # (~1 час, см. config.access_token_lifetime_ms) — если токен украдут, окно
    # для злоупотребления ограничено; продлить сессию можно через
    # /auth/refresh, не заходя в аккаунт заново.
    expires_at: Mapped[int] = mapped_column(BigInteger)

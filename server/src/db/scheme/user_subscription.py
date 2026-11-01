"""
Этот файл служит для хранения схемы таблицы user_subscriptions — подписки
одного пользователя на другого (см. db/user.py::sub_user).
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    # Fan-out таблица-связка (см. decisions/0002): своя строка на каждую
    # подписку, а не счётчик/список на пользователе. Здесь username лидирует
    # в составном PK и это как раз совпадает с основным запросом («на кого
    # подписан username») — в отличие от TagSubscription, здесь по PK уже всё
    # покрыто и отдельный индекс не нужен.
    # ondelete="CASCADE" — подписка бессмысленна без подписчика.
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"), primary_key=True
    )

    # Оба поля — FK на одну и ту же таблицу users: подписка связывает двух
    # существующих пользователей, оба должны быть валидными username.
    # ondelete="CASCADE" — если удалить того, на кого подписывались, подписка
    # на него тоже теряет смысл.
    subscribed_user: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"), primary_key=True
    )

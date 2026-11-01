"""
Этот файл служит для хранения схемы таблицы user_name_history — журнала
прежних nickname пользователя (см. api.api_users_data_post: смена nickname
добавляет сюда запись, а не перезаписывает историю).
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserNameHistory(Base):
    __tablename__ = "user_name_history"

    # Часть составного PK: один пользователь — много исторических имён, поэтому
    # уникальность строки обеспечивается парой (username, old_name), а не
    # отдельным id. FK на users.username — запись истории не может
    # существовать без пользователя, которому она принадлежит.
    # ondelete="CASCADE" — история имён бессмысленна без самого пользователя.
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"), primary_key=True
    )

    # Сюда попадают только прошлые значения User.nickname, поэтому предел
    # такой же, как у самого nickname (String(32)), а не произвольный. Часть
    # составного PK — на случай, если один и тот же nickname использовался
    # дважды, эта запись всё равно должна быть уникальной вместе с username;
    # на практике это ограничение почти никогда не сработает, но концептуально
    # именно пара (username, old_name) и определяет строку.
    old_name: Mapped[str] = mapped_column(String(32), primary_key=True)

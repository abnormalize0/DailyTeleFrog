"""
Этот файл служит для хранения схемы таблицы user_name_history — журнала
прежних nickname пользователя (см. db/user.py::update_nickname: при смене
nickname прежнее значение добавляется сюда, а текущее здесь не хранится).
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
    # составного PK, поэтому каждый ник хранится один раз: при возврате к прежнему
    # нику и новой смене запись не дублируется (см. db/user.py::_add_if_missing).
    # Даты в таблице нет, так что порядка смены ников и числа повторов история не
    # хранит. Ник, к которому пользователь вернулся, остаётся здесь как прошлый.
    old_name: Mapped[str] = mapped_column(String(32), primary_key=True)

"""
Этот файл служит для хранения схемы таблицы tag_blacklist — блокировки
пользователем тега (см. db/user.py::block_tag; заблокированные теги исключаются
из ленты в article.py::pages_get независимо от остальных фильтров).
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TagBlacklist(Base):
    __tablename__ = "tag_blacklist"

    # Тот же fan-out-паттерн и та же оговорка про порядок PK, что и у
    # TagSubscription (см. её комментарии и decisions/0002): tag_name лидирует,
    # хотя основной запрос — по username; компенсируем index=True на username.
    # Регистр при сравнении не учитывается (см. base.py).
    tag_name: Mapped[str] = mapped_column(String(512), primary_key=True)

    # FK на users.username — блокировка не может существовать без пользователя.
    # ondelete="CASCADE" — блокировка бессмысленна без пользователя, который
    # её поставил.
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

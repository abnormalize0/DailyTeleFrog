"""
Этот файл служит для хранения схемы таблицы user_blacklist — блокировки одним
пользователем другого (см. db/user.py::block_user; заблокированные авторы
исключаются из ленты в article.py::pages_get независимо от остальных фильтров).
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserBlacklist(Base):
    __tablename__ = "user_blacklist"

    # Тот же fan-out-паттерн, что и у UserSubscription: username лидирует в
    # составном PK и совпадает с основным запросом («кого заблокировал
    # username») — индекс не нужен, PK уже покрывает.
    # ondelete="CASCADE" — блокировка бессмысленна без того, кто её поставил.
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"), primary_key=True
    )

    # FK на users.username — блокируемый тоже должен быть существующим
    # пользователем. ondelete="CASCADE" — если удалить заблокированного,
    # блокировка на него тоже теряет смысл.
    blocked_user: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"), primary_key=True
    )

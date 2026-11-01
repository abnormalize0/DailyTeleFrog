"""
Этот файл служит для хранения схемы таблицы tag_subscriptions — подписки
пользователя на тег (см. db/user.py::sub_tag, article.py::pages_get для ленты
по подпискам).
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TagSubscription(Base):
    __tablename__ = "tag_subscriptions"

    # Fan-out таблица-связка (см. decisions/0002-db-write-pattern-and-indexes):
    # у каждой подписки своя строка вместо счётчика на теге, поэтому подписка/
    # отписка — это просто INSERT/DELETE, без конкурентной записи в общую
    # строку. tag_name — String(512): теги свободно вводятся пользователями,
    # это не контролируемый словарь, поэтому предел щедрый.
    #
    # tag_name лидирует в составном PK (а не username), хотя основной запрос
    # к этой таблице — «на какие теги подписан username» (по username). Из-за
    # этого запрос по username не покрыт индексом составного PK — компенсируем
    # отдельным index=True на username ниже (см. чек-лист decisions/0002).
    tag_name: Mapped[str] = mapped_column(String(512), primary_key=True)

    # FK на users.username — подписка не может существовать без пользователя.
    # ondelete="CASCADE" — подписка бессмысленна без пользователя, который
    # подписался; при удалении пользователя она должна исчезнуть вместе с ним,
    # а не остаться висящей ссылкой. index=True — см. комментарий у tag_name.
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

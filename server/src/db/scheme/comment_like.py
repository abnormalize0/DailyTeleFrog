"""
Этот файл служит для хранения схемы таблицы comment_likes — лайков комментария.
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CommentLike(Base):
    __tablename__ = "comment_likes"

    # Fan-out таблица-связка, тот же паттерн, что и ArticleLike (см. её
    # комментарии и decisions/0002): comment_id лидирует в составном PK и
    # совпадает с основным запросом («сколько лайков у комментария»), индекс
    # не нужен. ondelete="CASCADE" — лайк бессмысленен без комментария.
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True
    )

    # Тот, кто поставил лайк, а не автор статьи или комментария. Лайк не может
    # существовать без этого пользователя.
    # ondelete="CASCADE" — реакция, а не контент (см. ArticleLike).
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

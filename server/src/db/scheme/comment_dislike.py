"""
Этот файл служит для хранения схемы таблицы comment_dislikes — дизлайков
комментария.
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CommentDislike(Base):
    __tablename__ = "comment_dislikes"

    # Зеркало CommentLike — тот же fan-out-паттерн, тот же ondelete="CASCADE"
    # и та же причина, почему comment_id лидирует в составном PK (см. её
    # комментарии).
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True
    )

    # Тот, кто поставил дизлайк, а не автор статьи или комментария. Дизлайк не
    # может существовать без этого пользователя.
    # ondelete="CASCADE" — реакция, а не контент (см. ArticleLike).
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

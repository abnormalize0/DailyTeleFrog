"""
Этот файл служит для хранения схемы таблицы article_dislikes — дизлайков статьи.
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ArticleDislike(Base):
    __tablename__ = "article_dislikes"

    # Зеркало ArticleLike — тот же fan-out-паттерн, тот же ondelete="CASCADE"
    # (бессмысленно без статьи) и та же причина, почему article_id лидирует в
    # составном PK (см. её комментарии).
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )

    # FK на users.username — дизлайк не может существовать без автора.
    # ondelete="CASCADE" — реакция, а не контент, та же причина, что у
    # ArticleLike.author_username.
    author_username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"), primary_key=True
    )

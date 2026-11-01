"""
Этот файл служит для хранения схемы таблицы article_preview — контента
предпоказа статьи в ленте.
"""

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ArticlePreview(Base):
    __tablename__ = "article_preview"

    # У статьи ровно один предпоказ (отношение один-к-одному), поэтому в
    # качестве PK используется сам article_id (FK на articles.id), а не
    # отдельный суррогатный id, — это одновременно и первичный, и внешний ключ.
    # ondelete="CASCADE" — предпоказ бессмысленен без самой статьи.
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )

    # Контент предпоказа — тоже произвольный JSON без интерпретации сервером
    # (см. Article.body), поэтому Text, а не String(n).
    preview_content: Mapped[str] = mapped_column(Text)

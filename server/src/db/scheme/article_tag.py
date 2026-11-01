"""
Этот файл служит для хранения схемы таблицы article_tags — тегов статьи.
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ArticleTag(Base):
    __tablename__ = "article_tags"

    # Fan-out таблица-связка (см. decisions/0002): своя строка на каждый тег
    # статьи, а не список/строка через запятую — по отдельной таблице можно
    # искать («все статьи с тегом X», см. pages_get) и считать, а по строке
    # через запятую нормально нельзя (см. dailytelefrog-db-schema, п.9).
    # String(512) — теги свободно вводятся пользователями, предел щедрый.
    #
    # tag_name лидирует в составном PK, хотя article.py::tags() ищет теги
    # именно по article_id — этот запрос не покрыт индексом составного PK,
    # компенсируем index=True на article_id ниже (см. decisions/0002).
    tag_name: Mapped[str] = mapped_column(String(512), primary_key=True)

    # FK на articles.id — тег не может существовать без статьи, которой
    # принадлежит. ondelete="CASCADE" — тег бессмысленен без статьи, при
    # удалении статьи удаляем и все её теги. index=True — см. tag_name выше.
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

"""
Этот файл служит для хранения схемы таблицы article_likes — лайков статьи.
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ArticleLike(Base):
    __tablename__ = "article_likes"

    # Fan-out таблица-связка (см. decisions/0002-db-write-pattern-and-indexes):
    # у каждого лайка своя строка вместо счётчика likes_count на статье — это
    # даёт идемпотентность («один пользователь — один лайк на статью») через
    # сам составной PK и не создаёт горячую строку при всплеске лайков на одной
    # статье. Счётчик считается на лету через COUNT(*) (article.py::likes_count).
    #
    # article_id лидирует в составном PK — это совпадает с основным запросом
    # («сколько лайков у статьи», «лайкал ли X статью Y» по article_id), PK
    # уже покрывает такой поиск, отдельный индекс не нужен.
    # ondelete="CASCADE" — лайк бессмысленен без статьи, которую лайкнули.
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )

    # Тот, кто поставил лайк, а не автор статьи или комментария. Лайк не может
    # существовать без этого пользователя.
    # ondelete="CASCADE" — в отличие от Article.author_username (авторство
    # контента), лайк — это реакция, а не контент: если пользователя удалили,
    # его лайки просто перестают существовать, никакого продуктового вопроса
    # здесь нет.
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

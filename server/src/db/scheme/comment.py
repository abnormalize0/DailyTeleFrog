"""
Этот файл служит для хранения схемы таблицы comments — комментариев и ответов
на них.
"""

from sqlalchemy import ForeignKey, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from .base import Base


class Comment(Base):
    __tablename__ = "comments"

    # Суррогатный автоинкрементный id — у комментария нет естественного
    # уникального ключа (текст не уникален), плюс на него ссылается root_id
    # у ответов на этот же комментарий.
    id: Mapped[int] = mapped_column(primary_key=True)

    # FK на articles.id — не часть составного PK (в отличие от таблиц-связок
    # вроде ArticleLike), так как у Comment уже есть свой суррогатный id;
    # обязательное поле — комментарий без статьи не имеет смысла.
    # ondelete="CASCADE" — комментарий бессмысленен без своей статьи, поэтому
    # при удалении статьи удаляем и все её комментарии вместе (в отличие от
    # авторства, тут нет продуктового вопроса «а вдруг захотим оставить»).
    # index=True — comment.py::from_article() ищет именно по этой колонке
    # («все комментарии статьи»), без индекса — full scan.
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )

    # FK на users.username — у комментария всегда есть автор, обязательное
    # поле. ondelete не задан (по умолчанию RESTRICT) — та же причина, что и у
    # Article.author_username: удаления аккаунта в API ещё нет, решение о
    # судьбе чужих комментариев при удалении автора — отдельный продуктовый
    # вопрос на будущее, не молчаливое умолчание.
    author_username: Mapped[str] = mapped_column(
        ForeignKey("users.username"),
    )

    # Текст комментария — свободный текст, поэтому Text, а не String(n). Предел
    # Text в MySQL — 65 535 байт, API проверяет его до записи (см.
    # api_info.TEXT_MAX_BYTES).
    text: Mapped[str] = mapped_column(Text)

    # Мс с 1970 года — единый формат времени по проекту.
    creation_date: Mapped[int] = mapped_column(BigInteger)

    # NULL — комментарий верхнего уровня (не ответ), настоящий внешний ключ на
    # comments.id (self-referential) — не магическое значение вроде -1, чтобы
    # база сама не давала сослаться на несуществующий комментарий. На границе
    # с API исторический sentinel -1 по-прежнему используется — конвертация в
    # NULL и обратно делается в src/db/comment.py, формат ответа клиенту не
    # меняется.
    # ondelete не задан (по умолчанию RESTRICT) — удалить комментарий, на
    # который уже есть ответы, нельзя. Осознанное умолчание: удаления
    # комментария в API пока нет вовсе, а решить, что должно происходить с
    # ответами при удалении родителя (удалить вместе с веткой, поднять их на
    # верхний уровень через SET NULL, и т.п.) — отдельный вопрос на будущее.
    root_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id"))

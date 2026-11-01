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
    # уникального ключа (текст не уникален), плюс на него ссылается parent_id
    # у ответов на этот же комментарий.
    id: Mapped[int] = mapped_column(primary_key=True)

    # FK на articles.id — не часть составного PK (в отличие от таблиц-связок
    # вроде ArticleLike), так как у Comment уже есть свой суррогатный id;
    # обязательное поле — комментарий без статьи не имеет смысла.
    # ondelete="CASCADE" — комментарий бессмысленен без своей статьи, поэтому
    # при удалении статьи удаляем и все её комментарии вместе (в отличие от
    # авторства, тут нет продуктового вопроса «а вдруг захотим оставить»).
    # API удаляет статьи мягко, это правило работает при удалении строки вручную.
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )

    # FK на users.username — у комментария всегда есть автор, обязательное
    # поле. ondelete не задан (по умолчанию RESTRICT) — та же причина, что и у
    # Article.author_username: аккаунт удаляется мягко, строка users остаётся.
    author_username: Mapped[str] = mapped_column(
        ForeignKey("users.username"), index=True
    )

    # Текст комментария — свободный текст, поэтому Text, а не String(n). Предел
    # Text в MySQL — 65 535 байт, API проверяет его до записи (см.
    # api_info.TEXT_MAX_BYTES).
    text: Mapped[str] = mapped_column(Text)

    # Мс с 1970 года — единый формат времени по проекту.
    creation_date: Mapped[int] = mapped_column(BigInteger)

    # Прямой родитель: комментарий, на который отвечают. Это может быть и сам
    # ответ, так что вложенность не ограничена и комментарии образуют дерево.
    # NULL — комментарий верхнего уровня (не ответ), настоящий внешний ключ на
    # comments.id (self-referential) — не магическое значение вроде -1, чтобы
    # база сама не давала сослаться на несуществующий комментарий. В API верхний
    # уровень обозначается -1: конвертация в NULL и обратно делается в
    # src/db/comment.py. То, что родитель лежит в той же статье, база не проверяет,
    # это делает comment.py::add.
    # ondelete="SET NULL", а не CASCADE: каскад по этой связи MySQL разрешает не
    # глубже 15 уровней, и статья с длинной веткой ответов не удалилась бы (ошибка
    # 3008). SET NULL не рекурсивен, поэтому строка статьи удаляется при любой
    # глубине, а её комментарии убирает каскад по article_id. API удаляет
    # комментарии мягко, так что ветки это правило не разрывает.
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("comments.id", ondelete="SET NULL"), index=True
    )

    # Мягкое удаление (см. decisions/0005-soft-delete.md): строка остаётся, чтобы не
    # разрывать ветку ответов. В дереве такой комментарий отдаётся заглушкой, без
    # автора и текста.
    is_deleted: Mapped[bool] = mapped_column(default=False)

"""
Этот файл служит для хранения схемы таблицы articles — основной сущности
статьи.
"""

from sqlalchemy import ForeignKey, String, BigInteger
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Article(Base):
    __tablename__ = "articles"

    # Суррогатный автоинкрементный id — в отличие от User, у статьи нет
    # естественного уникального человекочитаемого ключа (title не уникален и
    # не задумывался как идентификатор).
    id: Mapped[int] = mapped_column(primary_key=True)

    # Заголовок статьи. String(512) — с запасом, но конечный предел, так как
    # заголовок по смыслу короткий текст, а не произвольный контент.
    title: Mapped[str] = mapped_column(String(512))

    # Мс с 1970 года — единый формат времени по проекту; используется для
    # сортировки и границ дат ленты (article.py::pages_get). index=True —
    # именно по этой колонке лента сортируется/фильтруется по умолчанию, без
    # индекса это был бы full scan/filesort по мере роста числа статей.
    creation_date: Mapped[int] = mapped_column(BigInteger, index=True)

    # Тело статьи — JSON произвольной, определяемой frontend'ом структуры
    # (блочный редактор), сервер её не разбирает, поэтому текстовый тип, а не
    # String(n). MEDIUMTEXT, а не Text: в 65 535 байт Text блочная разметка
    # оставляет примерно 34 000 русских символов, а лонгрид бывает длиннее. Предел
    # MEDIUMTEXT — 16 777 215 байт, API проверяет его до записи (см.
    # api_info.ARTICLE_BODY_MAX_BYTES).
    body: Mapped[str] = mapped_column(MEDIUMTEXT)

    # FK на users.username — у статьи всегда есть автор, поле обязательное
    # (без Optional): статья без автора не имеет смысла в модели проекта.
    # ondelete не задан (по умолчанию RESTRICT/запрет): аккаунт удаляется мягко,
    # строка users остаётся, а статьи автора продолжают отображаться (см.
    # decisions/0005-soft-delete.md).
    author_username: Mapped[str] = mapped_column(
        ForeignKey("users.username"), index=True
    )

    # Мягкое удаление (см. decisions/0005-soft-delete.md): удалённая статья не видна
    # ни в одном методе, вместе с ней скрыто всё, что находится внутри неё.
    is_deleted: Mapped[bool] = mapped_column(default=False)

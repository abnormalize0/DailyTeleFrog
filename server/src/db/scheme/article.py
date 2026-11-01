"""
Этот файл служит для хранения схемы таблицы articles — основной сущности
статьи.
"""

from sqlalchemy import ForeignKey, String, Text, BigInteger
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
    # (блочный редактор), сервер её не разбирает, поэтому Text, а не String(n).
    # Предел Text в MySQL — 65 535 байт, API проверяет его до записи (см.
    # api_info.TEXT_MAX_BYTES).
    body: Mapped[str] = mapped_column(Text)

    # FK на users.username — у статьи всегда есть автор, поле обязательное
    # (без Optional): статья без автора не имеет смысла в модели проекта.
    # ondelete не задан (по умолчанию RESTRICT/запрет) — удалить пользователя,
    # пока у него есть статьи, нельзя. Это осознанный выбор по умолчанию, а не
    # забытый случай: удаления аккаунта в API ещё нет, а решить, что должно
    # происходить со статьями удалённого автора (удалить вместе, оставить от
    # имени «удалённого пользователя» и т.п.) — отдельный продуктовый вопрос,
    # который стоит явно обсудить, когда появится сама фича удаления аккаунта.
    #
    # index=True — по этой колонке фильтруется лента (include_authors/
    # exclude_authors и блок-лист авторов в pages_get), без индекса это тоже
    # full scan.
    author_username: Mapped[str] = mapped_column(
        ForeignKey("users.username"), index=True
    )

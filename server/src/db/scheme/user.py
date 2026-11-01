"""
Этот файл служит для хранения схемы таблицы users — основной сущности
пользователя, на которую по username ссылаются все остальные таблицы.
"""

from sqlalchemy import String, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from .base import Base


class User(Base):
    __tablename__ = "users"

    # Первичный ключ пользователя — не суррогатный id, а сам username: это уже
    # готовый уникальный человекочитаемый идентификатор, которым и так
    # оперируют все API-методы, поэтому он же используется как внешний ключ
    # во всех связанных таблицах (лайки, подписки, статьи и т.д.). Не меняется
    # после регистрации, в отличие от nickname. Регистр при сравнении не
    # учитывается (см. base.py). String(32) — разумный предел длины логина.
    username: Mapped[str] = mapped_column(String(32), primary_key=True)

    # unique=True — по email тоже можно войти (см. /auth/login: username или email).
    # Ограничение живёт в самой базе, а не только в коде, чтобы гонка из двух
    # параллельных регистраций не создала дубликат (см. dailytelefrog-db-schema).
    # Регистр при сравнении не учитывается (см. base.py).
    # String(255) — 254 символа: максимальная длина email по RFC 5321, с
    # запасом в 1 символ.
    email: Mapped[str] = mapped_column(String(255), unique=True)

    # Отображаемое имя, в отличие от username может меняться — при каждом
    # изменении старое значение уходит в UserNameHistory.
    nickname: Mapped[str] = mapped_column(String(32))

    # Хранится PBKDF2-HMAC-SHA256 хеш пароля в формате
    # "<итерации>$<соль-hex>$<хеш-hex>" (см. db/user.py::_hash_password), не
    # пароль в открытом виде. 128 символов хватает с запасом (сейчас формат
    # занимает ~104 символа при 600 000 итераций). deferred=True — колонка не
    # подгружается при обычных запросах пользователя (запрашивается отдельно,
    # только там, где реально нужна проверка пароля), чтобы хеш пароля лишний
    # раз не оказывался в памяти/логах ORM.
    password: Mapped[str] = mapped_column(String(128), deferred=True)

    # Мс с 1970 года — единый формат времени по всему проекту, чтобы не
    # путаться при сравнении дат из разных таблиц.
    creation_date: Mapped[int] = mapped_column(BigInteger)

    # Optional — у пользователя может не быть аватара при регистрации.
    # String(4096) — это ссылка (URL), а не сам файл; подписанные ссылки внешних
    # хранилищ бывают длиной в тысячи символов, поэтому предел с большим запасом.
    avatar: Mapped[Optional[str]] = mapped_column(String(4096))

    # Optional — описание профиля необязательно. Text, а не String(n): это
    # свободный текст, в отличие от коротких полей вроде username/nickname.
    # Предел Text в MySQL — 65 535 байт, API проверяет его до записи (см.
    # api_info.TEXT_MAX_BYTES).
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Мягкое удаление (см. decisions/0005-soft-delete.md): строка остаётся, потому
    # что на неё ссылаются статьи и комментарии. username и email остаются занятыми.
    is_deleted: Mapped[bool] = mapped_column(default=False)

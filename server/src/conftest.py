"""
Этот файл служит для хранения fixtures pytest для unit-тестов в src/: сессии к
настоящей тестовой MySQL и фабрики пользователей. Тесты вызывают функции напрямую,
без сервера и HTTP, а БД подключается, только если тест запросил fixture `session`.
SQLite не подходит: схема использует MEDIUMTEXT, а смысл
проверок дубликатов задаёт правило сравнения строк MySQL (см.
decisions/0006-unit-tests.md).
"""

import os
from collections.abc import Callable, Generator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from src.db import scheme


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    """Создаёт engine к тестовой БД и один раз на прогон пересоздаёт таблицы.

    Args:
        None

    Returns:
        sqlalchemy.Engine: engine, подключенный к MVP_DB_URL_TEST.
    """
    engine = create_engine(os.environ["MVP_DB_URL_TEST"])
    scheme.Base.metadata.drop_all(engine)
    scheme.Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(db_engine: Engine) -> Generator[Session, None, None]:
    """Даёт сессию, изменения которой исчезают после теста.

    Args:
        db_engine: fixture engine тестовой БД.

    Returns:
        Generator[Session]: сессия SQLAlchemy.
    """
    # Функции src/db только делают flush, а commit остаётся за API-методами, поэтому
    # выход из контекста без commit откатывает всё, что сделал тест. Это намного
    # быстрее, чем пересоздавать таблицы перед каждым тестом, как в tests/routes.
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def add_user(session: Session) -> Callable[[str], str]:
    """Даёт функцию для создания пользователя прямой вставкой строки.

    Args:
        session: fixture сессии.

    Returns:
        Callable[[str], str]: функция (username) -> username.
    """

    def _add_user(username: str) -> str:
        # Вставка в обход user.add_user: хеширование пароля занимает десятые доли
        # секунды, а большинству тестов нужен только сам факт наличия пользователя.
        session.add(
            scheme.User(
                username=username,
                email=f"{username}@test.test",
                nickname=f"{username}_nickname",
                password="unused",
                creation_date=0,
            )
        )
        session.flush()
        return username

    return _add_user

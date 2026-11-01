"""
Этот файл служит для хранения общих хелперов unit-тестов в src/: проверки ошибок
(тест обязан сверить не только вид ошибки, но и её текст, который увидит клиент) и
подготовки строк для тестов на гонки.
"""

from sqlalchemy.orm import Session

from src.db import scheme
from src.request_status import ErrorType, Status


def assert_error_status(status: Status, error_type: ErrorType, detail: str) -> None:
    """Проверяет, что `Status` — ошибка ожидаемого вида с ожидаемым текстом.

    Args:
        status: проверяемый статус.
        error_type: ожидаемый вид ошибки.
        detail: ожидаемый текст ошибки.

    Returns:
        None
    """
    assert status.is_error
    problem = status.problem()
    assert problem["type"] == f"/errors/{error_type.slug}", problem
    assert problem["detail"] == detail, problem


def user_row(username: str) -> scheme.User:
    """Строит строку пользователя без хеширования пароля: оно занимает десятые доли
    секунды, а большинству тестов нужен только сам факт наличия пользователя.

    Args:
        username: имя пользователя.

    Returns:
        Строка таблицы users, ещё не добавленная в сессию.
    """
    return scheme.User(
        username=username,
        email=f"{username}@test.test",
        nickname=f"{username}_nickname",
        password="unused",
        creation_date=0,
    )


def open_snapshot(session: Session) -> None:
    """Фиксирует снимок данных для транзакции session.

    При REPEATABLE READ транзакция с этого момента не видит чужих коммитов, но
    уникальные ключи их видят. Строка, закоммиченная после вызова, в точности повторяет
    гонку: проверка её не находит, а вставка падает на ключе. Настоящая база делает
    гонку детерминированной, без моков и потоков. Поэтому engine из src/conftest.py
    намеренно остаётся на REPEATABLE READ, хотя сервер работает на READ COMMITTED.

    Args:
        session: проверяемая сессия.

    Returns:
        None
    """
    session.query(scheme.User).first()

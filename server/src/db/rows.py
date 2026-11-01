"""
Этот файл служит для хранения записи строк-связей, общей для пользователей, статей и
комментариев: в этих таблицах весь первичный ключ составлен из значений строки, поэтому
повторная вставка означает, что нужное состояние уже достигнуто.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import scheme


def add_if_missing(session: Session, model: type, **columns: str) -> None:
    """Добавляет строку таблицы со связью или историей, если её ещё нет.

    Для клиента повтор не ошибка: PUT и PATCH описывают нужное состояние, и оно уже
    достигнуто. Проверки перед вставкой мало: параллельный запрос может вставить ту же
    строку между проверкой и записью, и тогда конфликт вернул бы клиенту 500.

    Вставка идёт в точке сохранения: сбой обычного flush откатил бы всю транзакцию
    вместе с остальными изменениями запроса, а значит нарушил бы атомарность метода
    (см. decisions/0009-api-atomicity.md). IntegrityError здесь может означать только
    повтор: внешние ключи ведут на объекты, которые вызывающий уже проверил, а
    физически они не удаляются (см. decisions/0005-soft-delete.md).

    Args:
        session: сессия SQLAlchemy.
        model: класс таблицы из scheme.
        **columns: значения всех колонок первичного ключа.

    Returns:
        None
    """
    if session.query(model).filter_by(**columns).first() is not None:
        return
    try:
        with session.begin_nested():
            session.add(model(**columns))
    except IntegrityError:
        pass


def lock_user_reactions(session: Session, username: str) -> None:
    """Выстраивает в очередь изменения реакций одного пользователя до конца транзакции.

    Лайк и дизлайк лежат в разных таблицах, поэтому первичный ключ не запрещает им
    существовать одновременно. Параллельные PUT лайка и дизлайка не увидели бы вставку
    друг друга и оставили бы обе реакции. Блокируется строка пользователя, а не строка
    реакции: она есть всегда, и реакции других пользователей этого ждать не будут.

    Защита работает только при READ COMMITTED (см. shared.get_session): при REPEATABLE
    READ запрос, дождавшийся блокировки, читал бы снимок из начала транзакции и всё равно
    не видел бы чужую реакцию.

    Args:
        session: сессия SQLAlchemy.
        username: кто меняет реакцию.

    Returns:
        None
    """
    session.query(scheme.User.username).where(
        scheme.User.username == username
    ).with_for_update().first()

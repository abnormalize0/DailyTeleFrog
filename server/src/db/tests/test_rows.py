"""
Этот файл служит для хранения unit-тестов src/db/rows.py на настоящей MySQL: повторная
вставка строки-связи не должна мешать остальным изменениям транзакции.
"""

from collections.abc import Callable

from sqlalchemy.orm import Session

from src.db import rows, scheme
from src.tests.helpers import open_snapshot, user_row


def test_add_if_missing_adds_row_once(session: Session, add_user: Callable) -> None:
    add_user("frog")

    for _ in range(2):
        rows.add_if_missing(
            session, scheme.TagSubscription, tag_name="tag", username="frog"
        )

    assert session.query(scheme.TagSubscription).count() == 1


def test_add_if_missing_lost_race_keeps_transaction(
    session: Session, commit_rows: Callable
) -> None:
    commit_rows(user_row("frog"))
    open_snapshot(session)
    commit_rows(scheme.TagSubscription(tag_name="tag", username="frog"))
    session.get(scheme.User, "frog").nickname = "changed_before_insert"
    session.flush()

    rows.add_if_missing(
        session, scheme.TagSubscription, tag_name="tag", username="frog"
    )
    session.commit()

    # Читается новая транзакция: изменение до вставки должно пережить конфликт.
    assert session.get(scheme.User, "frog").nickname == "changed_before_insert"
    assert session.query(scheme.TagSubscription).count() == 1

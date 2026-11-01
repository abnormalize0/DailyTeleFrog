"""
Этот файл служит для хранения общей проверки ошибок для unit-тестов в src/: тест
обязан сверить не только вид ошибки, но и её текст, который увидит клиент.
"""

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

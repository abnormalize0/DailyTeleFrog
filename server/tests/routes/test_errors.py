"""
Этот файл служит для хранения e2e-тестов ошибок, общих для всех API-методов: их
выдаёт Flask или авторизация ещё до логики метода, поэтому своего файла ресурса у
них нет.
"""

from collections.abc import Callable

import requests

from tests.helpers import LOCALHOST, assert_error, auth_headers

FLASK_NOT_FOUND = (
    "The requested URL was not found on the server. If you entered the URL manually "
    "please check your spelling and try again."
)


def _assert_flask_problem(answer: requests.Response, code: int, detail: str) -> None:
    """Проверяет ошибку самого Flask: у неё нет нашего ErrorType, поэтому `type`
    равен "about:blank" (см. shared.handle_http_exception).

    Args:
        answer: ответ сервера.
        code: ожидаемый HTTP-код.
        detail: ожидаемый текст ошибки.

    Returns:
        None
    """
    assert answer.status_code == code, answer.text
    assert answer.headers["Content-Type"] == "application/problem+json"
    problem = answer.json()
    assert problem["type"] == "about:blank", problem
    assert problem["status"] == code, problem
    assert problem["detail"] == detail, problem


def test_unknown_path() -> None:
    _assert_flask_problem(
        requests.get(LOCALHOST + "/no-such-path"), 404, FLASK_NOT_FOUND
    )


def test_path_with_wrong_id_type() -> None:
    _assert_flask_problem(
        requests.get(LOCALHOST + "/articles/abc"), 404, FLASK_NOT_FOUND
    )


def test_id_larger_than_column() -> None:
    # Значение не помещается в колонку INT, но не должно доходить до ошибки MySQL.
    article_id = 10**30

    assert_error(
        requests.get(f"{LOCALHOST}/articles/{article_id}"),
        "not-found",
        f"Cannot find article with id: {article_id}",
    )


def test_wrong_method_lists_allowed_ones() -> None:
    answer = requests.patch(LOCALHOST + "/articles")

    _assert_flask_problem(
        answer, 405, "The method is not allowed for the requested URL."
    )
    assert "GET" in answer.headers["Allow"]


def test_malformed_authorization_header(add_user: Callable) -> None:
    _, _, _, _, access_token, _ = add_user()

    for authorization in (
        access_token,
        f"Basic {access_token}",
        f"bearer {access_token}",
        "Bearer",
        "Bearer ",
        "Bearer unknown",
        "Bearer " + "x" * 5000,
    ):
        assert_error(
            requests.post(
                LOCALHOST + "/auth/logout-all",
                headers={"Authorization": authorization},
            ),
            "invalid-token",
            "Missing or invalid token",
        )

    # Проверка, что неудачные попытки не задели настоящую сессию.
    answer = requests.post(
        LOCALHOST + "/auth/logout-all", headers=auth_headers(access_token)
    )
    assert answer.status_code == 204


def test_refresh_token_is_not_accepted_as_access_token(add_user: Callable) -> None:
    _, _, _, _, _, refresh_token = add_user()

    assert_error(
        requests.post(
            LOCALHOST + "/auth/logout-all", headers=auth_headers(refresh_token)
        ),
        "invalid-token",
        "Missing or invalid token",
    )


def test_access_token_is_not_accepted_as_refresh_token(add_user: Callable) -> None:
    _, _, _, _, access_token, _ = add_user()

    assert_error(
        requests.post(
            LOCALHOST + "/auth/refresh", json={"refresh_token": access_token}
        ),
        "invalid-token",
        "Missing or invalid token",
    )

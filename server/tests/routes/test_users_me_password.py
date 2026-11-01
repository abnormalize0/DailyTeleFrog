"""
Этот файл служит для хранения теста на API-метод PUT /users/me/password.
"""

from collections.abc import Callable

import requests

from tests.helpers import (
    LOCALHOST,
    assert_error,
    assert_ok,
    assert_preflight_allows,
    auth_headers,
    check_endpoint_structure,
)


def test_users_me_password_put(add_user: Callable) -> None:
    endpoint = "/users/me/password"
    check_endpoint_structure(endpoint, "put")
    assert_preflight_allows(endpoint, "PUT")

    username, password, _, _, access_token, _ = add_user()

    # wrong previous password must be rejected
    answer = requests.put(
        LOCALHOST + endpoint,
        json={"previous_password": password + "wrong", "new_password": "1234"},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "forbidden")
    login_answer = requests.post(
        LOCALHOST + "/auth/login",
        json={"username": username, "password": password},
    )
    assert_ok(login_answer)

    # happy path
    answer = requests.put(
        LOCALHOST + endpoint,
        json={"previous_password": password, "new_password": "1234"},
        headers=auth_headers(access_token),
    )
    assert_ok(answer, 204)
    login_answer = requests.post(
        LOCALHOST + "/auth/login",
        json={"username": username, "password": "1234"},
    )
    assert_ok(login_answer)

    # Проверка, что смена пароля отзывает старый access token.
    answer = requests.get(
        LOCALHOST + "/users/me",
        params={"requested_data": "nickname"},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "invalid-token")

    # Проверка, что без токена пароль не сменить.
    answer = requests.put(
        LOCALHOST + endpoint,
        json={"previous_password": "1234", "new_password": "5678"},
    )
    assert_error(answer, "invalid-token")

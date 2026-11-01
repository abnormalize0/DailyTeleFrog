"""
Этот файл служит для хранения теста на API-метод POST /auth/login.
"""

from collections.abc import Callable

import requests

from tests.helpers import (
    LOCALHOST,
    assert_error,
    assert_ok,
    auth_headers,
    check_endpoint_structure,
    read_server_log,
)


def test_auth_login_post(add_user: Callable) -> None:
    endpoint = "/auth/login"
    check_endpoint_structure(endpoint, "post")

    username, password, _, email, _, _ = add_user()

    # happy path: login by username
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"username": username, "password": password},
    )
    assert_ok(answer)
    assert "access_token" in answer.json()
    assert "refresh_token" in answer.json()

    # happy path: login by email
    answer = requests.post(
        LOCALHOST + endpoint, json={"email": email, "password": password}
    )
    assert_ok(answer)
    assert "access_token" in answer.json()
    assert "refresh_token" in answer.json()

    # Проверка, что выданный access token реально работает на защищённом методе.
    access_token = answer.json()["access_token"]
    profile_answer = requests.get(
        LOCALHOST + "/users/me",
        params={"requested_data": "nickname"},
        headers=auth_headers(access_token),
    )
    assert_ok(profile_answer)

    # Проверка, что пароль и выданные токены не попали в лог.
    server_log = read_server_log()
    assert password not in server_log
    assert access_token not in server_log

    # wrong password must be rejected
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"username": username, "password": password + "wrong"},
    )
    assert_error(answer, "invalid-credentials", "Incorrect login or password")

    # Проверка, что несуществующий пользователь неотличим от неверного пароля.
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"username": "nobody", "password": password},
    )
    assert_error(answer, "invalid-credentials", "Incorrect login or password")

    # both username and email must be rejected
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"username": username, "email": email, "password": password},
    )
    assert_error(
        answer, "validation", "User cannot log in with both username and email"
    )

    # neither username nor email must be rejected, not crash
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"password": password},
    )
    assert_error(answer, "validation", "User must log in with username or email")

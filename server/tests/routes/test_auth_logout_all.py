"""
Этот файл служит для хранения теста на API-метод POST /auth/logout-all.
"""

from collections.abc import Callable

import requests

from tests.helpers import (
    LOCALHOST,
    assert_error,
    assert_ok,
    auth_headers,
    check_endpoint_structure,
)


def test_auth_logout_all_post(add_user: Callable) -> None:
    endpoint = "/auth/logout-all"
    check_endpoint_structure(endpoint, "post")

    username, password, _, _, access_token, refresh_token = add_user()
    _, _, _, _, other_access_token, _ = add_user()

    # Вторая сессия того же пользователя, как с другого устройства.
    answer = requests.post(
        LOCALHOST + "/auth/login", json={"username": username, "password": password}
    )
    assert_ok(answer)
    second_access_token = answer.json()["access_token"]
    second_refresh_token = answer.json()["refresh_token"]

    # Проверка, что без токена нельзя завершить сессии.
    assert_error(requests.post(LOCALHOST + endpoint), "invalid-token")

    # happy path
    answer = requests.post(LOCALHOST + endpoint, headers=auth_headers(access_token))
    assert_ok(answer, 204)

    # Проверка, что отозваны access токены обеих сессий.
    for token in (access_token, second_access_token):
        answer = requests.get(
            LOCALHOST + "/users/me",
            params={"requested_data": "nickname"},
            headers=auth_headers(token),
        )
        assert_error(answer, "invalid-token")

    # Проверка, что отозваны и refresh токены обеих сессий.
    for token in (refresh_token, second_refresh_token):
        answer = requests.post(
            LOCALHOST + "/auth/refresh", json={"refresh_token": token}
        )
        assert_error(answer, "invalid-token")

    # Проверка, что сессии другого пользователя не затронуты.
    answer = requests.get(
        LOCALHOST + "/users/me",
        params={"requested_data": "nickname"},
        headers=auth_headers(other_access_token),
    )
    assert_ok(answer)

"""
Этот файл служит для хранения теста на API-метод POST /auth/logout.
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


def test_auth_logout_post(add_user: Callable) -> None:
    endpoint = "/auth/logout"
    check_endpoint_structure(endpoint, "post")

    _, _, _, _, access_token, refresh_token = add_user()

    # Проверка, что без токена нельзя разлогиниться.
    answer = requests.post(LOCALHOST + endpoint, json={"refresh_token": refresh_token})
    assert_error(answer, "invalid-token")

    # happy path
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"refresh_token": refresh_token},
        headers=auth_headers(access_token),
    )
    assert_ok(answer, 204)

    # Проверка, что access token отозван.
    profile_answer = requests.get(
        LOCALHOST + "/users/me",
        params={"requested_data": "nickname"},
        headers=auth_headers(access_token),
    )
    assert_error(profile_answer, "invalid-token")

    # Проверка, что refresh token тоже отозван.
    refresh_answer = requests.post(
        LOCALHOST + "/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert_error(refresh_answer, "invalid-token")

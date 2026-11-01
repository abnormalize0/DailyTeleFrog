"""
Этот файл служит для хранения теста на API-метод POST /auth/refresh.
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


def test_auth_refresh_post(add_user: Callable) -> None:
    endpoint = "/auth/refresh"
    check_endpoint_structure(endpoint, "post")

    _, _, _, _, access_token, refresh_token = add_user()

    # happy path: получаем новую пару токенов
    answer = requests.post(LOCALHOST + endpoint, json={"refresh_token": refresh_token})
    assert_ok(answer)
    new_access_token = answer.json()["access_token"]
    new_refresh_token = answer.json()["refresh_token"]
    assert new_access_token != access_token
    assert new_refresh_token != refresh_token

    # Проверка, что новый access token работает.
    profile_answer = requests.get(
        LOCALHOST + "/users/me",
        params={"requested_data": "nickname"},
        headers=auth_headers(new_access_token),
    )
    assert_ok(profile_answer)

    # Проверка ротации: старый refresh token больше не работает.
    answer = requests.post(LOCALHOST + endpoint, json={"refresh_token": refresh_token})
    assert_error(answer, "invalid-token", "Missing or invalid token")

    # Проверка, что токены не попали в лог ни из запроса, ни из ответа.
    server_log = read_server_log()
    for token in (refresh_token, new_refresh_token, new_access_token):
        assert token not in server_log

    # invalid refresh token
    answer = requests.post(LOCALHOST + endpoint, json={"refresh_token": "bogus_token"})
    assert_error(answer, "invalid-token", "Missing or invalid token")

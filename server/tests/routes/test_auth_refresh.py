"""
Этот файл служит для хранения теста на API-метод POST /auth/refresh.
"""

from collections.abc import Callable

import requests
from sqlalchemy import Engine, text

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


def test_auth_refresh_removes_expired_tokens(
    add_user: Callable, db_engine: Engine, read_all_rows: Callable
) -> None:
    username, password, _, _, expired_access, expired_refresh = add_user()
    answer = requests.post(
        LOCALHOST + "/auth/login", json={"username": username, "password": password}
    )
    assert_ok(answer)
    # Срок меняется только у первой пары: второй токен нужен для самого запроса.
    with db_engine.begin() as connection:
        connection.execute(
            text("UPDATE access_tokens SET expires_at = 1 WHERE token = :token"),
            {"token": expired_access},
        )
        connection.execute(
            text("UPDATE refresh_tokens SET expires_at = 1 WHERE token = :token"),
            {"token": expired_refresh},
        )

    # Проверка, что успешное обновление убирает просроченные токены после commit
    answer = requests.post(
        LOCALHOST + "/auth/refresh",
        json={"refresh_token": answer.json()["refresh_token"]},
    )
    assert_ok(answer)
    after = read_all_rows()
    assert expired_access not in [row.token for row in after["access_tokens"]]
    assert [row.token for row in after["refresh_tokens"]] == [
        answer.json()["refresh_token"]
    ]

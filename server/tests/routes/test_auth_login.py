"""
Этот файл служит для хранения теста на API-метод POST /auth/login.
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


def test_auth_login_removes_expired_tokens(
    add_user: Callable, db_engine: Engine, read_all_rows: Callable
) -> None:
    username, password, _, _, access_token, refresh_token = add_user()
    # По HTTP срок жизни не изменить, а удаление важно проверить после настоящего
    # commit: внутри одной транзакции оно видно, даже если потом откатится.
    with db_engine.begin() as connection:
        connection.execute(text("UPDATE access_tokens SET expires_at = 1"))
        connection.execute(text("UPDATE refresh_tokens SET expires_at = 1"))
    before = read_all_rows()

    # Проверка, что отказ по просроченному токену ничего не меняет
    answer = requests.get(
        LOCALHOST + "/users/me",
        params={"requested_data": "email"},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "invalid-token", "Missing or invalid token")
    answer = requests.post(
        LOCALHOST + "/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert_error(answer, "invalid-token", "Missing or invalid token")
    assert read_all_rows() == before

    # Проверка, что после успешного входа остаются только новые токены
    answer = requests.post(
        LOCALHOST + "/auth/login", json={"username": username, "password": password}
    )
    assert_ok(answer)
    after = read_all_rows()
    assert [row.token for row in after["access_tokens"]] == [
        answer.json()["access_token"]
    ]
    assert [row.token for row in after["refresh_tokens"]] == [
        answer.json()["refresh_token"]
    ]

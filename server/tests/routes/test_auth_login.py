"""
Этот файл служит для хранения теста на API-метод POST /auth/login.
"""

import time
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

    # both username and email must be rejected (even when one is empty)
    for both in (
        {"username": username, "email": "", "password": password},
        {"username": "", "email": email, "password": password},
        {"username": "", "email": "", "password": password},
        {"username": username, "email": email, "password": password},
    ):
        answer = requests.post(LOCALHOST + endpoint, json=both)
        assert_error(
            answer, "validation", "User cannot log in with both username and email"
        )
        assert answer.json()["errors"] == [
            {"pointer": "/username", "detail": "cannot be used together with email"},
            {"pointer": "/email", "detail": "cannot be used together with username"},
        ]

    # neither username nor email must be rejected, not crash
    for empty_id in (
        {"password": password},
        {"username": "", "password": password},
        {"email": "", "password": password},
    ):
        answer = requests.post(LOCALHOST + endpoint, json=empty_id)
        assert_error(answer, "validation", "User must log in with username or email")
        assert answer.json()["errors"] == [
            {"pointer": "/username", "detail": "username or email is required"},
            {"pointer": "/email", "detail": "username or email is required"},
        ]


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


def test_auth_login_uppercase_username_normalizes_session(
    add_user: Callable, db_engine: Engine, read_all_rows: Callable
) -> None:
    username, password, _, email, _, _ = add_user()

    answer = requests.post(
        LOCALHOST + "/auth/login",
        json={"username": username.upper(), "password": password},
    )
    assert_ok(answer)
    access_token = answer.json()["access_token"]
    refresh_token = answer.json()["refresh_token"]
    headers = auth_headers(access_token)

    with db_engine.connect() as connection:
        access_owner = connection.execute(
            text("SELECT username FROM access_tokens WHERE token = :token"),
            {"token": access_token},
        ).scalar_one()
        refresh_owner = connection.execute(
            text("SELECT username FROM refresh_tokens WHERE token = :token"),
            {"token": refresh_token},
        ).scalar_one()
    assert access_owner == username
    assert refresh_owner == username

    # Права владельца и авторство контента в сессии работают в нижнем регистре.
    article_answer = requests.post(
        LOCALHOST + "/articles",
        json={
            "title": "title",
            "body": {"text": "body"},
            "preview": {"text": "preview"},
            "tags": ["tag1"],
        },
        headers=headers,
    )
    assert_ok(article_answer, 201)
    article_id = article_answer.json()["article_id"]
    rows = read_all_rows()
    assert [
        row.author_username for row in rows["articles"] if row.id == article_id
    ] == [username]

    for reaction in ("like", "dislike"):
        react_answer = requests.put(
            f"{LOCALHOST}/articles/{article_id}/{reaction}", headers=headers
        )
        assert_error(
            react_answer,
            "forbidden",
            "User cannot like or dislike their own article",
        )

    comment_answer = requests.post(
        f"{LOCALHOST}/articles/{article_id}/comments",
        json={"text": "comment", "parent": -1},
        headers=headers,
    )
    assert_ok(comment_answer, 201)
    comment_id = comment_answer.json()["id"]
    react_comment = requests.put(
        f"{LOCALHOST}/comments/{comment_id}/like", headers=headers
    )
    assert_error(
        react_comment,
        "forbidden",
        "User cannot like or dislike their own comment",
    )
    assert_ok(
        requests.delete(f"{LOCALHOST}/comments/{comment_id}", headers=headers), 204
    )
    assert_ok(
        requests.delete(f"{LOCALHOST}/articles/{article_id}", headers=headers), 204
    )

    # Повторный PATCH /users/me со своим текущим email не даёт ложный 409.
    assert_ok(
        requests.patch(LOCALHOST + "/users/me", json={"email": email}, headers=headers),
        204,
    )

    # После refresh в новых токенах тоже остаётся канонический username.
    refresh_answer = requests.post(
        LOCALHOST + "/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert_ok(refresh_answer)
    with db_engine.connect() as connection:
        new_access_owner = connection.execute(
            text("SELECT username FROM access_tokens WHERE token = :token"),
            {"token": refresh_answer.json()["access_token"]},
        ).scalar_one()
        new_refresh_owner = connection.execute(
            text("SELECT username FROM refresh_tokens WHERE token = :token"),
            {"token": refresh_answer.json()["refresh_token"]},
        ).scalar_one()
    assert new_access_owner == username
    assert new_refresh_owner == username


def test_auth_login_timing_equalized(add_user: Callable) -> None:
    endpoint = "/auth/login"
    username, password, _, _, _, _ = add_user()
    deleted_username, deleted_password, _, deleted_email, deleted_token, _ = add_user()
    assert_ok(
        requests.delete(
            LOCALHOST + "/users/me",
            json={"password": deleted_password},
            headers=auth_headers(deleted_token),
        ),
        204,
    )

    # Берём минимум из двух прогонов, чтобы единичный всплеск CPU не завышал порог.
    baseline_runs = []
    for _ in range(2):
        started = time.perf_counter()
        answer = requests.post(
            LOCALHOST + endpoint,
            json={"username": username, "password": password + "wrong"},
        )
        elapsed = time.perf_counter() - started
        assert_error(answer, "invalid-credentials", "Incorrect login or password")
        baseline_runs.append(elapsed)
    baseline = min(baseline_runs)
    assert baseline > 0.02

    # Проверка, что время ответа для несуществующего и удалённого пользователя
    # сопоставимо со временем ответа при неверном пароле существующего аккаунта.
    for payload in (
        {"username": "nobody", "password": password},
        {"email": "nobody@test.test", "password": password},
        {"username": deleted_username, "password": deleted_password},
        {"email": deleted_email, "password": deleted_password},
    ):
        started = time.perf_counter()
        answer = requests.post(LOCALHOST + endpoint, json=payload)
        elapsed = time.perf_counter() - started
        assert_error(answer, "invalid-credentials", "Incorrect login or password")
        assert elapsed >= baseline * 0.4

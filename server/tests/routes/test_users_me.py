"""
Этот файл служит для хранения тестов на API-методы пути /users/me: чтение (GET),
изменение (PATCH) и удаление (DELETE) данных пользователя.
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
    read_field,
    read_server_log,
)

ENDPOINT = "/users/me"


def test_users_me_get(add_user: Callable) -> None:
    check_endpoint_structure(ENDPOINT, "get")

    _, _, _, _, access_token, _ = add_user()

    # happy path
    requested_data = [
        "nickname",
        "email",
        "name_history",
        "avatar",
        "blocked_tags",
        "creation_date",
        "rating",
    ]
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"requested_data": requested_data},
        headers=auth_headers(access_token),
    )
    assert_ok(answer)
    assert "nickname" in answer.json()
    assert "email" in answer.json()
    assert "name_history" in answer.json()
    assert "avatar" in answer.json()
    assert "creation_date" in answer.json()
    assert "rating" in answer.json()

    # Проверка, что без токена профиль не получить.
    answer = requests.get(
        LOCALHOST + ENDPOINT, params={"requested_data": requested_data}
    )
    assert_error(answer, "invalid-token", "Missing or invalid token")


def test_users_me_patch(add_user: Callable) -> None:
    check_endpoint_structure(ENDPOINT, "patch")
    assert_preflight_allows(ENDPOINT, "PATCH")

    own_username, _, user_name, _, access_token, _ = add_user()
    headers = auth_headers(access_token)

    # happy path
    nickname = "new_name"
    email = "new_email@email.email"
    avatar = "avatar_link"
    answer = requests.patch(
        LOCALHOST + ENDPOINT,
        json={"nickname": nickname, "avatar": avatar, "email": email},
        headers=headers,
    )
    assert_ok(answer, 204)

    requested_data = ["nickname", "email", "name_history", "avatar"]
    answer = requests.get(
        LOCALHOST + ENDPOINT, params={"requested_data": requested_data}, headers=headers
    )
    assert_ok(answer)
    assert answer.json()["nickname"] == nickname
    assert answer.json()["name_history"] == [user_name]
    assert answer.json()["avatar"] == avatar

    # Проверка, что непереданные поля не меняются.
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"description": "text"}, headers=headers
    )
    assert_ok(answer, 204)
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"requested_data": ["nickname", "description"]},
        headers=headers,
    )
    assert answer.json()["nickname"] == nickname
    assert answer.json()["description"] == "text"

    # subscriptions and blacklists (tags and users)
    other_username, _, _, _, _, _ = add_user()
    answer = requests.patch(
        LOCALHOST + ENDPOINT,
        json={
            "sub-tags": ["tag1", "tag2"],
            "blocked-tags": ["tag3"],
            "sub-users": [other_username],
        },
        headers=headers,
    )
    assert_ok(answer, 204)

    requested_data = ["sub_tags", "blocked_tags", "sub_users", "blocked_users"]
    answer = requests.get(
        LOCALHOST + ENDPOINT, params={"requested_data": requested_data}, headers=headers
    )
    assert_ok(answer)
    assert sorted(answer.json()["sub_tags"]) == ["tag1", "tag2"]
    assert answer.json()["blocked_tags"] == ["tag3"]
    assert answer.json()["sub_users"] == [other_username]
    assert answer.json()["blocked_users"] == []

    # blocking a user must remove any existing subscription to them, and vice versa
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"blocked-users": [other_username]}, headers=headers
    )
    assert_ok(answer, 204)
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"requested_data": ["sub_users", "blocked_users"]},
        headers=headers,
    )
    assert answer.json()["sub_users"] == []
    assert answer.json()["blocked_users"] == [other_username]

    # Проверка, что повторные подписка и блокировка не являются ошибкой.
    answer = requests.patch(
        LOCALHOST + ENDPOINT,
        json={
            "sub-tags": ["tag1", "tag1"],
            "blocked-tags": ["tag3"],
            "blocked-users": [other_username],
        },
        headers=headers,
    )
    assert_ok(answer, 204)
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"sub-users": [other_username]}, headers=headers
    )
    assert_ok(answer, 204)
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"sub-users": [other_username]}, headers=headers
    )
    assert_ok(answer, 204)

    # Проверка, что нельзя подписаться на себя или заблокировать себя, а частичные
    # изменения запроса откатываются.
    for field in ("sub-users", "blocked-users"):
        answer = requests.patch(
            LOCALHOST + ENDPOINT,
            json={"avatar": "rolled_back", field: [own_username]},
            headers=headers,
        )
        assert_error(
            answer, "forbidden", "User cannot subscribe to or block themselves"
        )
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"requested_data": ["sub_users", "blocked_users", "avatar"]},
        headers=headers,
    )
    assert own_username not in answer.json()["sub_users"]
    assert own_username not in answer.json()["blocked_users"]
    assert answer.json()["avatar"] == avatar

    # Проверка, что лимиты длины работают и в PATCH: значения предельной длины
    # сохраняются (слишком длинные отвергает check_endpoint_structure).
    answer = requests.patch(
        LOCALHOST + ENDPOINT,
        json={"sub-tags": ["т" * 512], "blocked-tags": ["б" * 512]},
        headers=headers,
    )
    assert_ok(answer, 204)

    # Проверка, что на несуществующего пользователя нельзя подписаться или
    # заблокировать его, а частичные изменения запроса откатываются.
    for field in ("sub-users", "blocked-users"):
        answer = requests.patch(
            LOCALHOST + ENDPOINT,
            json={"avatar": "rolled_back", field: ["nobody"]},
            headers=headers,
        )
        assert_error(answer, "validation", "Cannot find user with username: nobody")
    assert read_field(ENDPOINT, "avatar", access_token) == avatar

    # Проверка, что PATCH применяет те же правила, что регистрация, и не меняет поля.
    for invalid in (
        {"nickname": "   "},
        {"email": "not-an-email"},
        {"sub-tags": ["tag", " "]},
        {"blocked-tags": ["\u200b"]},
    ):
        answer = requests.patch(
            LOCALHOST + ENDPOINT,
            json={"avatar": "rolled_back", **invalid},
            headers=headers,
        )
        assert_error(answer, "validation", "Wrong request parameters structure")
    assert read_field(ENDPOINT, "avatar", access_token) == avatar

    # Проверка, что нельзя занять чужой email, а свой указать повторно можно.
    other_email = "other@email.email"
    _, _, _, other_user_email, _, _ = add_user()
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"email": other_user_email}, headers=headers
    )
    assert_error(answer, "conflict", "User with email test_2@test.test already exists")
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"email": email}, headers=headers
    )
    assert_ok(answer, 204)
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"email": other_email}, headers=headers
    )
    assert_ok(answer, 204)

    # Проверка, что можно вернуться к прежнему nickname.
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"nickname": user_name}, headers=headers
    )
    assert_ok(answer, 204)
    assert read_field(ENDPOINT, "nickname", access_token) == user_name
    assert sorted(read_field(ENDPOINT, "name_history", access_token)) == sorted(
        [nickname, user_name]
    )

    # Проверка, что без токена профиль не обновить.
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"nickname": nickname, "avatar": avatar}
    )
    assert_error(answer, "invalid-token", "Missing or invalid token")


def test_users_me_delete(add_user: Callable, add_article: Callable) -> None:
    check_endpoint_structure(ENDPOINT, "delete")
    assert_preflight_allows(ENDPOINT, "DELETE")
    username, password, nickname, email, access_token, refresh_token = add_user()
    _, _, _, _, follower_token, _ = add_user()
    article_id = add_article(access_token)
    answer = requests.patch(
        LOCALHOST + ENDPOINT,
        json={"sub-users": [username]},
        headers=auth_headers(follower_token),
    )
    assert_ok(answer, 204)

    # Проверка, что без токена аккаунт не удалить.
    answer = requests.delete(LOCALHOST + ENDPOINT, json={"password": password})
    assert_error(answer, "invalid-token", "Missing or invalid token")

    # Проверка, что с неверным паролем аккаунт не удаляется.
    answer = requests.delete(
        LOCALHOST + ENDPOINT,
        json={"password": "wrong_password"},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "forbidden", "Incorrect password")
    assert read_field(ENDPOINT, "nickname", access_token) == nickname

    # happy path
    answer = requests.delete(
        LOCALHOST + ENDPOINT,
        json={"password": password},
        headers=auth_headers(access_token),
    )
    assert_ok(answer, 204)

    # Проверка, что пароль из тела DELETE не попал в лог.
    assert password not in read_server_log()

    # Проверка, что все токены удалённого аккаунта отозваны.
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"requested_data": "nickname"},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "invalid-token", "Missing or invalid token")
    answer = requests.post(
        LOCALHOST + "/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert_error(answer, "invalid-token", "Missing or invalid token")

    # Проверка, что в удалённый аккаунт нельзя войти.
    answer = requests.post(
        LOCALHOST + "/auth/login", json={"username": username, "password": password}
    )
    assert_error(answer, "invalid-credentials", "Incorrect login or password")

    # Проверка, что username и email удалённого аккаунта остаются занятыми.
    for new_username, new_email, detail in (
        (username, "new@test.test", f"User with username {username} already exists"),
        ("new", email, f"User with email {email} already exists"),
    ):
        answer = requests.post(
            LOCALHOST + "/users",
            json={
                "username": new_username,
                "nickname": "nickname",
                "email": new_email,
                "password": password,
            },
        )
        assert_error(answer, "conflict", detail)

    # Проверка, что статья осталась, но данных автора в ней нет.
    article = requests.get(f"{LOCALHOST}/articles/{article_id}").json()["article"]
    assert article["author_preview"] == {"is_deleted": True}
    page = requests.get(LOCALHOST + "/articles", params={"indexes": 0}).json()["pages"]
    assert page["0"][0]["author_preview"] == {"is_deleted": True}

    # Проверка, что подписка на удалённый аккаунт снята и оформить её нельзя.
    assert read_field(ENDPOINT, "sub_users", follower_token) == []
    answer = requests.patch(
        LOCALHOST + ENDPOINT,
        json={"sub-users": [username]},
        headers=auth_headers(follower_token),
    )
    assert_error(
        answer, "validation", "Cannot find user with username: tester_username_0"
    )

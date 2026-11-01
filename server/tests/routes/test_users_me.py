"""
Этот файл служит для хранения тестов на API-методы пути /users/me: чтение (GET)
и изменение (PATCH) данных пользователя.
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
    assert_error(answer, "invalid-token")


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
    assert answer.json()["name_history"] == [nickname, user_name]
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
        assert_error(answer, "forbidden")
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
        assert_error(answer, "validation")
    assert read_field(ENDPOINT, "avatar", access_token) == avatar

    # Проверка, что нельзя занять чужой email, а свой указать повторно можно.
    other_email = "other@email.email"
    _, _, _, other_user_email, _, _ = add_user()
    answer = requests.patch(
        LOCALHOST + ENDPOINT, json={"email": other_user_email}, headers=headers
    )
    assert_error(answer, "conflict")
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
    assert_error(answer, "invalid-token")

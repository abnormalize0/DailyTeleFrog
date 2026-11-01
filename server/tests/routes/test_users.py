"""
Этот файл служит для хранения теста на API-метод POST /users.
"""

import requests

from tests.helpers import (
    LOCALHOST,
    assert_error,
    assert_ok,
    auth_headers,
    check_endpoint_structure,
)


def test_users_post() -> None:
    endpoint = "/users"
    check_endpoint_structure(endpoint, "post")

    username = "test_name_1"
    nickname = "test_name_1"
    email = "test@,test.test"
    password = "password"
    avatar = "avatar"

    # happy path
    answer = requests.post(
        LOCALHOST + endpoint,
        json={
            "username": username,
            "nickname": nickname,
            "email": email,
            "password": password,
            "avatar": avatar,
        },
    )
    assert_ok(answer, 201)
    assert answer.json()["username"] == username

    login_answer = requests.post(
        LOCALHOST + "/auth/login",
        json={"username": username, "password": password},
    )
    assert_ok(login_answer)
    access_token = login_answer.json()["access_token"]

    requested_data = [
        "nickname",
        "email",
        "name_history",
        "avatar",
        "creation_date",
        "rating",
    ]
    answer = requests.get(
        LOCALHOST + "/users/me",
        params={"requested_data": requested_data},
        headers=auth_headers(access_token),
    )
    assert_ok(answer)
    assert nickname == answer.json()["nickname"]
    assert email == answer.json()["email"]
    assert [nickname] == answer.json()["name_history"]
    assert avatar == answer.json()["avatar"]
    assert 0 == answer.json()["rating"]
    assert "creation_date" in answer.json()

    # Проверка, что значения предельной длины реально сохраняются: лимиты API
    # совпадают с колонками, а длина String(n) считается в символах, а не в байтах.
    long_nickname = "я" * 32
    answer = requests.post(
        LOCALHOST + endpoint,
        json={
            "username": "u" * 32,
            "nickname": long_nickname,
            "email": "e" * 255,
            "password": password,
            "avatar": "a" * 512,
            "description": "о" * 32767,
        },
    )
    assert_ok(answer, 201)

    # Проверка, что описание считается в байтах: 32768 кириллических символов
    # занимают 65536 байт и в TEXT не помещаются.
    answer = requests.post(
        LOCALHOST + endpoint,
        json={
            "username": "too_long_description",
            "nickname": "n",
            "email": "too_long@test.test",
            "password": password,
            "description": "о" * 32768,
        },
    )
    assert_error(answer, "validation")
    assert answer.json()["errors"][0]["name"] == "description"

    # username is a primary key: same username with a different email must be rejected
    answer = requests.post(
        LOCALHOST + endpoint,
        json={
            "username": username,
            "nickname": "other_nickname",
            "email": "other_email@test.test",
            "password": password,
        },
    )
    assert_error(answer, "conflict")

    # email is unique: different username with the same email must be rejected
    answer = requests.post(
        LOCALHOST + endpoint,
        json={
            "username": "other_username",
            "nickname": "other_nickname",
            "email": email,
            "password": password,
        },
    )
    assert_error(answer, "conflict")

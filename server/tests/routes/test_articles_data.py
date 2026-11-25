"""
Этот файл служит для хранения теста на API-метод GET /articles/{id}/data.
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


def test_articles_data_get(add_user: Callable, add_article: Callable) -> None:
    _, _, _, _, access_token, _ = add_user()
    article_id = add_article(access_token)
    endpoint = f"/articles/{article_id}/data"
    check_endpoint_structure(endpoint, "get")
    request_data = [
        "likes",
        "dislikes",
        "rating",
        "comments_count",
        "creation_date",
        "tags",
        "is_liked",
        "is_disliked",
    ]
    answer = requests.get(
        LOCALHOST + endpoint,
        params={"requested_data": request_data},
        headers=auth_headers(access_token),
    )
    assert_ok(answer)
    data = answer.json()
    for field in request_data:
        assert field in data
    assert sorted(data["tags"]) == ["tag1", "tag2"]

    # Проверка, что OPTIONS /articles/{id}/data включает "tags" в допустимые поля.
    options_answer = requests.options(LOCALHOST + endpoint)
    assert_ok(options_answer)
    requested_data_schema = options_answer.json()["get"][0]
    assert {"name": "tags"} in requested_data_schema["structure"]

    # Проверка, что одиночный запрос requested_data=tags возвращает только поле tags.
    answer = requests.get(
        LOCALHOST + endpoint,
        params={"requested_data": "tags"},
        headers=auth_headers(access_token),
    )
    assert_ok(answer)
    body = answer.json()
    assert set(body) == {"tags"}
    assert sorted(body["tags"]) == ["tag1", "tag2"]

    # test unlogged users (запрос без заголовка Authorization)
    answer = requests.get(LOCALHOST + endpoint, params={"requested_data": request_data})
    assert_ok(answer)
    data = answer.json()
    for field in request_data:
        assert field in data

    # Проверка, что неверный токен не превращает запрос в анонимный.
    answer = requests.get(
        LOCALHOST + endpoint,
        params={"requested_data": request_data},
        headers=auth_headers("bogus_token"),
    )
    assert_error(answer, "invalid-token", "Missing or invalid token")

    # trying to read a non-existent article
    answer = requests.get(
        f"{LOCALHOST}/articles/{article_id + 1}/data",
        params={"requested_data": request_data},
    )
    assert_error(answer, "not-found", "Cannot find article with id: 2")

    # Проверка, что 404 не зависит от набора полей: is_liked сам по себе не
    # проверяет существование статьи.
    answer = requests.get(
        f"{LOCALHOST}/articles/{article_id + 1}/data",
        params={"requested_data": "is_liked"},
    )
    assert_error(answer, "not-found", "Cannot find article with id: 2")

    # Проверка, что для статьи без тегов возвращается пустой список.
    article_id_no_tags = add_article(access_token, tags=[])
    answer = requests.get(
        f"{LOCALHOST}/articles/{article_id_no_tags}/data",
        params={"requested_data": "tags"},
    )
    assert_ok(answer)
    assert answer.json() == {"tags": []}

"""
Этот файл служит для хранения теста на API-метод POST /articles/{id}/comments.
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


def test_articles_comments_post(add_user: Callable, add_article: Callable) -> None:
    _, _, _, _, access_token, _ = add_user()
    article_id = add_article(access_token)
    endpoint = f"/articles/{article_id}/comments"
    check_endpoint_structure(endpoint, "post")

    # Проверка, что без токена нельзя оставить комментарий.
    answer = requests.post(LOCALHOST + endpoint, json={"text": "text", "root": -1})
    assert_error(answer, "invalid-token")

    # Публикуем комментарий к статье.
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"text": "text", "root": -1},
        headers=auth_headers(access_token),
    )
    assert_ok(answer, 201)
    comment_id = answer.json()["id"]
    assert answer.headers["Location"] == f"/comments/{comment_id}"

    # Публикуем ответ на комментарий.
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"text": "text", "root": comment_id},
        headers=auth_headers(access_token),
    )
    assert_ok(answer, 201)
    assert "id" in answer.json(), answer.json()

    # Проверка, что оба комментария появились в статье и ответ вложен в родителя.
    article = requests.get(f"{LOCALHOST}/articles/{article_id}").json()["article"]
    assert article["comments_count"] == 2
    assert len(article["comments"][0]["answers"]) == 1

    # Проверка, что комментарий предельной длины сохраняется, а длиннее — нет.
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"text": "ю" * 32767, "root": -1},
        headers=auth_headers(access_token),
    )
    assert_ok(answer, 201)
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"text": "ю" * 32768, "root": -1},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "validation")

    # Попытка ответить на несуществующий комментарий.
    answer = requests.post(
        LOCALHOST + endpoint,
        json={"text": "text", "root": comment_id + 1000},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "validation")

    # Проверка, что к несуществующей статье комментарий не оставить.
    answer = requests.post(
        f"{LOCALHOST}/articles/{article_id + 1}/comments",
        json={"text": "text", "root": -1},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "not-found")

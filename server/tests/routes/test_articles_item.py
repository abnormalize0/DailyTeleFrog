"""
Этот файл служит для хранения теста на API-метод GET /articles/{id}.
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


def test_articles_item_get(add_user: Callable, add_article: Callable) -> None:
    _, _, _, _, access_token, _ = add_user()
    author, _, _, _, author_token, _ = add_user()
    article_id = add_article(author_token)
    endpoint = f"/articles/{article_id}"
    check_endpoint_structure(endpoint, "get")

    # happy path
    answer = requests.get(LOCALHOST + endpoint, headers=auth_headers(access_token))
    assert_ok(answer)
    assert answer.headers["Content-Type"] == "application/json"
    article = answer.json()["article"]
    assert "body" in article.keys()
    assert "preview" in article.keys()
    assert "author_preview" in article.keys()
    assert article["author_preview"]["username"] == author
    assert "likes" in article.keys()
    assert "dislikes" in article.keys()
    assert "is_liked" in article.keys()
    assert "is_disliked" in article.keys()
    assert "comments_count" in article.keys()
    assert "tags" in article.keys()
    assert "creation_date" in article.keys()

    # Проверка, что тело успешного ответа не содержит служебного статуса.
    assert "status" not in answer.json()

    # test unlogged users (запрос без заголовка Authorization)
    assert_ok(requests.get(LOCALHOST + endpoint))

    # Проверка, что неверный токен не превращает запрос в анонимный.
    answer = requests.get(LOCALHOST + endpoint, headers=auth_headers("bogus_token"))
    assert_error(answer, "invalid-token")

    # trying to read a non-existent article
    answer = requests.get(
        f"{LOCALHOST}/articles/{article_id + 1}", headers=auth_headers(access_token)
    )
    assert_error(answer, "not-found")

    # Проверка, что ошибки самого Flask тоже отдаются в формате Problem Details.
    answer = requests.get(f"{LOCALHOST}/articles/not_a_number")
    assert answer.status_code == 404
    assert answer.headers["Content-Type"] == "application/problem+json"
    assert answer.json()["type"] == "about:blank"

    answer = requests.delete(LOCALHOST + endpoint)
    assert answer.status_code == 405
    assert answer.headers["Content-Type"] == "application/problem+json"
    assert "GET" in answer.headers["Allow"]

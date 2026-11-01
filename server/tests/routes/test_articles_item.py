"""
Этот файл служит для хранения тестов на API-методы пути /articles/{id}: GET и DELETE.
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
    assert_error(answer, "invalid-token", "Missing or invalid token")

    # trying to read a non-existent article
    answer = requests.get(
        f"{LOCALHOST}/articles/{article_id + 1}", headers=auth_headers(access_token)
    )
    assert_error(answer, "not-found", "Cannot find article with id: 2")

    # Проверка, что ошибки самого Flask тоже отдаются в формате Problem Details.
    answer = requests.get(f"{LOCALHOST}/articles/not_a_number")
    assert answer.status_code == 404
    assert answer.headers["Content-Type"] == "application/problem+json"
    assert answer.json()["type"] == "about:blank"

    answer = requests.patch(LOCALHOST + endpoint)
    assert answer.status_code == 405
    assert answer.headers["Content-Type"] == "application/problem+json"
    assert "GET" in answer.headers["Allow"]


def test_articles_item_delete(
    add_user: Callable,
    add_article: Callable,
    add_comment: Callable,
    like_article: Callable,
) -> None:
    _, _, _, _, author_token, _ = add_user()
    _, _, _, _, other_token, _ = add_user()
    article_id = add_article(author_token)
    kept_article_id = add_article(author_token)
    comment_id = add_comment(other_token, article_id)
    like_article(article_id, other_token)
    endpoint = f"/articles/{article_id}"
    check_endpoint_structure(endpoint, "delete")
    assert_preflight_allows(endpoint, "DELETE")

    # Проверка, что без токена статью не удалить.
    assert_error(
        requests.delete(LOCALHOST + endpoint),
        "invalid-token",
        "Missing or invalid token",
    )

    # Проверка, что удалить статью может только автор.
    answer = requests.delete(LOCALHOST + endpoint, headers=auth_headers(other_token))
    assert_error(answer, "forbidden", "User cannot delete someone else's article")
    assert_ok(requests.get(LOCALHOST + endpoint))

    # Проверка, что несуществующую статью не удалить.
    answer = requests.delete(
        f"{LOCALHOST}/articles/{kept_article_id + 1}",
        headers=auth_headers(author_token),
    )
    assert_error(answer, "not-found", "Cannot find article with id: 3")

    # happy path
    assert read_field("/users/me", "rating", author_token) == 1
    answer = requests.delete(LOCALHOST + endpoint, headers=auth_headers(author_token))
    assert_ok(answer, 204)

    # Проверка, что к удалённой статье нельзя обратиться ни одним методом.
    assert_error(
        requests.get(LOCALHOST + endpoint),
        "not-found",
        "Cannot find article with id: 1",
    )
    answer = requests.get(
        f"{LOCALHOST}{endpoint}/data", params={"requested_data": "likes"}
    )
    assert_error(answer, "not-found", "Cannot find article with id: 1")
    answer = requests.put(
        f"{LOCALHOST}{endpoint}/like", headers=auth_headers(other_token)
    )
    assert_error(answer, "not-found", "Cannot find article with id: 1")
    answer = requests.post(
        f"{LOCALHOST}{endpoint}/comments",
        json={"text": "text", "parent": -1},
        headers=auth_headers(other_token),
    )
    assert_error(answer, "not-found", "Cannot find article with id: 1")

    # Проверка, что вместе со статьёй скрыты и её комментарии.
    answer = requests.get(
        f"{LOCALHOST}/comments/{comment_id}", params={"requested_data": "likes"}
    )
    assert_error(answer, "not-found", "Cannot find comment with id: 1")

    # Проверка, что комментарий удалённой статьи не удалить отдельно.
    answer = requests.delete(
        f"{LOCALHOST}/comments/{comment_id}", headers=auth_headers(other_token)
    )
    assert_error(answer, "not-found", "Cannot find comment with id: 1")

    # Проверка, что статьи нет в ленте, а другая статья автора осталась.
    page = requests.get(LOCALHOST + "/articles", params={"indexes": 0}).json()["pages"]
    assert [article["id"] for article in page["0"]] == [kept_article_id]

    # Проверка, что реакции на удалённую статью не входят в рейтинг автора.
    assert read_field("/users/me", "rating", author_token) == 0

    # Проверка, что посторонний не узнает о существовании удалённой статьи.
    answer = requests.delete(LOCALHOST + endpoint, headers=auth_headers(other_token))
    assert_error(answer, "not-found", "Cannot find article with id: 1")

    # Проверка идемпотентности для автора.
    answer = requests.delete(LOCALHOST + endpoint, headers=auth_headers(author_token))
    assert_ok(answer, 204)

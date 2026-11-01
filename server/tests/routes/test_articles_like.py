"""
Этот файл служит для хранения тестов на API-методы пути /articles/{id}/like: постановка
(PUT) и снятие (DELETE) лайка статьи.
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


def test_articles_like_put(add_user: Callable, add_article: Callable) -> None:
    method = "put"
    _, _, _, _, access_token, _ = add_user()
    _, _, _, _, access_token_2, _ = add_user()
    article_id = add_article(access_token)
    endpoint = f"/articles/{article_id}/like"
    check_endpoint_structure(endpoint, method)
    assert_preflight_allows(endpoint, "PUT")
    assert_preflight_allows(endpoint, "DELETE")

    # Проверка, что без токена нельзя поставить лайк.
    assert_error(
        requests.put(LOCALHOST + endpoint), "invalid-token", "Missing or invalid token"
    )

    # Проверка, что нельзя поставить лайк на свою статью.
    assert_error(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token)),
        "forbidden",
        "User cannot like or dislike their own article",
    )

    # Проверка, что на несуществующий объект лайк не поставить.
    assert_error(
        requests.put(
            f"{LOCALHOST}/articles/{article_id + 1000}/like",
            headers=auth_headers(access_token_2),
        ),
        "not-found",
        "Cannot find article with id: 1001",
    )

    # Проверка, что лайк применился.
    assert_ok(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token_2)), 204
    )
    assert read_field(f"/articles/{article_id}/data", "likes") == 1

    # Проверка, что лайк изменяет рейтинг автора.
    assert read_field("/users/me", "rating", access_token) == 1

    # Проверка идемпотентности: повторный PUT не отменяет лайк и не дублирует его.
    assert_ok(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token_2)), 204
    )
    assert read_field(f"/articles/{article_id}/data", "likes") == 1

    # Проверка, что лайк перезаписывает дизлайк.
    assert_ok(
        requests.put(
            f"{LOCALHOST}/articles/{article_id}/dislike",
            headers=auth_headers(access_token_2),
        ),
        204,
    )
    assert_ok(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token_2)), 204
    )
    assert read_field(f"/articles/{article_id}/data", "likes") == 1
    assert read_field(f"/articles/{article_id}/data", "dislikes") == 0

    # Проверка, что лайк на одной статье не задевает другую.
    other_article_id = add_article(access_token)
    assert_ok(
        requests.put(
            f"{LOCALHOST}/articles/{other_article_id}/like",
            headers=auth_headers(access_token_2),
        ),
        204,
    )
    assert read_field(f"/articles/{article_id}/data", "likes") == 1
    assert read_field(f"/articles/{other_article_id}/data", "likes") == 1


def test_articles_like_delete(add_user: Callable, add_article: Callable) -> None:
    method = "delete"
    _, _, _, _, access_token, _ = add_user()
    _, _, _, _, access_token_2, _ = add_user()
    article_id = add_article(access_token)
    endpoint = f"/articles/{article_id}/like"
    check_endpoint_structure(endpoint, method)

    # Проверка, что без токена нельзя снять лайк.
    assert_error(
        requests.delete(LOCALHOST + endpoint),
        "invalid-token",
        "Missing or invalid token",
    )

    # Проверка, что с несуществующего объекта лайк не снять.
    assert_error(
        requests.delete(
            f"{LOCALHOST}/articles/{article_id + 1000}/like",
            headers=auth_headers(access_token_2),
        ),
        "not-found",
        "Cannot find article with id: 1001",
    )

    # Проверка, что снятие отсутствующего лайка не является ошибкой.
    assert_ok(
        requests.delete(LOCALHOST + endpoint, headers=auth_headers(access_token_2)),
        204,
    )

    # Проверка, что лайк снимается и рейтинг автора возвращается к нулю.
    assert_ok(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token_2)), 204
    )
    assert_ok(
        requests.delete(LOCALHOST + endpoint, headers=auth_headers(access_token_2)),
        204,
    )
    assert read_field(f"/articles/{article_id}/data", "likes") == 0
    assert read_field("/users/me", "rating", access_token) == 0

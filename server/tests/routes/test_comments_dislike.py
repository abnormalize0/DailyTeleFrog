"""
Этот файл служит для хранения тестов на API-методы пути /comments/{id}/dislike: постановка
(PUT) и снятие (DELETE) дизлайка комментария.
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


def test_comments_dislike_put(
    add_user: Callable, add_article: Callable, add_comment: Callable
) -> None:
    method = "put"
    _, _, _, _, access_token, _ = add_user()
    _, _, _, _, access_token_2, _ = add_user()
    article_id = add_article(access_token)
    comment_id = add_comment(access_token, article_id)
    endpoint = f"/comments/{comment_id}/dislike"
    check_endpoint_structure(endpoint, method)
    assert_preflight_allows(endpoint, "PUT")
    assert_preflight_allows(endpoint, "DELETE")

    # Проверка, что без токена нельзя поставить дизлайк.
    assert_error(
        requests.put(LOCALHOST + endpoint), "invalid-token", "Missing or invalid token"
    )

    # Проверка, что нельзя поставить дизлайк на свой комментарий.
    assert_error(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token)),
        "forbidden",
        "User cannot like or dislike their own comment",
    )

    # Проверка, что на несуществующий объект дизлайк не поставить.
    assert_error(
        requests.put(
            f"{LOCALHOST}/comments/{comment_id + 1000}/dislike",
            headers=auth_headers(access_token_2),
        ),
        "not-found",
        "Cannot find comment with id: 1001",
    )

    # Проверка, что дизлайк применился.
    assert_ok(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token_2)), 204
    )
    assert read_field(f"/comments/{comment_id}", "dislikes") == 1

    # Проверка, что дизлайк изменяет рейтинг автора.
    assert read_field("/users/me", "rating", access_token) == -1

    # Проверка идемпотентности: повторный PUT не отменяет дизлайк и не дублирует его.
    assert_ok(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token_2)), 204
    )
    assert read_field(f"/comments/{comment_id}", "dislikes") == 1

    # Проверка, что дизлайк перезаписывает лайк.
    assert_ok(
        requests.put(
            f"{LOCALHOST}/comments/{comment_id}/like",
            headers=auth_headers(access_token_2),
        ),
        204,
    )
    assert_ok(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token_2)), 204
    )
    assert read_field(f"/comments/{comment_id}", "dislikes") == 1
    assert read_field(f"/comments/{comment_id}", "likes") == 0


def test_comments_dislike_delete(
    add_user: Callable, add_article: Callable, add_comment: Callable
) -> None:
    method = "delete"
    _, _, _, _, access_token, _ = add_user()
    _, _, _, _, access_token_2, _ = add_user()
    article_id = add_article(access_token)
    comment_id = add_comment(access_token, article_id)
    endpoint = f"/comments/{comment_id}/dislike"
    check_endpoint_structure(endpoint, method)

    # Проверка, что без токена нельзя снять дизлайк.
    assert_error(
        requests.delete(LOCALHOST + endpoint),
        "invalid-token",
        "Missing or invalid token",
    )

    # Проверка, что с несуществующего объекта дизлайк не снять.
    assert_error(
        requests.delete(
            f"{LOCALHOST}/comments/{comment_id + 1000}/dislike",
            headers=auth_headers(access_token_2),
        ),
        "not-found",
        "Cannot find comment with id: 1001",
    )

    # Проверка, что снятие отсутствующего дизлайка не является ошибкой.
    assert_ok(
        requests.delete(LOCALHOST + endpoint, headers=auth_headers(access_token_2)),
        204,
    )

    # Проверка, что дизлайк снимается и рейтинг автора возвращается к нулю.
    assert_ok(
        requests.put(LOCALHOST + endpoint, headers=auth_headers(access_token_2)), 204
    )
    assert_ok(
        requests.delete(LOCALHOST + endpoint, headers=auth_headers(access_token_2)),
        204,
    )
    assert read_field(f"/comments/{comment_id}", "dislikes") == 0
    assert read_field("/users/me", "rating", access_token) == 0

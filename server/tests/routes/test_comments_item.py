"""
Этот файл служит для хранения тестов на API-методы пути /comments/{id}: GET и DELETE.
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
)


def test_comments_item_get(
    add_user: Callable, add_article: Callable, add_comment: Callable
) -> None:
    add_user()
    _, _, _, _, access_token, _ = add_user()
    article_id = add_article(access_token)
    request_data = [
        "likes",
        "dislikes",
        "rating",
        "creation_date",
        "is_liked",
        "is_disliked",
    ]

    comment_id = add_comment(access_token, article_id)
    endpoint = f"/comments/{comment_id}"
    check_endpoint_structure(endpoint, "get")

    answer = requests.get(
        LOCALHOST + endpoint,
        params={"requested_data": request_data},
        headers=auth_headers(access_token),
    )
    assert_ok(answer)
    data = answer.json()
    for field in request_data:
        assert field in data

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

    # trying to read a non-existent comment
    answer = requests.get(
        f"{LOCALHOST}/comments/{comment_id + 1}",
        params={"requested_data": request_data},
    )
    assert_error(answer, "not-found", "Cannot find comment with id: 2")

    # Проверка, что 404 не зависит от набора полей: is_liked сам по себе не
    # проверяет существование комментария.
    answer = requests.get(
        f"{LOCALHOST}/comments/{comment_id + 1}",
        params={"requested_data": "is_liked"},
    )
    assert_error(answer, "not-found", "Cannot find comment with id: 2")


def test_comments_item_delete(
    add_user: Callable, add_article: Callable, add_comment: Callable
) -> None:
    _, _, _, _, author_token, _ = add_user()
    _, _, _, _, other_token, _ = add_user()
    article_id = add_article(author_token)
    comment_id = add_comment(author_token, article_id)
    answer = requests.post(
        f"{LOCALHOST}/articles/{article_id}/comments",
        json={"text": "reply", "parent": comment_id},
        headers=auth_headers(other_token),
    )
    assert_ok(answer, 201)
    reply_id = answer.json()["id"]
    endpoint = f"/comments/{comment_id}"
    check_endpoint_structure(endpoint, "delete")
    assert_preflight_allows(endpoint, "DELETE")

    # Проверка, что без токена комментарий не удалить.
    assert_error(
        requests.delete(LOCALHOST + endpoint),
        "invalid-token",
        "Missing or invalid token",
    )

    # Проверка, что удалить комментарий может только автор.
    answer = requests.delete(LOCALHOST + endpoint, headers=auth_headers(other_token))
    assert_error(answer, "forbidden", "User cannot delete someone else's comment")

    # Проверка, что несуществующий комментарий не удалить.
    answer = requests.delete(
        f"{LOCALHOST}/comments/{reply_id + 1}", headers=auth_headers(author_token)
    )
    assert_error(answer, "not-found", "Cannot find comment with id: 3")

    # happy path
    answer = requests.delete(LOCALHOST + endpoint, headers=auth_headers(author_token))
    assert_ok(answer, 204)

    # Проверка, что в дереве осталась заглушка без автора и текста, а ответ на месте.
    article = requests.get(f"{LOCALHOST}/articles/{article_id}").json()["article"]
    stub = article["comments"][0]
    assert sorted(stub) == ["answers", "id", "is_deleted", "parent_id"]
    assert stub["is_deleted"] is True
    assert stub["answers"][0]["id"] == reply_id
    assert stub["answers"][0]["parent_id"] == comment_id
    assert stub["answers"][0]["text"] == "reply"
    assert stub["answers"][0]["is_deleted"] is False

    # Проверка, что заглушка не входит в число комментариев статьи.
    assert article["comments_count"] == 1

    # Проверка, что по id отдаётся только статус удалённого комментария.
    answer = requests.get(
        LOCALHOST + endpoint, params={"requested_data": ["likes", "creation_date"]}
    )
    assert_ok(answer)
    assert answer.json() == {"is_deleted": True}

    # Проверка, что на удалённый комментарий нельзя отреагировать и ответить.
    answer = requests.put(
        f"{LOCALHOST}{endpoint}/like", headers=auth_headers(other_token)
    )
    assert_error(answer, "not-found", "Cannot find comment with id: 1")
    answer = requests.post(
        f"{LOCALHOST}/articles/{article_id}/comments",
        json={"text": "text", "parent": comment_id},
        headers=auth_headers(other_token),
    )
    assert_error(answer, "validation", "Cannot find comment with id: 1")

    # Проверка идемпотентности.
    answer = requests.delete(LOCALHOST + endpoint, headers=auth_headers(author_token))
    assert_ok(answer, 204)

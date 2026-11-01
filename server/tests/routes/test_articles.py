"""
Этот файл служит для хранения тестов на API-методы пути /articles: публикация
статьи (POST) и лента статей (GET).
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

ENDPOINT = "/articles"


def _page_ids(answer: requests.Response, index: str = "0") -> list:
    """Достаёт id статей страницы из успешного ответа ленты.

    Args:
        answer: ответ GET /articles.
        index: номер страницы.

    Returns:
        Список id статей в порядке выдачи.
    """
    assert_ok(answer)
    return [article["id"] for article in answer.json()["pages"][index]]


def test_articles_post(add_user: Callable, add_article: Callable) -> None:
    check_endpoint_structure(ENDPOINT, "post")

    _, _, _, _, access_token, _ = add_user()
    article = {
        "title": "test_name",
        "preview": {"type": "image", "data": "ref"},
        "tags": ["tag1", "tag2", "tag3"],
        "body": {"block1": "text"},
    }

    # happy path
    answer = requests.post(
        LOCALHOST + ENDPOINT, json=article, headers=auth_headers(access_token)
    )
    assert_ok(answer, 201)
    article_id = answer.json()["article_id"]
    assert answer.headers["Location"] == f"/articles/{article_id}"

    # Проверка, что статья действительно доступна по адресу из Location.
    assert_ok(requests.get(LOCALHOST + answer.headers["Location"]))

    # Проверка, что значения предельной длины реально сохраняются: статья длиннее
    # предела TEXT (65 535 байт) помещается в MEDIUMTEXT.
    long_article = {
        "title": "t" * 512,
        "preview": {"data": "p" * 65000},
        "tags": ["т" * 512],
        "body": {"data": "б" * 100000},
    }
    answer = requests.post(
        LOCALHOST + ENDPOINT, json=long_article, headers=auth_headers(access_token)
    )
    assert_ok(answer, 201)

    # Проверка, что предел считается в байтах хранимого вида, а не в символах:
    # 33000 кириллических символов занимают 66000 байт и в TEXT не помещаются.
    answer = requests.post(
        LOCALHOST + ENDPOINT,
        json={**long_article, "preview": {"data": "п" * 33000}},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "validation")
    assert answer.json()["errors"][0]["name"] == "preview"

    # Проверка, что нельзя выставить статье одинаковые теги, в том числе отличающиеся
    # только регистром, и что статья при этом не создаётся.
    articles_before = len(
        requests.get(LOCALHOST + ENDPOINT, params={"indexes": 0}).json()["pages"]["0"]
    )
    for tags in (["tag1", "tag1"], ["Tag1", "tag1"]):
        answer = requests.post(
            LOCALHOST + ENDPOINT,
            json={**article, "tags": tags},
            headers=auth_headers(access_token),
        )
        assert_error(answer, "validation")
        assert answer.json()["errors"][0]["name"] == "tags"
    articles_after = len(
        requests.get(LOCALHOST + ENDPOINT, params={"indexes": 0}).json()["pages"]["0"]
    )
    assert articles_after == articles_before

    # Проверка, что тег обязан быть строкой.
    answer = requests.post(
        LOCALHOST + ENDPOINT,
        json={**article, "tags": [1]},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "validation")

    # Проверка, что статья с пустым списком тегов публикуется без тегов.
    article_id = add_article(access_token, tags=[])
    assert (
        requests.get(f"{LOCALHOST}/articles/{article_id}").json()["article"]["tags"]
        == []
    )

    # Проверка, что без токена статью не опубликовать.
    assert_error(requests.post(LOCALHOST + ENDPOINT, json=article), "invalid-token")

    # Проверка, что тело не в формате JSON даёт 400, а не 500.
    answer = requests.post(
        LOCALHOST + ENDPOINT,
        data="{not json",
        headers={**auth_headers(access_token), "Content-Type": "application/json"},
    )
    assert_error(answer, "validation")


def test_articles_get(
    add_user: Callable, add_article: Callable, like_article: Callable
) -> None:
    check_endpoint_structure(ENDPOINT, "get")

    username, _, _, _, access_token, _ = add_user()
    username2, _, _, _, access_token2, _ = add_user()
    _, _, _, _, liker_token, _ = add_user()
    headers = auth_headers(access_token)

    article_1 = add_article(
        access_token, tags=["tag1", "tag2"], preview={"type": "text", "data": "text1"}
    )
    article_2 = add_article(
        access_token, tags=["tag2", "tag3"], preview={"type": "text", "data": "text2"}
    )
    like_article(article_2, access_token2)

    article_3 = add_article(
        access_token, tags=["tag1", "tag4"], preview={"type": "text", "data": "text3"}
    )
    like_article(article_3, access_token2)
    like_article(article_3, liker_token)

    # invalid sort_column / sort_direction values
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"indexes": 0, "sort_column": "bogus_column"},
        headers=headers,
    )
    assert_error(answer, "validation")

    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"indexes": 0, "sort_direction": "sideways"},
        headers=headers,
    )
    assert_error(answer, "validation")

    # Проверка, что неверный токен не превращает запрос в анонимный.
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"indexes": 0},
        headers=auth_headers("bogus_token"),
    )
    assert_error(answer, "invalid-token")

    # happy path: sort by rating, descending
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={
            "indexes": 0,
            "sort_column": "rating",
            "sort_direction": "descending",
        },
        headers=headers,
    )
    assert _page_ids(answer) == [article_3, article_2, article_1]
    page = answer.json()["pages"]["0"]
    for article in page:
        assert "preview_content" in article
        assert "tags" in article
        assert "creation_date" in article
        assert "author_preview" in article
        assert "likes" in article
        assert "dislikes" in article
        assert "rating" in article
        assert "comments_count" in article
        assert "is_liked" in article
        assert "is_disliked" in article
    assert page[0]["author_preview"]["username"] == username

    # sort by rating, ascending
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={
            "indexes": 0,
            "sort_column": "rating",
            "sort_direction": "ascending",
        },
        headers=headers,
    )
    assert _page_ids(answer) == [article_1, article_2, article_3]

    # sort by creation_date, descending (default)
    answer = requests.get(LOCALHOST + ENDPOINT, params={"indexes": 0}, headers=headers)
    assert _page_ids(answer) == [article_3, article_2, article_1]

    # sort by creation_date, ascending
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={
            "indexes": 0,
            "sort_column": "creation_date",
            "sort_direction": "ascending",
        },
        headers=headers,
    )
    assert _page_ids(answer) == [article_1, article_2, article_3]

    # include_tags: only articles having ALL requested tags
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"indexes": 0, "include_tags": ["tag1", "tag4"]},
        headers=headers,
    )
    assert _page_ids(answer) == [article_3]

    # exclude_tags
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={
            "indexes": 0,
            "sort_column": "creation_date",
            "sort_direction": "ascending",
            "exclude_tags": "tag4",
        },
        headers=headers,
    )
    assert _page_ids(answer) == [article_1, article_2]

    # include_authors / exclude_authors
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"indexes": 0, "include_authors": username2},
        headers=headers,
    )
    assert _page_ids(answer) == []

    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"indexes": 0, "exclude_authors": username},
        headers=headers,
    )
    assert _page_ids(answer) == []

    # bounds on rating
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={
            "indexes": 0,
            "sort_column": "rating",
            "sort_direction": "descending",
            "lower_rating": 0,
        },
        headers=headers,
    )
    assert _page_ids(answer) == [article_3, article_2]

    # blacklist: blocked authors are always excluded
    answer = requests.patch(
        LOCALHOST + "/users/me", json={"blocked-users": [username2]}, headers=headers
    )
    assert_ok(answer, 204)
    article_4 = add_article(
        access_token2, tags=["tag5"], preview={"type": "text", "data": "text4"}
    )
    answer = requests.get(LOCALHOST + ENDPOINT, params={"indexes": 0}, headers=headers)
    assert article_4 not in _page_ids(answer)

    # subscriptions: include_nonsub=false restricts to subscribed tags/authors
    answer = requests.patch(
        LOCALHOST + "/users/me", json={"sub-tags": ["tag4"]}, headers=headers
    )
    assert_ok(answer, 204)
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={"indexes": 0, "include_nonsub": "false"},
        headers=headers,
    )
    assert _page_ids(answer) == [article_3]

    # unlogged users can browse pages too (запрос без заголовка Authorization)
    answer = requests.get(LOCALHOST + ENDPOINT, params={"indexes": 0})
    assert article_4 in _page_ids(answer)

    # pagination across multiple indexes
    _, _, _, _, access_token3, _ = add_user()
    paginated_ids = []
    for i in range(7):
        paginated_ids.append(
            add_article(
                access_token3,
                tags=["pagination_tag"],
                preview={"type": "text", "data": f"page_text_{i}"},
            )
        )
    answer = requests.get(
        LOCALHOST + ENDPOINT,
        params={
            "indexes": [0, 1],
            "include_tags": "pagination_tag",
            "sort_column": "creation_date",
            "sort_direction": "ascending",
        },
    )
    assert _page_ids(answer, "0") == paginated_ids[:5]
    assert _page_ids(answer, "1") == paginated_ids[5:]

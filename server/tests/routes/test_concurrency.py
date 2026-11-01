"""
Этот файл служит для хранения e2e-тестов одновременных одинаковых запросов: так выглядят
двойной клик и повтор при сетевом сбое. Проверка «нашли, что строки нет, и вставили» не
защищает от них: результат гарантирует первичный или уникальный ключ БД, а взаимоисключающие
строки в разных таблицах защищает блокировка. Клиент при этом не должен получать 500
(см. decisions/0009-api-atomicity.md).
"""

import threading
from collections.abc import Callable

import pytest
import requests

from tests.helpers import LOCALHOST, assert_ok, auth_headers, read_field

PARALLEL_REQUESTS = 8
OPPOSITE_REACTION_ROUNDS = 5


def _send_together(
    send: Callable[[int], requests.Response], count: int = PARALLEL_REQUESTS
) -> list[int]:
    """Отправляет запросы одновременно: барьер отпускает все потоки разом.

    Args:
        send: функция (номер запроса) -> ответ сервера.
        count: сколько запросов отправить.

    Returns:
        Отсортированный список HTTP-кодов ответов.
    """
    barrier = threading.Barrier(count)
    codes = []

    def _worker(index: int) -> None:
        barrier.wait()
        codes.append(send(index).status_code)

    threads = [
        threading.Thread(target=_worker, args=(index,)) for index in range(count)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return sorted(codes)


def test_users_post_same_username() -> None:
    def _register(_: int) -> requests.Response:
        return requests.post(
            LOCALHOST + "/users",
            json={
                "username": "racer",
                "nickname": "racer",
                "password": "tester_password",
                "email": "racer@test.test",
            },
        )

    # Проверка, что регистрацию выигрывает один запрос, а остальные получают конфликт
    assert _send_together(_register) == [201] + [409] * (PARALLEL_REQUESTS - 1)


def test_users_me_patch_same_email(add_user: Callable, read_all_rows: Callable) -> None:
    tokens = [add_user()[4] for _ in range(PARALLEL_REQUESTS)]

    def _change_email(index: int) -> requests.Response:
        return requests.patch(
            LOCALHOST + "/users/me",
            json={"description": "racer", "email": "racer@test.test"},
            headers=auth_headers(tokens[index]),
        )

    # Проверка, что email достаётся одному пользователю, а остальные получают конфликт
    assert _send_together(_change_email) == [204] + [409] * (PARALLEL_REQUESTS - 1)

    # Проверка, что проигравшие запросы не сохранили и остальные поля
    descriptions = [row.description for row in read_all_rows()["users"]]
    assert descriptions.count("racer") == 1


def test_users_me_patch_same_subscription(add_user: Callable) -> None:
    access_token = add_user()[4]

    def _subscribe(_: int) -> requests.Response:
        return requests.patch(
            LOCALHOST + "/users/me",
            json={"sub-tags": ["tag"]},
            headers=auth_headers(access_token),
        )

    # Проверка, что повтор PATCH не считается ошибкой и подписка остаётся одна
    assert _send_together(_subscribe) == [204] * PARALLEL_REQUESTS
    answer = read_field("/users/me", "sub_tags", access_token)
    assert answer == ["tag"]


@pytest.mark.parametrize("resource", ["articles", "comments"])
@pytest.mark.parametrize(
    "reaction, opposite, counter",
    [("like", "dislike", "likes"), ("dislike", "like", "dislikes")],
)
def test_reaction_put_same_user(
    add_user: Callable,
    add_article: Callable,
    add_comment: Callable,
    resource: str,
    reaction: str,
    opposite: str,
    counter: str,
) -> None:
    author_token = add_user()[4]
    reader_token = add_user()[4]
    article_id = add_article(author_token)
    comment_id = add_comment(author_token, article_id)
    path = f"/{resource}/{article_id if resource == 'articles' else comment_id}"
    headers = auth_headers(reader_token)
    assert_ok(requests.put(f"{LOCALHOST}{path}/{opposite}", headers=headers), 204)

    def _react(_: int) -> requests.Response:
        return requests.put(f"{LOCALHOST}{path}/{reaction}", headers=headers)

    # Проверка, что PUT идемпотентен и при одновременных повторах
    assert _send_together(_react) == [204] * PARALLEL_REQUESTS
    data_path = f"{path}/data" if resource == "articles" else path
    assert read_field(data_path, counter) == 1
    other_counter = "dislikes" if counter == "likes" else "likes"
    assert read_field(data_path, other_counter) == 0


@pytest.mark.parametrize("resource", ["articles", "comments"])
def test_opposite_reactions_same_user(
    add_user: Callable,
    add_article: Callable,
    add_comment: Callable,
    resource: str,
) -> None:
    author_token = add_user()[4]
    reader_token = add_user()[4]
    article_id = add_article(author_token)
    comment_id = add_comment(author_token, article_id)
    path = f"/{resource}/{article_id if resource == 'articles' else comment_id}"

    headers = auth_headers(reader_token)
    data_path = f"{path}/data" if resource == "articles" else path

    def _react(index: int) -> requests.Response:
        reaction = "like" if index else "dislike"
        return requests.put(f"{LOCALHOST}{path}/{reaction}", headers=headers)

    # Проверка, что лайк и дизлайк одновременно оставляют одну реакцию. Запросов ровно
    # два и каждый раунд начинается без реакций: при большем числе запросов следующие
    # убирают лишнюю реакцию, и ошибка не видна в итоговом состоянии.
    for _ in range(OPPOSITE_REACTION_ROUNDS):
        assert_ok(requests.delete(f"{LOCALHOST}{path}/like", headers=headers), 204)
        assert_ok(requests.delete(f"{LOCALHOST}{path}/dislike", headers=headers), 204)
        assert _send_together(_react, count=2) == [204, 204]
        assert read_field(data_path, "likes") + read_field(data_path, "dislikes") == 1


def test_opposite_reactions_different_users(
    add_user: Callable, add_article: Callable
) -> None:
    article_id = add_article(add_user()[4])
    tokens = [add_user()[4] for _ in range(PARALLEL_REQUESTS)]

    def _react(index: int) -> requests.Response:
        reaction = "like" if index % 2 else "dislike"
        return requests.put(
            f"{LOCALHOST}/articles/{article_id}/{reaction}",
            headers=auth_headers(tokens[index]),
        )

    # Проверка, что очередь реакций не мешает разным пользователям и не даёт
    # взаимоблокировок на одной статье
    assert _send_together(_react) == [204] * PARALLEL_REQUESTS
    assert read_field(f"/articles/{article_id}/data", "likes") == PARALLEL_REQUESTS // 2
    assert (
        read_field(f"/articles/{article_id}/data", "dislikes") == PARALLEL_REQUESTS // 2
    )

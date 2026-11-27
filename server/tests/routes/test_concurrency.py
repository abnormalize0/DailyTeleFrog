"""
Этот файл служит для хранения e2e-тестов одновременных одинаковых запросов: так выглядят
двойной клик и повтор при сетевом сбое. Проверка «нашли, что строки нет, и вставили» не
защищает от них: результат гарантирует первичный или уникальный ключ БД, а взаимоисключающие
строки в разных таблицах защищает блокировка. Клиент при этом не должен получать 500
(см. decisions/0009-api-atomicity.md).
"""

import threading
import time
from collections.abc import Callable

import pytest
import requests
from sqlalchemy import Engine, text

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


def _delay_write(db_engine: Engine, operation: str, table: str, seconds: float) -> None:
    """Создаёт MySQL-триггер, замедляющий запись в таблицу на заданное число секунд.

    Args:
        db_engine: engine тестовой БД.
        operation: операция ("INSERT", "UPDATE" или "DELETE").
        table: имя таблицы.
        seconds: задержка в секундах.

    Returns:
        None
    """
    with db_engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE TRIGGER delay_{operation}_{table} "
                f"BEFORE {operation} ON {table} FOR EACH ROW "
                f"DO SLEEP({seconds})"
            )
        )


def _send_revocation(
    revocation: str, access_token: str, password: str
) -> requests.Response:
    """Отправляет один из запросов отзыва всех сессий пользователя.

    Args:
        revocation: вид отзыва ("delete_user", "change_password", "logout_all").
        access_token: действующий access token пользователя.
        password: текущий пароль пользователя.

    Returns:
        Ответ сервера на запрос отзыва.
    """
    headers = auth_headers(access_token)
    if revocation == "delete_user":
        return requests.delete(
            LOCALHOST + "/users/me", json={"password": password}, headers=headers
        )
    if revocation == "change_password":
        return requests.put(
            LOCALHOST + "/users/me/password",
            json={
                "previous_password": password,
                "new_password": "new_password_123",
            },
            headers=headers,
        )
    return requests.post(LOCALHOST + "/auth/logout-all", headers=headers)


def test_auth_refresh_same_token(
    add_user: Callable, db_engine: Engine, read_all_rows: Callable
) -> None:
    _, _, _, _, _, refresh_token = add_user()
    _delay_write(db_engine, "DELETE", "refresh_tokens", 0.2)

    def _refresh(_: int) -> requests.Response:
        return requests.post(
            LOCALHOST + "/auth/refresh", json={"refresh_token": refresh_token}
        )

    assert _send_together(_refresh) == [200] + [401] * (PARALLEL_REQUESTS - 1)
    tokens = read_all_rows()["refresh_tokens"]
    assert len(tokens) == 1
    assert tokens[0].token != refresh_token


@pytest.mark.parametrize("revocation", ["delete_user", "change_password", "logout_all"])
def test_auth_refresh_vs_revocation(
    add_user: Callable,
    db_engine: Engine,
    read_all_rows: Callable,
    revocation: str,
) -> None:
    _, password, _, _, access_token, refresh_token = add_user()
    _delay_write(db_engine, "INSERT", "access_tokens", 0.5)
    results: dict[str, requests.Response] = {}

    def _refresh() -> None:
        results["refresh"] = requests.post(
            LOCALHOST + "/auth/refresh", json={"refresh_token": refresh_token}
        )

    def _revoke() -> None:
        time.sleep(0.15)
        results["revoke"] = _send_revocation(revocation, access_token, password)

    refresh_thread = threading.Thread(target=_refresh)
    revoke_thread = threading.Thread(target=_revoke)
    refresh_thread.start()
    revoke_thread.start()
    refresh_thread.join()
    revoke_thread.join()

    assert results["revoke"].status_code == 204
    assert results["refresh"].status_code in (200, 401)
    rows = read_all_rows()
    assert rows["access_tokens"] == []
    assert rows["refresh_tokens"] == []


@pytest.mark.parametrize("login_by", ["username", "email"])
@pytest.mark.parametrize("revocation", ["delete_user", "change_password", "logout_all"])
def test_auth_login_vs_revocation(
    add_user: Callable,
    db_engine: Engine,
    read_all_rows: Callable,
    login_by: str,
    revocation: str,
) -> None:
    username, password, _, email, access_token, _ = add_user()
    _delay_write(db_engine, "INSERT", "access_tokens", 0.6)
    results: dict[str, requests.Response] = {}
    identifier = username if login_by == "username" else email

    def _login() -> None:
        results["login"] = requests.post(
            LOCALHOST + "/auth/login",
            json={login_by: identifier, "password": password},
        )

    def _revoke() -> None:
        time.sleep(0.35)
        results["revoke"] = _send_revocation(revocation, access_token, password)

    login_thread = threading.Thread(target=_login)
    revoke_thread = threading.Thread(target=_revoke)
    login_thread.start()
    revoke_thread.start()
    login_thread.join()
    revoke_thread.join()

    assert results["revoke"].status_code == 204
    assert results["login"].status_code in (200, 401)
    rows = read_all_rows()
    assert rows["access_tokens"] == []
    assert rows["refresh_tokens"] == []


def test_auth_operations_different_users(add_user: Callable) -> None:
    users = [add_user() for _ in range(PARALLEL_REQUESTS)]

    def _operate(index: int) -> requests.Response:
        username, password, _, _, access_token, refresh_token = users[index]
        op = index % 5
        if op == 0:
            return requests.post(
                LOCALHOST + "/auth/login",
                json={"username": username, "password": password},
            )
        if op == 1:
            return requests.post(
                LOCALHOST + "/auth/refresh",
                json={"refresh_token": refresh_token},
            )
        if op == 2:
            return _send_revocation("logout_all", access_token, password)
        if op == 3:
            return _send_revocation("change_password", access_token, password)
        return _send_revocation("delete_user", access_token, password)

    expected = sorted(200 if i % 5 in (0, 1) else 204 for i in range(PARALLEL_REQUESTS))
    assert _send_together(_operate) == expected


@pytest.mark.parametrize("revocation", ["delete_user", "change_password", "logout_all"])
def test_revocation_blocks_auth_refresh(
    add_user: Callable,
    db_engine: Engine,
    read_all_rows: Callable,
    revocation: str,
) -> None:
    _, password, _, _, access_token, refresh_token = add_user()
    _delay_write(db_engine, "DELETE", "refresh_tokens", 0.5)
    results: dict[str, requests.Response] = {}

    def _revoke() -> None:
        results["revoke"] = _send_revocation(revocation, access_token, password)

    def _refresh() -> None:
        time.sleep(0.15)
        results["refresh"] = requests.post(
            LOCALHOST + "/auth/refresh", json={"refresh_token": refresh_token}
        )

    revoke_thread = threading.Thread(target=_revoke)
    refresh_thread = threading.Thread(target=_refresh)
    revoke_thread.start()
    refresh_thread.start()
    revoke_thread.join()
    refresh_thread.join()

    assert results["revoke"].status_code == 204
    assert results["refresh"].status_code == 401
    rows = read_all_rows()
    assert rows["access_tokens"] == []
    assert rows["refresh_tokens"] == []


@pytest.mark.parametrize("login_by", ["username", "email"])
@pytest.mark.parametrize("revocation", ["delete_user", "change_password"])
def test_revocation_blocks_auth_login(
    add_user: Callable,
    db_engine: Engine,
    read_all_rows: Callable,
    login_by: str,
    revocation: str,
) -> None:
    username, password, _, email, access_token, _ = add_user()
    _delay_write(db_engine, "DELETE", "refresh_tokens", 0.5)
    results: dict[str, requests.Response] = {}
    identifier = username if login_by == "username" else email

    def _revoke() -> None:
        results["revoke"] = _send_revocation(revocation, access_token, password)

    def _login() -> None:
        time.sleep(0.15)
        results["login"] = requests.post(
            LOCALHOST + "/auth/login",
            json={login_by: identifier, "password": password},
        )

    revoke_thread = threading.Thread(target=_revoke)
    login_thread = threading.Thread(target=_login)
    revoke_thread.start()
    login_thread.start()
    revoke_thread.join()
    login_thread.join()

    assert results["revoke"].status_code == 204
    assert results["login"].status_code == 401
    rows = read_all_rows()
    assert rows["access_tokens"] == []
    assert rows["refresh_tokens"] == []


def test_auth_login_by_email_vs_change_email(
    add_user: Callable, db_engine: Engine
) -> None:
    _, password, _, email, access_token, _ = add_user()
    _delay_write(db_engine, "UPDATE", "users", 0.4)
    results: dict[str, requests.Response] = {}

    def _change_email() -> None:
        results["patch"] = requests.patch(
            LOCALHOST + "/users/me",
            json={"email": "new_email@test.test"},
            headers=auth_headers(access_token),
        )

    def _login() -> None:
        time.sleep(0.1)
        results["login"] = requests.post(
            LOCALHOST + "/auth/login",
            json={"email": email, "password": password},
        )

    patch_thread = threading.Thread(target=_change_email)
    login_thread = threading.Thread(target=_login)
    patch_thread.start()
    login_thread.start()
    patch_thread.join()
    login_thread.join()

    assert results["patch"].status_code == 204
    assert results["login"].status_code == 401


def test_logout_all_blocks_delete_user(
    add_user: Callable, db_engine: Engine, read_all_rows: Callable
) -> None:
    _, password, _, _, access_token, _ = add_user()
    _delay_write(db_engine, "DELETE", "refresh_tokens", 0.5)
    results: dict[str, requests.Response] = {}

    def _logout_all() -> None:
        results["logout_all"] = _send_revocation("logout_all", access_token, password)

    def _delete_user() -> None:
        time.sleep(0.15)
        results["delete"] = _send_revocation("delete_user", access_token, password)

    logout_thread = threading.Thread(target=_logout_all)
    delete_thread = threading.Thread(target=_delete_user)
    logout_thread.start()
    delete_thread.start()
    logout_thread.join()
    delete_thread.join()

    assert results["logout_all"].status_code == 204
    assert results["delete"].status_code == 401
    users = read_all_rows()["users"]
    assert len(users) == 1
    assert users[0].is_deleted is False


def test_delete_user_vs_sub_user_no_deadlock_and_no_stale_sub(
    add_user: Callable, db_engine: Engine, read_all_rows: Callable
) -> None:
    _, _, _, _, token_a, _ = add_user()
    username_b, password_b, _, _, token_b, _ = add_user()
    assert_ok(
        requests.patch(
            LOCALHOST + "/users/me",
            json={"blocked-users": [username_b]},
            headers=auth_headers(token_a),
        ),
        204,
    )
    _delay_write(db_engine, "DELETE", "refresh_tokens", 0.5)
    results: dict[str, requests.Response] = {}

    def _delete_b() -> None:
        results["delete"] = _send_revocation("delete_user", token_b, password_b)

    def _sub_b() -> None:
        time.sleep(0.15)
        results["sub"] = requests.patch(
            LOCALHOST + "/users/me",
            json={"sub-users": [username_b]},
            headers=auth_headers(token_a),
        )

    delete_thread = threading.Thread(target=_delete_b)
    sub_thread = threading.Thread(target=_sub_b)
    delete_thread.start()
    sub_thread.start()
    delete_thread.join()
    sub_thread.join()

    assert results["delete"].status_code == 204
    assert results["sub"].status_code == 422
    rows = read_all_rows()
    assert rows["user_subscriptions"] == []
    assert rows["user_blacklist"] == []

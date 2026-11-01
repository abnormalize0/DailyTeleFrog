"""
Этот файл служит для хранения e2e-тестов атомарности API-методов с несколькими
записями в БД: если запрос завершился ошибкой, ни одна строка ни одной таблицы не
меняется. Проверка общая для многих ресурсов, поэтому у неё отдельный файл. Правило и
способ проверки описаны в decisions/0009-api-atomicity.md.
"""

from collections.abc import Callable

import pytest
import requests

from tests.helpers import LOCALHOST, assert_error, assert_ok, auth_headers

ARTICLE_BODY = {
    "title": "title",
    "preview": {"type": "image", "data": "ref"},
    "tags": ["tag1", "tag2"],
    "body": {"block1": "text"},
}


def _assert_unexpected_error(answer: requests.Response) -> None:
    """Проверяет, что запрос дошёл до сбоя записи и вернул 500.

    Без этой проверки тест прошёл бы и тогда, когда метод отклонил запрос раньше и
    до записи вообще не дошёл.

    Args:
        answer: ответ сервера.

    Returns:
        None
    """
    assert_error(answer, "internal-error", "Unexpected error")


def _patch_me(access_token: str, body: dict) -> requests.Response:
    """Отправляет PATCH /users/me.

    Args:
        access_token: токен пользователя.
        body: тело запроса.

    Returns:
        Ответ сервера.
    """
    return requests.patch(
        LOCALHOST + "/users/me", json=body, headers=auth_headers(access_token)
    )


def test_articles_post_duplicate_tags_keeps_nothing(
    add_user: Callable, read_all_rows: Callable
) -> None:
    access_token = add_user()[4]
    before = read_all_rows()

    # Проверка, что ошибка в тегах откатывает уже записанные статью и её предпоказ
    answer = requests.post(
        LOCALHOST + "/articles",
        json={**ARTICLE_BODY, "tags": ["tag", "tag"]},
        headers=auth_headers(access_token),
    )
    assert_error(answer, "validation", "Article tags must be unique")
    assert read_all_rows() == before


def test_articles_post_failed_write_keeps_nothing(
    add_user: Callable, fail_write: Callable, read_all_rows: Callable
) -> None:
    access_token = add_user()[4]
    fail_write("INSERT", "article_tags")
    before = read_all_rows()

    # Проверка, что сбой последней записи откатывает статью и её предпоказ
    answer = requests.post(
        LOCALHOST + "/articles",
        json=ARTICLE_BODY,
        headers=auth_headers(access_token),
    )
    _assert_unexpected_error(answer)
    assert read_all_rows() == before


@pytest.mark.parametrize(
    "resource, reaction, opposite",
    [
        ("article", "like", "dislike"),
        ("article", "dislike", "like"),
        ("comment", "like", "dislike"),
        ("comment", "dislike", "like"),
    ],
)
def test_reaction_put_failed_write_keeps_previous_reaction(
    add_user: Callable,
    add_article: Callable,
    add_comment: Callable,
    fail_write: Callable,
    read_all_rows: Callable,
    resource: str,
    reaction: str,
    opposite: str,
) -> None:
    author_token = add_user()[4]
    reader_token = add_user()[4]
    article_id = add_article(author_token)
    comment_id = add_comment(author_token, article_id)
    path = (
        f"/articles/{article_id}"
        if resource == "article"
        else f"/comments/{comment_id}"
    )
    answer = requests.put(
        f"{LOCALHOST}{path}/{opposite}", headers=auth_headers(reader_token)
    )
    assert_ok(answer, 204)
    # Прежняя реакция снимается первой, поэтому вставка новой и есть поздняя запись.
    fail_write("INSERT", f"{resource}_{reaction}s")
    before = read_all_rows()

    # Проверка, что новая реакция и снятие прежней применяются только вместе
    answer = requests.put(
        f"{LOCALHOST}{path}/{reaction}", headers=auth_headers(reader_token)
    )
    _assert_unexpected_error(answer)
    assert read_all_rows() == before


def test_auth_login_failed_write_keeps_nothing(
    add_user: Callable, fail_write: Callable, read_all_rows: Callable
) -> None:
    username, password, *_ = add_user()
    fail_write("INSERT", "refresh_tokens")
    before = read_all_rows()

    # Проверка, что без refresh token не остаётся и выпущенного access token
    answer = requests.post(
        LOCALHOST + "/auth/login", json={"username": username, "password": password}
    )
    _assert_unexpected_error(answer)
    assert read_all_rows() == before


def test_auth_refresh_failed_write_keeps_old_token(
    add_user: Callable, fail_write: Callable, read_all_rows: Callable
) -> None:
    refresh_token = add_user()[5]
    fail_write("INSERT", "refresh_tokens")
    before = read_all_rows()

    # Проверка, что сбой ротации не лишает пользователя действующего refresh token
    answer = requests.post(
        LOCALHOST + "/auth/refresh", json={"refresh_token": refresh_token}
    )
    _assert_unexpected_error(answer)
    assert read_all_rows() == before


def test_auth_logout_failed_write_keeps_session(
    add_user: Callable, fail_write: Callable, read_all_rows: Callable
) -> None:
    access_token, refresh_token = add_user()[4:6]
    fail_write("DELETE", "refresh_tokens")
    before = read_all_rows()

    # Проверка, что сессия не остаётся наполовину завершённой
    answer = requests.post(
        LOCALHOST + "/auth/logout",
        json={"refresh_token": refresh_token},
        headers=auth_headers(access_token),
    )
    _assert_unexpected_error(answer)
    assert read_all_rows() == before


def test_auth_logout_all_failed_write_keeps_sessions(
    add_user: Callable, fail_write: Callable, read_all_rows: Callable
) -> None:
    access_token = add_user()[4]
    fail_write("DELETE", "refresh_tokens")
    before = read_all_rows()

    # Проверка, что access token не отзывается отдельно от refresh token
    answer = requests.post(
        LOCALHOST + "/auth/logout-all", headers=auth_headers(access_token)
    )
    _assert_unexpected_error(answer)
    assert read_all_rows() == before


def _prepare_profile(add_user: Callable) -> tuple:
    """Создаёт пользователя, у которого есть что менять во всех полях PATCH /users/me.

    Args:
        add_user: fixture создания пользователя.

    Returns:
        Кортеж (access_token, username подписки, username блокировки): подписка и
        блокировка нужны, чтобы проверить откат снятия этих связей.
    """
    access_token = add_user()[4]
    subscribed = add_user()[0]
    blocked = add_user()[0]
    answer = _patch_me(
        access_token,
        {
            "sub-tags": ["subscribed_tag"],
            "blocked-tags": ["blocked_tag"],
            "sub-users": [subscribed],
            "blocked-users": [blocked],
        },
    )
    assert_ok(answer, 204)
    return access_token, subscribed, blocked


def _full_patch_body(blocked: str) -> dict:
    """Строит тело PATCH /users/me, которое меняет все поля и все связи пользователя.

    Порядок ключей важен: backend.update_user_info применяет поля в порядке тела,
    поэтому ключ, добавленный в конец, обрабатывается после всех этих записей.

    Args:
        blocked: кто заблокирован, он становится подпиской.

    Returns:
        Тело запроса.
    """
    return {
        "nickname": "new_nickname",
        "email": "new@test.test",
        "avatar": "new_avatar",
        "description": "new_description",
        "sub-tags": ["blocked_tag"],
        "blocked-tags": ["subscribed_tag"],
        "sub-users": [blocked],
    }


def test_users_me_patch_error_in_last_field_keeps_profile(
    add_user: Callable, read_all_rows: Callable
) -> None:
    access_token, subscribed, blocked = _prepare_profile(add_user)
    before = read_all_rows()
    body = _full_patch_body(blocked)
    body["blocked-users"] = [subscribed, "missing_user"]

    # Проверка, что ошибка в последнем значении последнего поля откатывает все поля
    answer = _patch_me(access_token, body)
    assert_error(answer, "validation", "Cannot find user with username: missing_user")
    assert read_all_rows() == before


def test_users_me_patch_failed_write_keeps_profile(
    add_user: Callable, fail_write: Callable, read_all_rows: Callable
) -> None:
    access_token, subscribed, blocked = _prepare_profile(add_user)
    fail_write("INSERT", "user_blacklist")
    before = read_all_rows()
    body = _full_patch_body(blocked)
    body["blocked-users"] = [subscribed]

    # Проверка, что сбой записи откатывает все поля, применённые до него
    answer = _patch_me(access_token, body)
    _assert_unexpected_error(answer)
    assert read_all_rows() == before


def test_users_me_delete_failed_write_keeps_account(
    add_user: Callable, fail_write: Callable, read_all_rows: Callable
) -> None:
    username, password, _, _, access_token, _ = add_user()
    follower_token = add_user()[4]
    blocker_token = add_user()[4]
    assert_ok(_patch_me(follower_token, {"sub-users": [username]}), 204)
    assert_ok(_patch_me(blocker_token, {"blocked-users": [username]}), 204)
    fail_write("DELETE", "refresh_tokens")
    before = read_all_rows()

    # Проверка, что аккаунт, связи с ним и токены удаляются только вместе
    answer = requests.delete(
        LOCALHOST + "/users/me",
        json={"password": password},
        headers=auth_headers(access_token),
    )
    _assert_unexpected_error(answer)
    assert read_all_rows() == before


def test_users_me_password_put_failed_write_keeps_password(
    add_user: Callable, fail_write: Callable, read_all_rows: Callable
) -> None:
    _, password, _, _, access_token, _ = add_user()
    fail_write("DELETE", "refresh_tokens")
    before = read_all_rows()

    # Проверка, что новый пароль не вступает в силу, пока старые сессии не отозваны
    answer = requests.put(
        LOCALHOST + "/users/me/password",
        json={"previous_password": password, "new_password": "new_password"},
        headers=auth_headers(access_token),
    )
    _assert_unexpected_error(answer)
    assert read_all_rows() == before

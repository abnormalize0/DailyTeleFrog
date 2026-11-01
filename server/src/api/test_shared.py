"""
Этот файл служит для хранения unit-тестов src/api/shared.py: проверки параметров
запроса и построения ответов. Запросы создаются через контекст Flask, поэтому ни
сервер, ни БД не нужны: `session=None` безопасен там, где код не должен идти в БД.
"""

import json

import pytest
from sqlalchemy.orm import Session

from src.api import api_info, shared
from src.request_status import ErrorType

NAME_FIELD = {"name": "name", "type": "str", "is_required": True}


def test_error_response() -> None:
    errors = [{"name": "title", "reason": "is required"}]

    response = shared.error_response(ErrorType.InvalidParameters, "Bad", errors)

    assert response.status_code == 400
    assert response.get_json(force=True)["errors"] == errors


def test_json_response_defaults() -> None:
    response = shared.json_response({"id": 1})

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert json.loads(response.get_data(as_text=True)) == {"id": 1}
    assert "Location" not in response.headers


def test_json_response_location() -> None:
    response = shared.json_response({"id": 1}, 201, "/articles/1")

    assert response.status_code == 201
    assert response.headers["Location"] == "/articles/1"


def test_no_content() -> None:
    response = shared.no_content()

    assert response.status_code == 204
    assert response.get_data() == b""


def test_flask_errors_use_problem_details() -> None:
    response = shared.app.test_client().get("/no-such-path")

    assert response.status_code == 404
    assert response.content_type == "application/problem+json"
    assert response.get_json(force=True)["type"] == "about:blank"


def test_flask_method_errors_keep_allow_header() -> None:
    response = shared.app.test_client().post("/static/none", data="")

    assert response.status_code == 405
    assert response.content_type == "application/problem+json"
    assert "GET" in response.headers["Allow"]


def test_get_bearer_token() -> None:
    with shared.app.test_request_context(headers={"Authorization": "Bearer abc"}):
        assert shared.get_bearer_token() == "abc"


def test_get_bearer_token_rejects_other_formats() -> None:
    with shared.app.test_request_context(headers={"Authorization": "Basic abc"}):
        assert shared.get_bearer_token() == ""
    with shared.app.test_request_context():
        assert shared.get_bearer_token() == ""


def test_optional_auth_without_header_is_anonymous() -> None:
    with shared.app.test_request_context():
        assert shared.optional_auth(None) == (None, None)


def test_require_auth_rejects_missing_and_unknown_token(session: Session) -> None:
    for headers in ({}, {"Authorization": "Bearer unknown"}):
        with shared.app.test_request_context(headers=headers):
            username, response = shared.require_auth(session)

        assert username is None
        assert response.status_code == 401
        assert response.get_json(force=True)["detail"] == "Missing or invalid token"


def test_optional_auth_rejects_unknown_token(session: Session) -> None:
    # Неверный токен не должен молча превращать запрос в анонимный.
    with shared.app.test_request_context(headers={"Authorization": "Bearer unknown"}):
        username, response = shared.optional_auth(session)

    assert username is None
    assert response.status_code == 401


def test_stored_size_counts_bytes_not_characters() -> None:
    assert shared._stored_size("жаба") == 8


def test_stored_size_of_dict_matches_stored_json() -> None:
    # Кириллица без \uXXXX и служебные символы JSON: так dict лежит в колонке.
    assert shared._stored_size({"a": "я"}) == len('{"a": "я"}'.encode("utf8"))


def test_check_limits() -> None:
    assert shared._check_limits("ab", {"max_length": 2}) is None
    assert "2 characters" in shared._check_limits("abc", {"max_length": 2})
    assert shared._check_limits("яя", {"max_bytes": 4}) is None
    assert "3 bytes" in shared._check_limits("яя", {"max_bytes": 3})
    assert shared._check_limits(["ab"], {"item_max_length": 2}) is None
    assert "items" in shared._check_limits(["abc"], {"item_max_length": 2})


def test_check_limits_min_length() -> None:
    element = {"min_length": 3}

    assert shared._check_limits("abc", element) is None
    assert shared._check_limits("ab", element) == "must be at least 3 characters"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "\t\r\n",
        "\x00\x07\x7f",
        "\u00a0",  # неразрывный пробел
        "\u2003\u3000",  # широкие пробелы
        "\u2028\u2029",  # разделители строк и абзацев
        "\u200b\u200c\u200d\u2060",  # пробелы и соединители нулевой ширины
        "\u00ad",  # мягкий перенос
        "\ufeff",  # BOM
        "\u202e",  # управление направлением текста
        "\u3164\uffa0",  # символы-заполнители хангыля
        "\u2800",  # пустой символ Брайля
        "\ufe0f",  # селектор варианта
        {},
    ],
)
def test_check_limits_blank(value: str | dict) -> None:
    assert shared._check_limits(value, {"not_blank": True}) == "must not be blank"


@pytest.mark.parametrize(
    "value",
    [
        "a",
        " a ",
        "жаба",
        ".",
        "0",
        "🐸",
        "\u200ba\u200b",
        "\U0001fae0",  # эмодзи новее базы Unicode в Python 3.10
        {"block": "text"},
    ],
)
def test_check_limits_not_blank(value: str | dict) -> None:
    assert shared._check_limits(value, {"not_blank": True}) is None


def test_check_limits_item_not_blank() -> None:
    element = {"item_not_blank": True}

    assert shared._check_limits(["tag", "другой"], element) is None
    assert shared._check_limits([], element) is None
    for item in ("", "   ", "\u200b"):
        assert shared._check_limits(["tag", item], element) == "items must not be blank"


def test_check_limits_pattern_must_match_whole_value() -> None:
    element = {"pattern": "[a-z]+", "pattern_reason": "must be lowercase"}

    assert shared._check_limits("abc", element) is None
    # fullmatch: search пропустил бы значение с допустимым куском внутри.
    assert shared._check_limits("abc1", element) == "must be lowercase"


def test_check_limits_reports_length_before_pattern() -> None:
    element = {"max_length": 2, "pattern": "[a-z]+", "pattern_reason": "bad format"}

    assert shared._check_limits("!!!", element) == "must be at most 2 characters"


def _field(pattern: list, name: str) -> dict:
    """Находит описание поля в схеме api_info.

    Args:
        pattern: схема метода.
        name: имя поля.

    Returns:
        Описание поля.
    """
    return next(field for field in pattern if field["name"] == name)


@pytest.mark.parametrize("value", ["abc", "a_b-c", "ABC123", "u" * 32])
def test_username_rules_accept(value: str) -> None:
    assert shared._check_limits(value, _field(api_info.users_post, "username")) is None


@pytest.mark.parametrize(
    "value, reason",
    [
        ("", "must be at least 3 characters"),
        ("ab", "must be at least 3 characters"),
        ("u" * 33, "must be at most 32 characters"),
        ("имя", "must contain only Latin letters, digits, _ and -"),
        ("a b", "must contain only Latin letters, digits, _ and -"),
        ("a\x00b", "must contain only Latin letters, digits, _ and -"),
        ("abc\n", "must contain only Latin letters, digits, _ and -"),
    ],
)
def test_username_rules_reject(value: str, reason: str) -> None:
    assert (
        shared._check_limits(value, _field(api_info.users_post, "username")) == reason
    )


@pytest.mark.parametrize("value", ["a@b.c", "first.last+tag@sub.example.com", "я@б.рф"])
def test_email_rules_accept(value: str) -> None:
    assert shared._check_limits(value, _field(api_info.users_post, "email")) is None


@pytest.mark.parametrize(
    "value",
    ["", "plain", "@b.c", "a@", "a@b", "a@b.", "a b@c.d", "a@b@c.d", "a@b.c\n"],
)
def test_email_rules_reject(value: str) -> None:
    assert (
        shared._check_limits(value, _field(api_info.users_post, "email"))
        == "must be a valid email address"
    )


@pytest.mark.parametrize("value", ["N", "Жаба 🐸", "two words"])
def test_nickname_rules_accept(value: str) -> None:
    assert shared._check_limits(value, _field(api_info.users_post, "nickname")) is None


@pytest.mark.parametrize(
    "value, reason",
    [
        ("", "must not be blank"),
        ("   ", "must not be blank"),
        ("\u200b", "must not be blank"),
        ("a\x00b", "must not contain control characters"),
        ("a\nb", "must not contain control characters"),
    ],
)
def test_nickname_rules_reject(value: str, reason: str) -> None:
    assert (
        shared._check_limits(value, _field(api_info.users_post, "nickname")) == reason
    )


@pytest.mark.parametrize(
    "pattern, name",
    [
        (api_info.users_post, "password"),
        (api_info.users_me_password_put, "new_password"),
    ],
)
def test_password_rules(pattern: list, name: str) -> None:
    field = _field(pattern, name)

    assert shared._check_limits("p" * 8, field) is None
    assert shared._check_limits("p" * 128, field) is None
    assert shared._check_limits("p" * 7, field) == "must be at least 8 characters"
    assert shared._check_limits("p" * 129, field) == "must be at most 128 characters"


def test_login_does_not_apply_registration_rules() -> None:
    # Иначе аккаунты со старым коротким паролем не смогли бы войти, а ответ
    # подсказывал бы правила вместо единого "Incorrect login or password".
    for field in api_info.auth_login_post:
        assert "min_length" not in field
        assert "pattern" not in field


def test_patch_uses_registration_rules() -> None:
    for name in ("nickname", "email"):
        patch_field = _field(api_info.users_me_patch, name)
        post_field = _field(api_info.users_post, name)

        assert patch_field["pattern"] == post_field["pattern"]


@pytest.mark.parametrize(
    "pattern, name",
    [
        (api_info.articles_post, "title"),
        (api_info.articles_post, "body"),
        (api_info.articles_comments_post, "text"),
    ],
)
def test_content_must_not_be_blank(pattern: list, name: str) -> None:
    assert _field(pattern, name)["not_blank"]


@pytest.mark.parametrize(
    "pattern, name",
    [
        (api_info.articles_post, "tags"),
        (api_info.users_me_patch, "sub-tags"),
        (api_info.users_me_patch, "blocked-tags"),
    ],
)
def test_tags_must_not_be_blank(pattern: list, name: str) -> None:
    assert _field(pattern, name)["item_not_blank"]


def test_check_structure_accepts_valid_data() -> None:
    assert shared.check_structure({"name": "frog"}, [NAME_FIELD]) == []


def test_check_structure_required_and_optional() -> None:
    pattern = [NAME_FIELD, {"name": "age", "type": "int", "is_required": False}]

    assert shared.check_structure({}, pattern) == [
        {"name": "name", "reason": "is required"}
    ]


def test_check_structure_reports_all_errors() -> None:
    pattern = [NAME_FIELD, {"name": "age", "type": "int", "is_required": True}]

    errors = shared.check_structure({"age": "old"}, pattern)

    assert [error["name"] for error in errors] == ["name", "age"]


def test_check_structure_does_not_accept_bool_as_int() -> None:
    # isinstance(True, int) истинно, поэтому важно сравнение типов через type().
    pattern = [{"name": "age", "type": "int", "is_required": True}]

    assert shared.check_structure({"age": True}, pattern) == [
        {"name": "age", "reason": "must be int"}
    ]


@pytest.mark.parametrize(
    "type_name, value",
    [
        ("str", "\ud800"),
        ("dict", {"key": "\ud800"}),
        ("dict", {"\ud800": "value"}),
        ("dict", {"key": ["\ud800"]}),
        ("list", ["\ud800"]),
    ],
)
def test_check_structure_rejects_invalid_unicode(type_name: str, value: object) -> None:
    # Такое значение проходит проверку типа, а падает уже при записи в БД как 500.
    pattern = [{"name": "field", "type": type_name, "is_required": True}]

    assert shared.check_structure({"field": value}, pattern) == [
        {"name": "field", "reason": "must be valid Unicode text"}
    ]


def test_check_structure_accepts_any_valid_unicode() -> None:
    pattern = [{"name": "field", "type": "str", "is_required": True}]

    assert shared.check_structure({"field": "жаба 🐸 \x00"}, pattern) == []


def test_check_structure_invalid_unicode_with_byte_limit() -> None:
    # Проверка размера кодирует значение в UTF-8 и без этой защиты бросила бы исключение.
    pattern = [{"name": "field", "type": "str", "is_required": True, "max_bytes": 9}]

    errors = shared.check_structure({"field": "\ud800"}, pattern)

    assert errors == [{"name": "field", "reason": "must be valid Unicode text"}]


def test_check_structure_list_allowed_values() -> None:
    pattern = [
        {
            "name": "requested_data",
            "type": "list",
            "is_required": True,
            "structure": [{"name": "nickname"}, {"name": "email"}],
        }
    ]

    assert shared.check_structure({"requested_data": ["email"]}, pattern) == []
    errors = shared.check_structure({"requested_data": ["password"]}, pattern)
    assert errors[0]["reason"] == "must be one of ['nickname', 'email']"


def test_check_structure_list_item_type() -> None:
    pattern = [
        {"name": "tags", "type": "list", "is_required": True, "item_type": "str"}
    ]

    assert shared.check_structure({"tags": ["a"]}, pattern) == []
    assert shared.check_structure({"tags": [1]}, pattern) == [
        {"name": "tags", "reason": "must contain str"}
    ]


def test_check_structure_applies_limits() -> None:
    pattern = [{**NAME_FIELD, "max_length": 2}]

    assert shared.check_structure({"name": "abc"}, pattern) == [
        {"name": "name", "reason": "must be at most 2 characters"}
    ]


def test_read_body_invalid_unicode_is_400() -> None:
    with shared.app.test_request_context(
        data='{"name": "\\ud800"}', content_type="application/json"
    ):
        data, response = shared.read_body([NAME_FIELD])

    assert data is None
    problem = response.get_json(force=True)
    assert problem["detail"] == "Wrong request parameters structure"
    assert problem["errors"] == [
        {"name": "name", "reason": "must be valid Unicode text"}
    ]


def test_read_body_valid() -> None:
    with shared.app.test_request_context(json={"name": "frog"}):
        assert shared.read_body([NAME_FIELD]) == ({"name": "frog"}, None)


def test_read_body_broken_or_non_object_json_is_400() -> None:
    bodies = ["{broken", "[1, 2]"]
    for body in bodies:
        with shared.app.test_request_context(
            data=body, content_type="application/json"
        ):
            data, response = shared.read_body([NAME_FIELD])

        assert data is None
        assert response.status_code == 400
        assert response.get_json(force=True)["errors"] == [
            {"name": "name", "reason": "is required"}
        ]


def test_parse_query_value() -> None:
    assert shared._parse_query_value("true", "bool") is True
    assert shared._parse_query_value("false", "bool") is False
    assert shared._parse_query_value("yes", "bool") == "yes"
    assert shared._parse_query_value("12", "int") == 12
    assert shared._parse_query_value("abc", "int") == "abc"
    assert shared._parse_query_value("12", "str") == "12"


def test_read_query_restores_types() -> None:
    pattern = [
        {"name": "page", "type": "int", "is_required": True},
        {"name": "full", "type": "bool", "is_required": True},
        {"name": "ids", "type": "list", "is_required": True, "item_type": "int"},
    ]

    with shared.app.test_request_context("/?page=2&full=true&ids=1&ids=2"):
        data, response = shared.read_query(pattern)

    assert response is None
    assert data == {"page": 2, "full": True, "ids": [1, 2]}


def test_read_query_rejects_wrong_type() -> None:
    pattern = [{"name": "page", "type": "int", "is_required": True}]

    with shared.app.test_request_context("/?page=abc"):
        data, response = shared.read_query(pattern)

    assert data is None
    assert response.status_code == 400
    assert response.get_json(force=True)["errors"] == [
        {"name": "page", "reason": "must be int"}
    ]


def test_fill_default() -> None:
    pattern = [
        {"name": "name", "type": "str"},
        {"name": "age", "type": "int"},
    ]

    assert shared.fill_default({"name": "frog"}, pattern) == {
        "name": "frog",
        "age": api_info.type_defaults["int"],
    }

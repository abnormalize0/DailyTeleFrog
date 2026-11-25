"""
Этот файл служит для хранения unit-тестов src/api/shared.py: проверки параметров
запроса и построения ответов. Запросы создаются через контекст Flask, поэтому ни
сервер, ни БД не нужны: `session=None` безопасен там, где код не должен идти в БД.
"""

import pytest
from sqlalchemy.orm import Session

from src.api import api_info, shared
from src.request_status import ErrorType

NAME_FIELD = {"name": "name", "type": "str", "is_required": True}


def test_error_response() -> None:
    errors = [{"pointer": "/title", "detail": "is required"}]

    response = shared.error_response(ErrorType.InvalidParameters, "Bad", errors)

    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == errors


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


def test_check_limits_item_pattern() -> None:
    element = {
        "item_pattern": "[^\\x00-\\x1f\\x7f]+",
        "item_pattern_reason": "items must not contain control characters",
    }

    assert shared._check_limits(["ok", "тег 1"], element) is None
    assert shared._check_limits([], element) is None
    # fullmatch: допустимое начало не должно маскировать управляющий символ в конце.
    assert (
        shared._check_limits(["ok", "bad\n"], element)
        == "items must not contain control characters"
    )
    assert (
        shared._check_limits(["ok", "bad\x7f"], element)
        == "items must not contain control characters"
    )


def test_check_limits_reports_item_length_and_blank_before_item_pattern() -> None:
    element = {
        "item_max_length": 2,
        "item_not_blank": True,
        "item_pattern": "[a-z]+",
        "item_pattern_reason": "bad item format",
    }

    assert shared._check_limits(["\t"], element) == "items must not be blank"
    assert (
        shared._check_limits(["!!!"], element) == "items must be at most 2 characters"
    )


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
    [
        "",
        "plain",
        "@b.c",
        "a@",
        "a@b",
        "a@b.",
        "a b@c.d",
        "a@b@c.d",
        "a@b.c\n",
        "a\x00b@c.d",
        "a\x01b@c.d",
        "a@b\x07.c",
        "a@b.c\x1f",
        "a@b.c\x7f",
    ],
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
    for name in ("nickname", "email", "avatar"):
        patch_field = _field(api_info.users_me_patch, name)
        post_field = _field(api_info.users_post, name)

        assert patch_field["pattern"] == post_field["pattern"]


def test_article_title_rejects_control_chars() -> None:
    field = _field(api_info.articles_post, "title")

    assert shared._check_limits("Обычный заголовок 123", field) is None
    for bad in ("a\nb", "a\rb", "a\tb", "a\x01b", "a\x7fb"):
        assert shared._check_limits(bad, field) == "must not contain control characters"


@pytest.mark.parametrize(
    "pattern",
    [api_info.users_post, api_info.users_me_patch],
)
def test_avatar_rules(pattern: list) -> None:
    field = _field(pattern, "avatar")

    # Пустая строка допустима: позволяет сбросить аватар.
    assert shared._check_limits("", field) is None
    assert shared._check_limits("https://example.com/a.png", field) is None
    for bad in ("a\nb", "a\tb", "a\x01b", "a\x7fb"):
        assert shared._check_limits(bad, field) == "must not contain control characters"


@pytest.mark.parametrize(
    "pattern, name",
    [
        (api_info.articles_post, "tags"),
        (api_info.users_me_patch, "sub-tags"),
        (api_info.users_me_patch, "blocked-tags"),
    ],
)
def test_tags_reject_control_chars(pattern: list, name: str) -> None:
    field = _field(pattern, name)

    assert "item_pattern" in field
    assert shared._check_limits(["rpg", "инди-игры"], field) is None
    for bad in ("tag\n", "tag\t", "tag\x01", "tag\x7f"):
        assert (
            shared._check_limits(["ok", bad], field)
            == "items must not contain control characters"
        )


def test_multiline_fields_allow_newlines_and_tabs() -> None:
    for pattern, name in (
        (api_info.articles_comments_post, "text"),
        (api_info.users_post, "description"),
        (api_info.users_me_patch, "description"),
    ):
        field = _field(pattern, name)
        assert "pattern" not in field
        assert shared._check_limits("line1\nline2\r\n\tindented", field) is None

    for name in ("body", "preview"):
        field = _field(api_info.articles_post, name)
        assert "pattern" not in field
        assert (
            shared._check_limits({"text": "line1\nline2\r\n\tindented"}, field) is None
        )


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
        {"pointer": "/name", "detail": "is required"}
    ]


def test_check_structure_reports_all_errors() -> None:
    pattern = [NAME_FIELD, {"name": "age", "type": "int", "is_required": True}]

    errors = shared.check_structure({"age": "old"}, pattern)

    assert [error["pointer"] for error in errors] == ["/name", "/age"]


def test_check_structure_does_not_accept_bool_as_int() -> None:
    # isinstance(True, int) истинно, поэтому важно сравнение типов через type().
    pattern = [{"name": "age", "type": "int", "is_required": True}]

    assert shared.check_structure({"age": True}, pattern) == [
        {"pointer": "/age", "detail": "must be int"}
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
        {"pointer": "/field", "detail": "must be valid Unicode text"}
    ]


def test_check_structure_accepts_any_valid_unicode() -> None:
    pattern = [{"name": "field", "type": "str", "is_required": True}]

    assert shared.check_structure({"field": "жаба 🐸 \n\t\r"}, pattern) == []
    # Буквальная последовательность \u0000 из 6 символов — не NUL-байт, должна приниматься.
    assert shared.check_structure({"field": r"\u0000"}, pattern) == []


@pytest.mark.parametrize(
    "type_name, value",
    [
        ("str", "a\x00b"),
        ("str", "\x00"),
        ("list", ["ok", "a\x00b"]),
        ("dict", {"key": "a\x00b"}),
        ("dict", {"a\x00b": "value"}),
        ("dict", {"key": ["a\x00b"]}),
        ("dict", {"key": {"nested": "a\x00b"}}),
    ],
)
def test_check_structure_rejects_nul_bytes(type_name: str, value: object) -> None:
    pattern = [{"name": "field", "type": type_name, "is_required": True}]

    assert shared.check_structure({"field": value}, pattern) == [
        {"pointer": "/field", "detail": "must be valid Unicode text"}
    ]


def test_read_query_rejects_nul_bytes() -> None:
    with shared.app.test_request_context("/?name=a%00b"):
        data, response = shared.read_query([NAME_FIELD])

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/name", "detail": "must be valid Unicode text"}
    ]

    tags_pattern = [
        {"name": "tags", "type": "list", "is_required": True, "item_type": "str"}
    ]
    with shared.app.test_request_context("/?tags=ok&tags=a%00b"):
        data, response = shared.read_query(tags_pattern)

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/tags", "detail": "must be valid Unicode text"}
    ]


def test_check_structure_invalid_unicode_with_byte_limit() -> None:
    # Проверка размера кодирует значение в UTF-8 и без этой защиты бросила бы исключение.
    pattern = [{"name": "field", "type": "str", "is_required": True, "max_bytes": 9}]

    errors = shared.check_structure({"field": "\ud800"}, pattern)

    assert errors == [{"pointer": "/field", "detail": "must be valid Unicode text"}]


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
    assert errors == [
        {"pointer": "/requested_data", "detail": "must be one of ['nickname', 'email']"}
    ]


def test_check_structure_scalar_allowed_values() -> None:
    pattern = [
        {
            "name": "sort_column",
            "type": "str",
            "is_required": False,
            "allowed": ["creation_date", "rating"],
        }
    ]

    assert shared.check_structure({}, pattern) == []
    assert shared.check_structure({"sort_column": "rating"}, pattern) == []
    for bad_value in ("bogus", ""):
        assert shared.check_structure({"sort_column": bad_value}, pattern) == [
            {
                "pointer": "/sort_column",
                "detail": "must be one of ['creation_date', 'rating']",
            }
        ]


def test_check_structure_list_item_type() -> None:
    pattern = [
        {"name": "tags", "type": "list", "is_required": True, "item_type": "str"}
    ]

    assert shared.check_structure({"tags": ["a"]}, pattern) == []
    assert shared.check_structure({"tags": [1]}, pattern) == [
        {"pointer": "/tags", "detail": "must contain str"}
    ]


def test_check_structure_applies_limits() -> None:
    pattern = [{**NAME_FIELD, "max_length": 2}]

    assert shared.check_structure({"name": "abc"}, pattern) == [
        {"pointer": "/name", "detail": "must be at most 2 characters"}
    ]


def test_check_structure_rejects_unknown_fields() -> None:
    pattern = [NAME_FIELD, {"name": "age", "type": "int", "is_required": False}]

    assert shared.check_structure({"name": "frog", "extra": 1}, pattern) == [
        {"pointer": "/extra", "detail": "unknown field"}
    ]
    assert shared.check_structure({"extra": 1}, []) == [
        {"pointer": "/extra", "detail": "unknown field"}
    ]
    assert shared.check_structure(
        {"name": "frog", "first": 1, "second": "x"}, pattern
    ) == [
        {"pointer": "/first", "detail": "unknown field"},
        {"pointer": "/second", "detail": "unknown field"},
    ]
    assert shared.check_structure({"age": "old", "extra": 1}, pattern) == [
        {"pointer": "/name", "detail": "is required"},
        {"pointer": "/age", "detail": "must be int"},
        {"pointer": "/extra", "detail": "unknown field"},
    ]


def test_read_body_invalid_unicode_is_422() -> None:
    with shared.app.test_request_context(
        data='{"name": "\\ud800"}', content_type="application/json"
    ):
        data, response = shared.read_body([NAME_FIELD])

    assert data is None
    assert response.status_code == 422
    problem = response.get_json(force=True)
    assert problem["detail"] == "Wrong request parameters structure"
    assert problem["errors"] == [
        {"pointer": "/name", "detail": "must be valid Unicode text"}
    ]


def test_read_body_valid() -> None:
    with shared.app.test_request_context(json={"name": "frog"}):
        assert shared.read_body([NAME_FIELD]) == ({"name": "frog"}, None)


def test_read_body_accepts_empty_object_for_optional_schema() -> None:
    optional_pattern = [{"name": "opt", "type": "str", "is_required": False}]
    with shared.app.test_request_context(json={}):
        assert shared.read_body(optional_pattern) == ({}, None)


@pytest.mark.parametrize(
    "pattern",
    [
        [NAME_FIELD],
        [{"name": "opt", "type": "str", "is_required": False}],
    ],
)
@pytest.mark.parametrize(
    "body, content_type",
    [
        ("{broken", "application/json"),
        ("[1, 2]", "application/json"),
        ('"str"', "application/json"),
        ("123", "application/json"),
        ("true", "application/json"),
        ("null", "application/json"),
        ("", "application/json"),
        ('{"name": "frog"}', "text/plain"),
        ('{"name": "frog"}', None),
    ],
)
def test_read_body_broken_or_non_object_json_is_400(
    pattern: list, body: str, content_type: str | None
) -> None:
    with shared.app.test_request_context(data=body, content_type=content_type):
        data, response = shared.read_body(pattern)

    assert data is None
    assert response.status_code == 400
    problem = response.get_json(force=True)
    assert problem["type"] == "/errors/bad-request"
    assert problem["detail"] == "Request body must be a JSON object"
    assert "errors" not in problem


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
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/page", "detail": "must be int"}
    ]


def test_read_body_rejects_unknown_fields() -> None:
    with shared.app.test_request_context(json={"name": "frog", "extra": 1}):
        data, response = shared.read_body([NAME_FIELD])

    assert data is None
    assert response.status_code == 422
    problem = response.get_json(force=True)
    assert problem["type"] == "/errors/validation"
    assert problem["detail"] == "Wrong request parameters structure"
    assert problem["errors"] == [{"pointer": "/extra", "detail": "unknown field"}]

    optional_pattern = [{"name": "nickname", "type": "str", "is_required": False}]
    with shared.app.test_request_context(json={"nikname": "Vasya"}):
        data, response = shared.read_body(optional_pattern)

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/nikname", "detail": "unknown field"}
    ]


def test_read_query_rejects_unknown_fields() -> None:
    pattern = [{"name": "page", "type": "int", "is_required": True}]

    with shared.app.test_request_context("/?page=1&sort_by=rating"):
        data, response = shared.read_query(pattern)

    assert data is None
    assert response.status_code == 422
    problem = response.get_json(force=True)
    assert problem["type"] == "/errors/validation"
    assert problem["detail"] == "Wrong request parameters structure"
    assert problem["errors"] == [{"pointer": "/sort_by", "detail": "unknown field"}]

    with shared.app.test_request_context("/?page=1&foo=1&foo=2&bar=3&empty"):
        data, response = shared.read_query(pattern)

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/foo", "detail": "unknown field"},
        {"pointer": "/bar", "detail": "unknown field"},
        {"pointer": "/empty", "detail": "unknown field"},
    ]


def test_read_body_rejects_query_params() -> None:
    with shared.app.test_request_context("/?extra=1", json={"name": "frog"}):
        data, response = shared.read_body([NAME_FIELD])

    assert data is None
    assert response.status_code == 422
    problem = response.get_json(force=True)
    assert problem["type"] == "/errors/validation"
    assert problem["detail"] == "Wrong request parameters structure"
    assert problem["errors"] == [{"pointer": "/extra", "detail": "unknown field"}]

    # Имя query-параметра может совпадать с полем тела — оно всё равно лишнее.
    with shared.app.test_request_context("/?name=frog", json={"name": "frog"}):
        data, response = shared.read_body([NAME_FIELD])

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/name", "detail": "unknown field"}
    ]

    # Ошибки тела и query-строки собираются вместе за один запрос.
    with shared.app.test_request_context("/?extra=1", json={}):
        data, response = shared.read_body([NAME_FIELD])

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/name", "detail": "is required"},
        {"pointer": "/extra", "detail": "unknown field"},
    ]


def test_read_query_rejects_body() -> None:
    pattern = [{"name": "page", "type": "int", "is_required": True}]

    with shared.app.test_request_context("/?page=1", json={"extra": 1}):
        data, response = shared.read_query(pattern)

    assert data is None
    assert response.status_code == 422
    problem = response.get_json(force=True)
    assert problem["type"] == "/errors/validation"
    assert problem["detail"] == "Wrong request parameters structure"
    assert problem["errors"] == [{"pointer": "/extra", "detail": "unknown field"}]

    for body, content_type in (
        ("{}", "application/json"),
        ("[1, 2]", "application/json"),
        ("{broken", "application/json"),
        ("raw", "text/plain"),
    ):
        with shared.app.test_request_context(
            "/?page=1", data=body, content_type=content_type
        ):
            data, response = shared.read_query(pattern)

        assert data is None
        assert response.status_code == 422
        assert response.get_json(force=True)["errors"] == [
            {"pointer": "", "detail": "request body is not allowed"}
        ]


def test_require_no_params() -> None:
    with shared.app.test_request_context("/"):
        assert shared.require_no_params() is None

    with shared.app.test_request_context("/?extra=1&extra=2"):
        response = shared.require_no_params()

    assert response is not None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/extra", "detail": "unknown field"}
    ]

    with shared.app.test_request_context("/", json={"refresh_token": "abc"}):
        response = shared.require_no_params()

    assert response is not None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/refresh_token", "detail": "unknown field"}
    ]

    for body, content_type in (("{}", "application/json"), ("raw", "text/plain")):
        with shared.app.test_request_context("/", data=body, content_type=content_type):
            response = shared.require_no_params()

        assert response is not None
        assert response.status_code == 422
        assert response.get_json(force=True)["errors"] == [
            {"pointer": "", "detail": "request body is not allowed"}
        ]

    with shared.app.test_request_context("/?q=1", json={"b": 2}):
        response = shared.require_no_params()

    assert response is not None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/q", "detail": "unknown field"},
        {"pointer": "/b", "detail": "unknown field"},
    ]


def test_unknown_field_with_invalid_unicode_key() -> None:
    expected = [
        {"pointer": "", "detail": "unknown field name must be valid Unicode text"}
    ]

    assert (
        shared.check_structure({"name": "frog", "\ud800": 1}, [NAME_FIELD]) == expected
    )
    assert (
        shared.check_structure({"name": "frog", "bad\x00key": 1}, [NAME_FIELD])
        == expected
    )

    with shared.app.test_request_context(
        data='{"name": "frog", "\\ud800": 1}', content_type="application/json"
    ):
        data, response = shared.read_body([NAME_FIELD])

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == expected

    with shared.app.test_request_context(
        data='{"\\ud800": 1}', content_type="application/json"
    ):
        response = shared.require_no_params()

    assert response is not None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == expected


def test_fill_default() -> None:
    pattern = [
        {"name": "name", "type": "str"},
        {"name": "age", "type": "int"},
        {"name": "title", "type": "str"},
        {"name": "active", "type": "bool"},
    ]

    assert shared.fill_default({"name": "frog"}, pattern) == {
        "name": "frog",
        "age": None,
        "title": "",
        "active": True,
    }


def test_fill_default_returns_independent_lists() -> None:
    pattern = [
        {"name": "include_tags", "type": "list"},
        {"name": "exclude_tags", "type": "list"},
    ]

    first = shared.fill_default({}, pattern)
    second = shared.fill_default({}, pattern)

    assert first["include_tags"] == []
    assert first["exclude_tags"] == []
    assert first["include_tags"] is not first["exclude_tags"]
    assert first["include_tags"] is not second["include_tags"]

    first["include_tags"].append("rpg")

    assert first["exclude_tags"] == []
    assert second["include_tags"] == []
    assert shared.fill_default({}, pattern)["include_tags"] == []


def test_fill_default_returns_independent_dicts() -> None:
    pattern = [
        {"name": "meta", "type": "dict"},
        {"name": "extra", "type": "dict"},
    ]

    first = shared.fill_default({}, pattern)
    second = shared.fill_default({}, pattern)

    assert first["meta"] == {}
    assert first["extra"] == {}
    assert first["meta"] is not first["extra"]
    assert first["meta"] is not second["meta"]

    first["meta"]["k"] = "v"

    assert first["extra"] == {}
    assert second["meta"] == {}
    assert shared.fill_default({}, pattern)["meta"] == {}


def test_check_structure_list_max_items_and_item_min() -> None:
    pattern = [
        {
            "name": "indexes",
            "type": "list",
            "is_required": True,
            "item_type": "int",
            "item_min": 0,
            "max_items": 10,
        }
    ]

    assert (
        shared.check_structure({"indexes": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}, pattern)
        == []
    )

    # Повторы тоже учитываются в длине до дедупликации.
    assert shared.check_structure({"indexes": [0] * 11}, pattern) == [
        {"pointer": "/indexes", "detail": "must contain at most 10 items"}
    ]

    # item_min == 0 не должен игнорироваться как falsy.
    for bad_indexes in ([-1], [0, -2]):
        assert shared.check_structure({"indexes": bad_indexes}, pattern) == [
            {"pointer": "/indexes", "detail": "items must be at least 0"}
        ]

    # Приоритет проверок: длина проверяется раньше минимального значения элементов,
    # а тип элемента — раньше _check_limits.
    assert shared.check_structure({"indexes": [-1] * 11}, pattern) == [
        {"pointer": "/indexes", "detail": "must contain at most 10 items"}
    ]
    assert shared.check_structure({"indexes": ["abc"]}, pattern) == [
        {"pointer": "/indexes", "detail": "must contain int"}
    ]


def test_read_query_articles_indexes_validation() -> None:
    eleven_zeros = "&".join(["indexes=0"] * 11)
    for query, expected_detail in (
        ("/?indexes=-1", "items must be at least 0"),
        ("/?indexes=0&indexes=-2", "items must be at least 0"),
        (f"/?{eleven_zeros}", "must contain at most 10 items"),
    ):
        with shared.app.test_request_context(query):
            data, response = shared.read_query(api_info.articles_get)

        assert data is None
        assert response.status_code == 422
        assert response.get_json(force=True)["errors"] == [
            {"pointer": "/indexes", "detail": expected_detail}
        ]


def test_read_query_rejects_duplicate_scalar_params() -> None:
    required_int = [{"name": "page", "type": "int", "is_required": True}]
    with shared.app.test_request_context("/?page=1&page=2"):
        data, response = shared.read_query(required_int)

    assert data is None
    assert response.status_code == 422
    problem = response.get_json(force=True)
    assert problem["type"] == "/errors/validation"
    assert problem["detail"] == "Wrong request parameters structure"
    assert problem["errors"] == [{"pointer": "/page", "detail": "must not be repeated"}]

    for query, pointer in (
        ("/?indexes=0&sort_column=rating&sort_column=creation_date", "/sort_column"),
        ("/?indexes=0&sort_column=rating&sort_column=a%00b", "/sort_column"),
        ("/?indexes=0&sort_column=a%00b&sort_column=rating", "/sort_column"),
        ("/?indexes=0&upper_date=100&upper_date=bogus", "/upper_date"),
        ("/?indexes=0&upper_date=bogus&upper_date=100", "/upper_date"),
        ("/?indexes=0&include_nonsub=true&include_nonsub=false", "/include_nonsub"),
    ):
        with shared.app.test_request_context(query):
            data, response = shared.read_query(api_info.articles_get)

        assert data is None
        assert response.status_code == 422
        assert response.get_json(force=True)["errors"] == [
            {"pointer": pointer, "detail": "must not be repeated"}
        ]

    with shared.app.test_request_context("/?name=&name="):
        data, response = shared.read_query([NAME_FIELD])

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/name", "detail": "must not be repeated"}
    ]

    # Одновременное дублирование двух разных скалярных параметров.
    combined_pattern = [
        {"name": "page", "type": "int", "is_required": True},
        {"name": "sort", "type": "str", "is_required": False},
    ]
    with shared.app.test_request_context("/?page=1&page=2&sort=a&sort=b"):
        data, response = shared.read_query(combined_pattern)

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/page", "detail": "must not be repeated"},
        {"pointer": "/sort", "detail": "must not be repeated"},
    ]

    # Дублирование скаляра вместе с ошибкой значения другого присутствующего поля.
    with shared.app.test_request_context(
        "/?indexes=0&sort_column=rating&sort_column=creation_date&upper_date=bogus"
    ):
        data, response = shared.read_query(api_info.articles_get)

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/upper_date", "detail": "must be int"},
        {"pointer": "/sort_column", "detail": "must not be repeated"},
    ]

    # Ошибки отсутствующего, неизвестного, дублирующегося параметров и лишнего тела
    # собираются вместе за один запрос.
    with shared.app.test_request_context(
        "/?sort=a&sort=b&extra=1", json={"body_field": 1}
    ):
        data, response = shared.read_query(combined_pattern)

    assert data is None
    assert response.status_code == 422
    assert response.get_json(force=True)["errors"] == [
        {"pointer": "/page", "detail": "is required"},
        {"pointer": "/extra", "detail": "unknown field"},
        {"pointer": "/sort", "detail": "must not be repeated"},
        {"pointer": "/body_field", "detail": "unknown field"},
    ]

    # Списочные параметры по-прежнему принимают несколько значений.
    with shared.app.test_request_context("/?indexes=0&indexes=1&sort_column=rating"):
        data, response = shared.read_query(api_info.articles_get)

    assert response is None
    assert data == {"indexes": [0, 1], "sort_column": "rating"}

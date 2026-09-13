"""
Этот файл служит для хранения API методов, которые возвращают структуру входных данных.
Для каждого пути, по которому сервер принимает запросы должен быть свой API метод.
API методы обязаны обрабатывать запросы типа OPTIONS, так как это поведение используется в тестах.
Название методов формируется следующим образом: %METHOD_NAME%_info. %METHOD_NAME% такой же как и в /server/src/api.py
Таким образом имена не будут дублироваться для одних и тех же путей.
"""

import json
from flask import Blueprint

info = Blueprint("info", __name__)

type_defaults = {
    "int": None,
    "str": "",
    "json": {},
    "list": [],
    "bool": True,
    "date": "",
}

article_post = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {
        "name": "body",
        "type": "dict",
        "is_required": True,
        "container": "body",
        "structure": [],
    },
    {
        "name": "preview",
        "type": "dict",
        "is_required": True,
        "container": "body",
        "structure": [],
    },
    {
        "name": "title",
        "type": "str",
        "is_required": True,
        "container": "body",
    },
    {
        "name": "tags",
        "type": "list",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
]

article_get = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {"name": "article_id", "type": "int", "is_required": True, "container": "body"},
]


@info.route("/article", methods=["OPTIONS"])
def article_info():
    """Отвечает на OPTIONS /article.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /article.
    """
    return json.dumps({"post": article_post, "get": article_get})


article_like_post = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {"name": "article_id", "type": "int", "is_required": True, "container": "body"},
]

article_like_get = []


@info.route("/article/like", methods=["OPTIONS"])
def article_like_info():
    """Отвечает на OPTIONS /article/like.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /article/like.
    """
    return json.dumps({"post": article_like_post, "get": article_like_get})


article_dislike_post = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {"name": "article_id", "type": "int", "is_required": True, "container": "body"},
]

article_dislike_get = []


@info.route("/article/dislike", methods=["OPTIONS"])
def article_dislike_info():
    """Отвечает на OPTIONS /article/dislike.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /article/dislike.
    """
    return json.dumps({"post": article_dislike_post, "get": article_dislike_get})


article_comment_post = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {"name": "article_id", "type": "int", "is_required": True, "container": "body"},
    {"name": "text", "type": "str", "is_required": True, "container": "body"},
    {"name": "root", "type": "int", "is_required": True, "container": "body"},
]

article_comment_get = []


@info.route("/article/comment", methods=["OPTIONS"])
def article_comment_info():
    """Отвечает на OPTIONS /article/comment.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /article/comment.
    """
    return json.dumps({"post": article_comment_post, "get": article_comment_get})


article_comment_like_post = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {"name": "comment_id", "type": "int", "is_required": True, "container": "body"},
]

article_comment_like_get = []


@info.route("/article/comment/like", methods=["OPTIONS"])
def article_comment_like_info():
    """Отвечает на OPTIONS /article/comment/like.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /article/comment/like.
    """
    return json.dumps(
        {"post": article_comment_like_post, "get": article_comment_like_get}
    )


article_comment_dislike_post = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {"name": "comment_id", "type": "int", "is_required": True, "container": "body"},
]

article_comment_dislike_get = []


@info.route("/article/comment/dislike", methods=["OPTIONS"])
def article_comment_dislike_info():
    """Отвечает на OPTIONS /article/comment/dislike.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /article/comment/dislike.
    """
    return json.dumps(
        {"post": article_comment_dislike_post, "get": article_comment_dislike_get}
    )


article_comment_data_post = []

article_comment_data_get = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {"name": "comment_id", "type": "int", "is_required": True, "container": "body"},
    {
        "name": "requested_data",
        "type": "list",
        "is_required": True,
        "container": "body",
        "structure": [
            {
                "name": "likes",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "dislikes",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "rating",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "creation_date",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "is_liked",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "is_disliked",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
        ],
    },
]


@info.route("/article/comment/data", methods=["OPTIONS"])
def article_comment_data_info():
    """Отвечает на OPTIONS /article/comment/data.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /article/comment/data.
    """
    return json.dumps(
        {"post": article_comment_data_post, "get": article_comment_data_get}
    )


article_data_post = [
    {"name": "username", "type": "str", "is_required": True, "container": "header"},
    {"name": "article-id", "type": "int", "is_required": True, "container": "header"},
    {
        "name": "like-article",
        "type": "json",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
    {
        "name": "dislike-article",
        "type": "json",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
    {
        "name": "like-comment",
        "type": "json",
        "is_required": False,
        "container": "body",
        "structure": [{"name": "comment_id", "type": "int", "is_required": True}],
    },
    {
        "name": "dislike-comment",
        "type": "json",
        "is_required": False,
        "container": "body",
        "structure": [{"name": "comment_id", "type": "int", "is_required": True}],
    },
    {
        "name": "add-comment",
        "type": "json",
        "is_required": False,
        "container": "body",
        "structure": [
            {"name": "root", "type": "int", "is_required": True},
            {"name": "text", "type": "str", "is_required": True},
        ],
    },
]

article_data_get = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {"name": "article_id", "type": "int", "is_required": True, "container": "body"},
    {
        "name": "requested_data",
        "type": "list",
        "is_required": True,
        "container": "body",
        "structure": [
            {
                "name": "likes",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "dislikes",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "rating",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "comments_count",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "creation_date",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "is_liked",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
            {
                "name": "is_disliked",
                "type": "field",
                "is_required": True,
                "container": "body",
            },
        ],
    },
]


@info.route("/article/data", methods=["OPTIONS"])
def article_data_info():
    """Отвечает на OPTIONS /article/data.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /article/data.
    """
    return json.dumps({"post": article_data_post, "get": article_data_get})


pages_post = []

pages_get = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {
        "name": "indexes",
        "type": "list",
        "is_required": True,
        "container": "body",
        "structure": [],
    },
    {
        "name": "include_nonsub",
        "type": "bool",
        "is_required": False,
        "container": "body",
    },
    {"name": "sort_column", "type": "str", "is_required": False, "container": "body"},
    {
        "name": "sort_direction",
        "type": "str",
        "is_required": False,
        "container": "body",
    },
    {"name": "upper_date", "type": "int", "is_required": False, "container": "body"},
    {"name": "lower_date", "type": "int", "is_required": False, "container": "body"},
    {
        "name": "upper_rating",
        "type": "int",
        "is_required": False,
        "container": "body",
    },
    {
        "name": "lower_rating",
        "type": "int",
        "is_required": False,
        "container": "body",
    },
    {
        "name": "include_tags",
        "type": "list",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
    {
        "name": "exclude_tags",
        "type": "list",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
    {
        "name": "include_authors",
        "type": "list",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
    {
        "name": "exclude_authors",
        "type": "list",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
]


@info.route("/pages", methods=["OPTIONS"])
def pages_info():
    """Отвечает на OPTIONS /pages.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /pages.
    """
    return json.dumps({"post": pages_post, "get": pages_get})


users_post = [
    {
        "name": "username",
        "type": "str",
        "is_required": True,
        "container": "body",
    },
    {
        "name": "nickname",
        "type": "str",
        "is_required": True,
        "container": "body",
    },
    {
        "name": "email",
        "type": "str",
        "is_required": True,
        "container": "body",
    },
    {
        "name": "password",
        "type": "str",
        "is_required": True,
        "container": "body",
    },
    {
        "name": "avatar",
        "type": "str",
        "is_required": False,
        "container": "body",
    },
    {
        "name": "description",
        "type": "str",
        "is_required": False,
        "container": "body",
    },
]

users_get = []


@info.route("/users", methods=["OPTIONS"])
def users_info():
    """Отвечает на OPTIONS /users.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /users.
    """
    return json.dumps({"post": users_post, "get": users_get})


users_data_post = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {
        "name": "nickname",
        "type": "str",
        "is_required": False,
        "container": "body",
    },
    {
        "name": "email",
        "type": "str",
        "is_required": False,
        "container": "body",
    },
    {
        "name": "avatar",
        "type": "str",
        "is_required": False,
        "container": "body",
    },
    {
        "name": "sub-tags",
        "type": "list",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
    {
        "name": "blocked-tags",
        "type": "list",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
    {
        "name": "sub-users",
        "type": "list",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
    {
        "name": "blocked-users",
        "type": "list",
        "is_required": False,
        "container": "body",
        "structure": [],
    },
    {
        "name": "description",
        "type": "str",
        "is_required": False,
        "container": "body",
    },
]

users_data_get = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {
        "name": "requested_data",
        "type": "list",
        "is_required": True,
        "container": "body",
        "structure": [
            {
                "name": "nickname",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "email",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "name_history",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "avatar",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "sub_tags",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "blocked_tags",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "sub_users",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "blocked_users",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "description",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "creation_date",
                "type": "field",
                "is_required": False,
            },
            {
                "name": "rating",
                "type": "field",
                "is_required": False,
            },
        ],
    },
]


@info.route("/users/data", methods=["OPTIONS"])
def users_data_info():
    """Отвечает на OPTIONS /users/data.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /users/data.
    """
    return json.dumps({"post": users_data_post, "get": users_data_get})


user_password_post = [
    {"name": "username", "type": "str", "is_required": True, "container": "body"},
    {
        "name": "previous_password",
        "type": "str",
        "is_required": True,
        "container": "body",
    },
    {"name": "new_password", "type": "str", "is_required": True, "container": "body"},
]

user_password_get = []


@info.route("/users/password", methods=["OPTIONS"])
def users_password_info():
    """Отвечает на OPTIONS /users/password.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /users/password.
    """
    return json.dumps({"post": user_password_post, "get": user_password_get})


login_post = []

login_get = [
    {
        "name": "username",
        "type": "str",
        "is_required": False,
        "container": "body",
    },
    {
        "name": "email",
        "type": "str",
        "is_required": False,
        "container": "body",
    },
    {
        "name": "password",
        "type": "str",
        "is_required": True,
        "container": "body",
    },
]


@info.route("/login", methods=["OPTIONS"])
def login_info():
    """Отвечает на OPTIONS /login.

    Args:
        None

    Returns:
        JSON-строка со схемами полей для POST и GET /login.
    """
    return json.dumps({"post": login_post, "get": login_get})

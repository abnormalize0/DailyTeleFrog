"""
Этот файл служит для хранения описаний параметров API-методов. check_structure и
fill_default в shared.py проверяют по ним запросы, а обработчики OPTIONS отдают
их наружу: так тесты сами узнают, какие параметры у метода.
Название обработчика формируется так: %METHOD_NAME%_info, где %METHOD_NAME% такой
же, как и в src/api/routes/. Таким образом имена не будут дублироваться для одних
и тех же путей.

Поле "container" говорит, откуда читается параметр: "body" (JSON-тело) или
"query" (query-строка, для GET). Параметры из пути сюда не входят: их тип и
наличие проверяет сам маршрут Flask (<int:...>).

Ограничения, которые тоже уходят клиенту через OPTIONS:
- "max_length": предел строки в символах, совпадает с длиной колонки String(n);
- "max_bytes": предел значения в байтах, в виде, в котором оно хранится;
- "item_type" и "item_max_length": тип и предел длины элементов списка;
- "max_items": максимальное число элементов в списке;
- "item_min": минимальное допустимое числовое значение элемента списка;
- "min_length": нижний предел длины строки в символах;
- "not_blank" и "item_not_blank": значение или элемент списка должны содержать
  хотя бы один видимый символ: пробелы, табы, переносы строк и непечатные символы
  видимыми не считаются;
- "pattern" и "pattern_reason": регулярное выражение, которому значение должно
  соответствовать целиком, и причина ошибки, если оно не соответствует;
- "item_pattern" и "item_pattern_reason": регулярное выражение, которому должен
  соответствовать целиком каждый элемент списка, и причина ошибки;
- "allowed": список допустимых значений скалярного поля.
"""

from collections.abc import Callable

from flask import Blueprint

from ..db import scheme

info = Blueprint("info", __name__)

# Предел колонки TEXT в MySQL. Проверяем сами, потому что запись большего значения
# падает с ошибкой БД (500). У String(n) предел свой, и он берётся прямо из схемы.
TEXT_MAX_BYTES = 65_535
# Предел колонки MEDIUMTEXT (scheme.Article.body). Отдельного лимита для статьи нет,
# это та же техническая проверка: без неё значение больше колонки вернулось бы как 500.
ARTICLE_BODY_MAX_BYTES = 16_777_215
_TAG_MAX_LENGTH = scheme.ArticleTag.tag_name.type.length

# Правила ввода данных аккаунта общие для регистрации и изменения профиля, иначе
# ограничение можно было бы обойти через PATCH. См. decisions/0007-input-rules.md.
_USERNAME_RULES = {
    "min_length": 3,
    "max_length": scheme.User.username.type.length,
    # Только латиница: username попадает в ссылки и служит логином, а похожие друг
    # на друга кириллические и латинские буквы позволили бы выдавать себя за другого.
    # Кириллица доступна в nickname.
    "pattern": "[A-Za-z0-9_-]+",
    "pattern_reason": "must contain only Latin letters, digits, _ and -",
}
# Однострочные поля не должны принимать ASCII-управляющие символы (\x00-\x1f, \x7f),
# чтобы переносы строк, табы и прочие управляющие коды не попадали в заголовки,
# имена, ссылки на аватар и теги. Шаблон совместим с JS RegExp.
_NO_CONTROL_CHARS_PATTERN = "[^\\x00-\\x1f\\x7f]+"
_NO_CONTROL_CHARS_REASON = "must not contain control characters"

_NICKNAME_RULES = {
    "max_length": scheme.User.nickname.type.length,
    "not_blank": True,
    "pattern": _NO_CONTROL_CHARS_PATTERN,
    "pattern_reason": _NO_CONTROL_CHARS_REASON,
}
_EMAIL_RULES = {
    "max_length": scheme.User.email.type.length,
    # Намеренно грубая проверка: полный синтаксис RFC 5322 сложен и всё равно не
    # доказывает, что адрес существует. Это покажет только письмо с подтверждением.
    # Исключаем также ASCII-управляющие символы (\x00-\x1f, \x7f), которые могли
    # бы не попасть под \s (например, \x00, \x07, \x7f).
    "pattern": "[^@\\s\\x00-\\x1f\\x7f]+@[^@\\s\\x00-\\x1f\\x7f]+\\.[^@\\s\\x00-\\x1f\\x7f]+",
    "pattern_reason": "must be a valid email address",
}
_AVATAR_RULES = {
    "max_length": scheme.User.avatar.type.length,
    # Квантификатор * (а не +) сохраняет возможность сбросить аватар пустой строкой "".
    "pattern": "[^\\x00-\\x1f\\x7f]*",
    "pattern_reason": _NO_CONTROL_CHARS_REASON,
}
_TAG_ITEM_RULES = {
    "item_type": "str",
    "item_max_length": _TAG_MAX_LENGTH,
    "item_not_blank": True,
    "item_pattern": _NO_CONTROL_CHARS_PATTERN,
    "item_pattern_reason": "items must not contain control characters",
}
# 8 символов — минимум из NIST SP 800-63B, он же не рекомендует требовать разные
# классы символов. Верхний предел защищает от очень длинных значений в запросе.
_NEW_PASSWORD_RULES = {"min_length": 8, "max_length": 128}

# Фабрики вместо готовых значений: для изменяемых типов (list, dict) каждый
# вызов fill_default должен создавать новый независимый экземпляр, иначе мутация
# поля в одном запросе изменит значение по умолчанию для остальных полей и запросов.
type_defaults: dict[str, Callable[[], object]] = {
    "int": lambda: None,
    "str": str,
    "list": list,
    "dict": dict,
    "bool": lambda: True,
}


def _requested_field(name: str) -> dict:
    """Строит описание одного допустимого значения списка requested_data.

    Args:
        name: имя поля.

    Returns:
        dict-описание значения.
    """
    return {"name": name}


articles_post = [
    {
        "name": "title",
        "type": "str",
        "is_required": True,
        "container": "body",
        "max_length": scheme.Article.title.type.length,
        "not_blank": True,
        "pattern": _NO_CONTROL_CHARS_PATTERN,
        "pattern_reason": _NO_CONTROL_CHARS_REASON,
    },
    {
        "name": "body",
        "type": "dict",
        "is_required": True,
        "container": "body",
        "max_bytes": ARTICLE_BODY_MAX_BYTES,
        "not_blank": True,
    },
    {
        "name": "preview",
        "type": "dict",
        "is_required": True,
        "container": "body",
        "max_bytes": TEXT_MAX_BYTES,
    },
    {
        "name": "tags",
        "type": "list",
        "is_required": False,
        "container": "body",
        **_TAG_ITEM_RULES,
    },
]

articles_get = [
    {
        "name": "indexes",
        "type": "list",
        "is_required": True,
        "container": "query",
        "item_type": "int",
        "item_min": 0,
        "max_items": 10,
    },
    {
        "name": "include_nonsub",
        "type": "bool",
        "is_required": False,
        "container": "query",
    },
    {
        "name": "sort_column",
        "type": "str",
        "is_required": False,
        "container": "query",
        "allowed": ["creation_date", "rating"],
    },
    {
        "name": "sort_direction",
        "type": "str",
        "is_required": False,
        "container": "query",
        "allowed": ["descending", "ascending"],
    },
    {"name": "upper_date", "type": "int", "is_required": False, "container": "query"},
    {"name": "lower_date", "type": "int", "is_required": False, "container": "query"},
    {"name": "upper_rating", "type": "int", "is_required": False, "container": "query"},
    {"name": "lower_rating", "type": "int", "is_required": False, "container": "query"},
    {
        "name": "include_tags",
        "type": "list",
        "is_required": False,
        "container": "query",
    },
    {
        "name": "exclude_tags",
        "type": "list",
        "is_required": False,
        "container": "query",
    },
    {
        "name": "include_authors",
        "type": "list",
        "is_required": False,
        "container": "query",
    },
    {
        "name": "exclude_authors",
        "type": "list",
        "is_required": False,
        "container": "query",
    },
]


@info.route("/articles", methods=["OPTIONS"])
def articles_info() -> dict:
    """Отвечает на OPTIONS /articles.

    Args:
        None

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"post": articles_post, "get": articles_get}


@info.route("/articles/<int:article_id>", methods=["OPTIONS"])
def articles_item_info(article_id: int) -> dict:
    """Отвечает на OPTIONS /articles/{id}.

    Args:
        article_id: id из пути, в ответе не используется.

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"get": [], "delete": []}


articles_data_get = [
    {
        "name": "requested_data",
        "type": "list",
        "is_required": True,
        "container": "query",
        "structure": [
            _requested_field("likes"),
            _requested_field("dislikes"),
            _requested_field("rating"),
            _requested_field("comments_count"),
            _requested_field("creation_date"),
            _requested_field("tags"),
            _requested_field("is_liked"),
            _requested_field("is_disliked"),
        ],
    },
]


@info.route("/articles/<int:article_id>/data", methods=["OPTIONS"])
def articles_data_info(article_id: int) -> dict:
    """Отвечает на OPTIONS /articles/{id}/data.

    Args:
        article_id: id из пути, в ответе не используется.

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"get": articles_data_get}


@info.route("/articles/<int:article_id>/like", methods=["OPTIONS"])
def articles_like_info(article_id: int) -> dict:
    """Отвечает на OPTIONS /articles/{id}/like.

    Args:
        article_id: id из пути, в ответе не используется.

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"put": [], "delete": []}


@info.route("/articles/<int:article_id>/dislike", methods=["OPTIONS"])
def articles_dislike_info(article_id: int) -> dict:
    """Отвечает на OPTIONS /articles/{id}/dislike.

    Args:
        article_id: id из пути, в ответе не используется.

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"put": [], "delete": []}


articles_comments_post = [
    {
        "name": "text",
        "type": "str",
        "is_required": True,
        "container": "body",
        "max_bytes": TEXT_MAX_BYTES,
        "not_blank": True,
    },
    {"name": "parent", "type": "int", "is_required": True, "container": "body"},
]


@info.route("/articles/<int:article_id>/comments", methods=["OPTIONS"])
def articles_comments_info(article_id: int) -> dict:
    """Отвечает на OPTIONS /articles/{id}/comments.

    Args:
        article_id: id из пути, в ответе не используется.

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"post": articles_comments_post}


comments_item_get = [
    {
        "name": "requested_data",
        "type": "list",
        "is_required": True,
        "container": "query",
        "structure": [
            _requested_field("likes"),
            _requested_field("dislikes"),
            _requested_field("rating"),
            _requested_field("creation_date"),
            _requested_field("is_liked"),
            _requested_field("is_disliked"),
        ],
    },
]


@info.route("/comments/<int:comment_id>", methods=["OPTIONS"])
def comments_item_info(comment_id: int) -> dict:
    """Отвечает на OPTIONS /comments/{id}.

    Args:
        comment_id: id из пути, в ответе не используется.

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"get": comments_item_get, "delete": []}


@info.route("/comments/<int:comment_id>/like", methods=["OPTIONS"])
def comments_like_info(comment_id: int) -> dict:
    """Отвечает на OPTIONS /comments/{id}/like.

    Args:
        comment_id: id из пути, в ответе не используется.

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"put": [], "delete": []}


@info.route("/comments/<int:comment_id>/dislike", methods=["OPTIONS"])
def comments_dislike_info(comment_id: int) -> dict:
    """Отвечает на OPTIONS /comments/{id}/dislike.

    Args:
        comment_id: id из пути, в ответе не используется.

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"put": [], "delete": []}


users_post = [
    {
        "name": "username",
        "type": "str",
        "is_required": True,
        "container": "body",
        **_USERNAME_RULES,
    },
    {
        "name": "nickname",
        "type": "str",
        "is_required": True,
        "container": "body",
        **_NICKNAME_RULES,
    },
    {
        "name": "email",
        "type": "str",
        "is_required": True,
        "container": "body",
        **_EMAIL_RULES,
    },
    {
        "name": "password",
        "type": "str",
        "is_required": True,
        "container": "body",
        **_NEW_PASSWORD_RULES,
    },
    {
        "name": "avatar",
        "type": "str",
        "is_required": False,
        "container": "body",
        **_AVATAR_RULES,
    },
    {
        "name": "description",
        "type": "str",
        "is_required": False,
        "container": "body",
        "max_bytes": TEXT_MAX_BYTES,
    },
]


@info.route("/users", methods=["OPTIONS"])
def users_info() -> dict:
    """Отвечает на OPTIONS /users.

    Args:
        None

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"post": users_post}


users_me_get = [
    {
        "name": "requested_data",
        "type": "list",
        "is_required": True,
        "container": "query",
        "structure": [
            _requested_field("nickname"),
            _requested_field("email"),
            _requested_field("name_history"),
            _requested_field("avatar"),
            _requested_field("sub_tags"),
            _requested_field("blocked_tags"),
            _requested_field("sub_users"),
            _requested_field("blocked_users"),
            _requested_field("description"),
            _requested_field("creation_date"),
            _requested_field("rating"),
        ],
    },
]

users_me_patch = [
    {
        "name": "nickname",
        "type": "str",
        "is_required": False,
        "container": "body",
        **_NICKNAME_RULES,
    },
    {
        "name": "email",
        "type": "str",
        "is_required": False,
        "container": "body",
        **_EMAIL_RULES,
    },
    {
        "name": "avatar",
        "type": "str",
        "is_required": False,
        "container": "body",
        **_AVATAR_RULES,
    },
    {
        "name": "description",
        "type": "str",
        "is_required": False,
        "container": "body",
        "max_bytes": TEXT_MAX_BYTES,
    },
    {
        "name": "sub-tags",
        "type": "list",
        "is_required": False,
        "container": "body",
        **_TAG_ITEM_RULES,
    },
    {
        "name": "blocked-tags",
        "type": "list",
        "is_required": False,
        "container": "body",
        **_TAG_ITEM_RULES,
    },
    {
        "name": "sub-users",
        "type": "list",
        "is_required": False,
        "container": "body",
        "item_type": "str",
    },
    {
        "name": "blocked-users",
        "type": "list",
        "is_required": False,
        "container": "body",
        "item_type": "str",
    },
]


users_me_delete = [
    {"name": "password", "type": "str", "is_required": True, "container": "body"},
]


@info.route("/users/me", methods=["OPTIONS"])
def users_me_info() -> dict:
    """Отвечает на OPTIONS /users/me.

    Args:
        None

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"get": users_me_get, "patch": users_me_patch, "delete": users_me_delete}


users_me_password_put = [
    {
        "name": "previous_password",
        "type": "str",
        "is_required": True,
        "container": "body",
    },
    {
        "name": "new_password",
        "type": "str",
        "is_required": True,
        "container": "body",
        **_NEW_PASSWORD_RULES,
    },
]


@info.route("/users/me/password", methods=["OPTIONS"])
def users_me_password_info() -> dict:
    """Отвечает на OPTIONS /users/me/password.

    Args:
        None

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"put": users_me_password_put}


auth_login_post = [
    {"name": "username", "type": "str", "is_required": False, "container": "body"},
    {"name": "email", "type": "str", "is_required": False, "container": "body"},
    {"name": "password", "type": "str", "is_required": True, "container": "body"},
]


@info.route("/auth/login", methods=["OPTIONS"])
def auth_login_info() -> dict:
    """Отвечает на OPTIONS /auth/login.

    Args:
        None

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"post": auth_login_post}


auth_refresh_post = [
    {"name": "refresh_token", "type": "str", "is_required": True, "container": "body"},
]


@info.route("/auth/refresh", methods=["OPTIONS"])
def auth_refresh_info() -> dict:
    """Отвечает на OPTIONS /auth/refresh.

    Args:
        None

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"post": auth_refresh_post}


auth_logout_post = [
    {"name": "refresh_token", "type": "str", "is_required": True, "container": "body"},
]


@info.route("/auth/logout", methods=["OPTIONS"])
def auth_logout_info() -> dict:
    """Отвечает на OPTIONS /auth/logout.

    Args:
        None

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"post": auth_logout_post}


@info.route("/auth/logout-all", methods=["OPTIONS"])
def auth_logout_all_info() -> dict:
    """Отвечает на OPTIONS /auth/logout-all.

    Args:
        None

    Returns:
        Словарь со схемами полей методов этого пути.
    """
    return {"post": []}

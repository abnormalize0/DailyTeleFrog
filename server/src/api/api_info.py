'''
Этот файл служит для хранения API методов, которые возвращают структуру входных данных.
Для каждого пути, по которому сервер принимает запросы должен быть свой API метод.
API методы обязаны обрабатывать запросы типа OPTIONS, так как это поведение используется в тестах.
Название методов формируется следубщим образом: %METHOD_NAME%_info. %METHOD_NAME% такой же как и в /server/src/api.py
Таким образом имена не будут дублироваться для одних и тех же путей.
'''

import json
from flask import Blueprint

info = Blueprint('info', __name__)

@info.route('/article', methods=['OPTIONS'])
def article_info():
    request_post = [
        {
            'name': 'user-id',
            'type': 'int',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'article-body',
            'type': 'json',
            'is_required': True,
            'container': 'body',
            'structure': []
        },
        {
            'name': 'preview-content',
            'type': 'json',
            'is_required': True,
            'container': 'body',
            'structure': []
        },
        {
            'name': 'name',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        },
        {
            'name': 'tags',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        },
    ]

    request_get = [
        {
            'name': 'article-id',
            'type': 'int',
            'is_required': True,
            'container': 'header'
        }
    ]

    return json.dumps({'post': request_post,
                       'get': request_get})

@info.route('/article/data', methods=['OPTIONS'])
def article_data_info():
    request_post = [
        {
            'name': 'user-id',
            'type': 'int',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'article-id',
            'type': 'int',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'like-article',
            'type': 'json',
            'is_required': False,
            'container': 'body',
            'structure': []
        },
        {
            'name': 'dislike-article',
            'type': 'json',
            'is_required': False,
            'container': 'body',
            'structure': []
        },
        {
            'name': 'like-comment',
            'type': 'json',
            'is_required': False,
            'container': 'body',
            'structure': [
                {
                    'name': 'comment_id',
                    'type': 'int',
                    'is_required': True
                }
            ]
        },
        {
            'name': 'dislike-comment',
            'type': 'json',
            'is_required': False,
            'container': 'body',
            'structure': [
                {
                    'name': 'comment_id',
                    'type': 'int',
                    'is_required': True
                }
            ]
        },
        {
            'name': 'add-comment',
            'type': 'json',
            'is_required': False,
            'container': 'body',
            'structure': [
                {
                    'name': 'root',
                    'type': 'int',
                    'is_required': True
                },
                {
                    'name': 'text',
                    'type': 'str',
                    'is_required': True
                }
            ]
        }
    ]

    request_get = [
        {
            'name': 'article-id',
            'type': 'int',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'requested-data',
            'type': 'list',
            'is_required': True,
            'container': 'header',
            'structure': [
                {
                    'name': 'likes_count',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'likes_id',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'dislikes_count',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'dislikes_id',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'comments_count',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'creation_date',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'rating',
                    'type': 'field',
                    'is_required': False,
                }
            ]
        }
    ]

    return json.dumps({'post': request_post,
                       'get': request_get})


@info.route('/pages', methods=['OPTIONS'])
def pages_info():
    request_post = []

    request_get = [
        {
            'name': 'user-id',
            'type': 'int',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'indexes',
            'type': 'list_of_int',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'include-nonsub',
            'type': 'bool',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'sort-column',
            'type': 'str',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'sort-direction',
            'type': 'str',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'upper-date',
            'type': 'date',
            'is_required': False,
            'container': 'header'
        },
        {
            'name': 'lower-date',
            'type': 'date',
            'is_required': False,
            'container': 'header'
        },
        {
            'name': 'upper-rating',
            'type': 'int',
            'is_required': False,
            'container': 'header'
        },
        {
            'name': 'lower-rating',
            'type': 'int',
            'is_required': False,
            'container': 'header'
        },
        {
            'name': 'include-tags',
            'type': 'list',
            'is_required': False,
            'container': 'header',
            'structure': []
        },
        {
            'name': 'exclude-tags',
            'type': 'list',
            'is_required': False,
            'container': 'header',
            'structure': []
        },
        {
            'name': 'include-authors',
            'type': 'list',
            'is_required': False,
            'container': 'header',
            'structure': []
        },
        {
            'name': 'exclude-authors',
            'type': 'list',
            'is_required': False,
            'container': 'header',
            'structure': []
        },
        {
            'name': 'include-communities',
            'type': 'list',
            'is_required': False,
            'container': 'header',
            'structure': []
        },
        {
            'name': 'exclude-communities',
            'type': 'list',
            'is_required': False,
            'container': 'header',
            'structure': []
        },
    ]

    return json.dumps({'post': request_post,
                       'get': request_get})

@info.route('/users', methods=['OPTIONS'])
def users_info():
    request_post = [
        {
            'name': 'username',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        },
        {
            'name': 'nickname',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        },
        {
            'name': 'email',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        },
        {
            'name': 'password',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        },
        {
            'name': 'avatar',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        },
        {
            'name': 'sub-tags',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'blocked-tags',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'sub-authors',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'blocked-authors',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'sub-communities',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'blocked-communities',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'description',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        }
    ]

    request_get = []

    return json.dumps({'post': request_post,
                       'get': request_get})

@info.route('/users/data', methods=['OPTIONS'])
def users_data_info():
    request_post = [
        {
            'name': 'user-id',
            'type': 'str',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'nickname',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        },
        {
            'name': 'email',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        },
        {
            'name': 'avatar',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        },
        {
            'name': 'sub-tags',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'blocked-tags',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'sub-users',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'blocked-users',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'sub-communities',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'blocked-communities',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'description',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        }
    ]

    request_get = [
        {
            'name': 'user-id',
            'type': 'str',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'requested-data',
            'type': 'list',
            'is_required': True,
            'container': 'header',
            'structure': [
                {
                    'name': 'nickname',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'email',
                    'type': 'str',
                    'is_required': False,
                },
                {
                    'name': 'name_history',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'avatar',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'sub_tags',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body',
                },
                {
                    'name': 'blocked_tags',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body',
                },
                {
                    'name': 'sub_authors',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body',
                },
                {
                    'name': 'blocked_authors',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body',
                },
                {
                    'name': 'sub_communities',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body',
                },
                {
                    'name': 'blocked_communities',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body',
                },
                {
                    'name': 'description',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'creation_date',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'rating',
                    'type': 'field',
                    'is_required': False,
                }
            ]
        }
    ]

    return json.dumps({'post': request_post,
                       'get': request_get})


@info.route('/users/password', methods=['OPTIONS'])
def users_password_info():
    request_post = [
        {
            'name': 'user-id',
            'type': 'int',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'previous-password',
            'type': 'str',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'new-password',
            'type': 'str',
            'is_required': True,
            'container': 'body'
        }
    ]

    request_get = []

    return json.dumps({'post': request_post,
                       'get': request_get})

@info.route('/login', methods=['OPTIONS'])
def login_info():
    request_post = []

    request_get = [
        {
            'name': 'user-id',
            'type': 'str',
            'is_required': False,
            'container': 'header',
        },
        {
            'name': 'email',
            'type': 'str',
            'is_required': False,
            'container': 'header',
        },
        {
            'name': 'password',
            'type': 'str',
            'is_required': True,
            'container': 'header',
        }
    ]

    return json.dumps({'post': request_post,
                       'get': request_get})
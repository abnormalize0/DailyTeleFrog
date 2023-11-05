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
        {
            'name': 'created',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        }
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
    ]

    return json.dumps({'post': request_post,
                       'get': request_get})

@info.route('/users', methods=['OPTIONS'])
def users_info():
    request_post = [
        {
            'name': 'name',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        },
        {
            'name': 'password',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        },
        {
            'name': 'page',
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
            'name': 'blocked-tags',
            'type': 'str',
            'is_required': False,
            'container': 'body',
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
            'type': 'int',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'name',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        },
        {
            'name': 'page',
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
            'name': 'blocked-tags',
            'type': 'str',
            'is_required': False,
            'container': 'body',
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
                    'name': 'name',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'page',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'avatar',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'blocked_tags',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'description',
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
            'type': 'int',
            'is_required': True,
            'container': 'header'
        },
        {
            'name': 'password',
            'type': 'str',
            'is_required': True,
            'container': 'header'
        }
    ]

    return json.dumps({'post': request_post,
                       'get': request_get})
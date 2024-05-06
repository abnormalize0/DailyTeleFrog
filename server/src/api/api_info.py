'''
Этот файл служит для хранения API методов, которые возвращают структуру входных данных.
Для каждого пути, по которому сервер принимает запросы должен быть свой API метод.
API методы обязаны обрабатывать запросы типа OPTIONS, так как это поведение используется в тестах.
Название методов формируется следующим образом: %METHOD_NAME%_info. %METHOD_NAME% такой же как и в /server/src/api.py
Таким образом имена не будут дублироваться для одних и тех же путей.
'''

import json
from flask import Blueprint

info = Blueprint('info', __name__)

type_defaults = {
    'int': None,
    'str': '',
    'json': {},
    'list': [],
}

article_post = [
        {
            'name': 'username',
            'type': 'str',
            'is_required': True,
            'container': 'body'
        },
        {
            'name': 'body',
            'type': 'dict',
            'is_required': True,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'preview',
            'type': 'dict',
            'is_required': True,
            'container': 'body',
            'structure': [],
        },
        {
            'name': 'title',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        },
        {
            'name': 'tags',
            'type': 'list',
            'is_required': False,
            'container': 'body',
            'structure': [],
        },
    ]

article_get = [
        {
            'name': 'username',
            'type': 'str',
            'is_required': True,
            'container': 'body'
        },
        {
            'name': 'article_id',
            'type': 'int',
            'is_required': True,
            'container': 'body'
        }
    ]


@info.route('/article', methods=['OPTIONS'])
def article_info():
    return json.dumps({'post': article_post,
                       'get': article_get})

article_data_post = [
        {
            'name': 'username',
            'type': 'str',
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

article_data_get = [
        {
            'name': 'username',
            'type': 'str',
            'is_required': True,
            'container': 'body'
        },
        {
            'name': 'article_id',
            'type': 'int',
            'is_required': True,
            'container': 'body'
        },
        {
            'name': 'requested_data',
            'type': 'list',
            'is_required': True,
            'container': 'body',
            'structure': [
                {
                    'name': 'likes',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body'
                },
                {
                    'name': 'dislikes',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body'
                },
                {
                    'name': 'rating',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body'
                },
                {
                    'name': 'comments_count',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body'
                },
                {
                    'name': 'creation_date',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body'
                },
                {
                    'name': 'is_liked',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body'
                },
                {
                    'name': 'is_disliked',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body'
                },
                {
                    'name': 'open_count',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body'
                },
                {
                    'name': 'views_count',
                    'type': 'field',
                    'is_required': False,
                    'container': 'body'
                },
            ]
        }
    ]

@info.route('/article/data', methods=['OPTIONS'])
def article_data_info():
    return json.dumps({'post': article_data_post,
                       'get': article_data_get})

pages_post = []

pages_get = [
        {
            'name': 'username',
            'type': 'str',
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

@info.route('/pages', methods=['OPTIONS'])
def pages_info():
    return json.dumps({'post': pages_post,
                       'get': pages_get})

users_post = [
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
            'name': 'description',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        }
    ]

users_get = []

@info.route('/users', methods=['OPTIONS'])
def users_info():

    return json.dumps({'post': users_post,
                       'get': users_get})

users_data_post = [
        {
            'name': 'username',
            'type': 'str',
            'is_required': True,
            'container': 'body'
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
            'name': 'description',
            'type': 'str',
            'is_required': False,
            'container': 'body',
        }
    ]

users_data_get = [
        {
            'name': 'username',
            'type': 'str',
            'is_required': True,
            'container': 'body'
        },
        {
            'name': 'requested-data',
            'type': 'list',
            'is_required': True,
            'container': 'body',
            'structure': [
                {
                    'name': 'nickname',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'email',
                    'type': 'field',
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
                },
                {
                    'name': 'blocked_tags',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'sub_authors',
                    'type': 'field',
                    'is_required': False,
                },
                {
                    'name': 'blocked_authors',
                    'type': 'field',
                    'is_required': False,
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

@info.route('/users/data', methods=['OPTIONS'])
def users_data_info():
    return json.dumps({'post': users_data_post,
                       'get': users_data_get})


user_password_post = [
        {
            'name': 'username',
            'type': 'str',
            'is_required': True,
            'container': 'body'
        },
        {
            'name': 'previous_password',
            'type': 'str',
            'is_required': True,
            'container': 'body'
        },
        {
            'name': 'new_password',
            'type': 'str',
            'is_required': True,
            'container': 'body'
        }
    ]

user_password_get = []

@info.route('/users/password', methods=['OPTIONS'])
def users_password_info():
    return json.dumps({'post': user_password_post,
                       'get': user_password_get})

login_post = []

login_get = [
        {
            'name': 'username',
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
            'name': 'password',
            'type': 'str',
            'is_required': True,
            'container': 'body',
        }
    ]

@info.route('/login', methods=['OPTIONS'])
def login_info():
    return json.dumps({'post': login_post,
                       'get': login_get})
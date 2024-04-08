'''
Этот файл служит для хранения данных и методов, которые могут использованы во многих тестах.
'''

import unittest
import requests
import json

class BaseTest(unittest.TestCase):
    workdir = 'test_tmp'
    localhost = 'http://127.0.0.1:5000'
    user_count = 0

    default_values = {
        'int': 1,
        'str': 'qwerty',
        'json': {'key': 'value'},
        'list_of_int': '~1~2~3~',
        'bool': 'true',
        'date': '1-1-2024'
    }

    wrong_values = {
        'int': 'f',
        'str': '',
        'json': '{["str"}]',
        'list_of_int': '',
        'list': '',
        'bool': 'hehe',
        'date': '1.1.2024'
    }

    def setUp(self):
        return

    def tearDown(self):
        return

    def add_user(self, **kwargs):
        username = f'tester_username_{self.user_count}'
        nickname = f'tester_nickname_{self.user_count}'
        password = 'qwerty'
        email = f'test_{self.user_count}@test.test'
        answer = requests.post(self.localhost+'/users', json={'username': username,
                                                              'nickname': nickname,
                                                              'password': password,
                                                              'email': email})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.user_count += 1
        return (username, password, nickname, email)

    def add_arcticle(self, **kwargs):
        article = {'name': 'test_name',
                   'preview-content': {'type': 'image', 'data': 'ref'},
                   'tags': '~tag1~tag2~',
                   'article-body': {'block1': 'text'}
        }
        response = requests.post(self.localhost+'/article',
                                 headers={'user-id': str(kwargs['user_id'])},
                                 json=article)
        self.assertEqual(response.json()['status']['type'], 'OK', msg=response.json()['status'])
        return response.json()['article_id']
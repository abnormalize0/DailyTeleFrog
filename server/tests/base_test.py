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
        'list_of_int': '~1~2~3~'
    }

    wrong_values = {
        'int': 'f',
        'str': '',
        'json': '{["str"}]',
        'list_of_int': '',
        'list': ''
    }

    def setUp(self):
        return

    def tearDown(self):
        return

    def add_user(self, **kwargs):
        name = f'tester_{self.user_count}'
        password = 'qwerty'
        answer = requests.post(self.localhost+'/users', json={'name': name,
                                                              'password': password})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.user_count += 1
        return self.user_count, password, name

    def add_arcticle(self, **kwargs):
        article = {'name': 'test_name',
                   'preview-content': {'type': 'image', 'data': 'ref'},
                   'tags': ['test_tag_1', 'test_tag_2'],
                   'created': '01.01.2000',
                   'article-body': {'block1': 'text'}
        }
        response = requests.post(self.localhost+'/article',
                                 headers={'user-id': str(kwargs['user_id'])},
                                 json=article)
        self.assertEqual(response.json()['status']['type'], 'OK', msg=response.json()['status'])
        return response.json()['article_id']
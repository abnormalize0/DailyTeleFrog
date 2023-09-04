import unittest
import requests
import json
import os

class BaseTest(unittest.TestCase):
    workdir = 'test_tmp'
    user_db_filepath = os.path.join(workdir, 'users')
    article_db_filepath = os.path.join(workdir, 'articles')
    comments_db_filepath = os.path.join(workdir, 'comments')
    localhost = 'http://127.0.0.1:5000'
    user_count = 0

    def setUp(self):
        return

    def tearDown(self):
        return

    def add_user(self, **kwargs):
        password = 'qwerty'
        user_info = {'name': 'test_name_' + str(self.user_count),
                     'password': password}
        self.user_count += 1
        headers={'user-info': json.dumps(user_info)}
        requests.post(self.localhost+'/users/new', headers=headers)
        return self.user_count, password

    def add_arcticle(self, **kwargs):
        article = {'name': 'test_name',
                   'preview_content': {'type': 'image', 'data': 'ref'},
                   'tags': ['test_tag_1', 'test_tag_2'],
                   'created': '01.01.2000'
        }
        response = requests.post(self.localhost+'/article', headers={'user-id': str(kwargs['user_id']),
                                                                     'article': json.dumps(article)})
        return response.json()['article-id']
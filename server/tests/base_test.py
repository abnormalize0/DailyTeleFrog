import unittest
import requests
import json
import os

class BaseTest(unittest.TestCase):
    workdir = 'test_tmp'
    user_db_filepath = os.path.join(workdir, 'users')
    article_db_filepath = os.path.join(workdir, 'articles')
    localhost = 'http://127.0.0.1:5000'
    user_count = 0

    def setUp(self):
        return
    
    def tearDown(self):
        return

    def add_user(self, **kwargs):
        password = 'qwerty'
        user_info = {'name': 'test_name_' + str(self.user_count),
                     'password': 'password'}
        self.user_count += 1
        requests.post(self.localhost+'/users/new', headers={'user-info': json.dumps(user_info)})
        return self.user_count, password
    
    def add_arcticle(self, **kwargs):
        article = {'name': 'test_name',
                   'preview_content': {'type': 'png', 'data': 'test_data'},
                   'tags': ['test_tag_1', 'test_tag_2'],
                   'date': '01.01.2000'
        }
        response = requests.post(self.localhost+'/article', headers={'user-id': str(kwargs['user_id']),
                                                                     'article': json.dumps(article)})
        return response.json()['article_id']
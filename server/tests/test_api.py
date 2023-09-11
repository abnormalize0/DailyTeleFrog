import os
import requests
import subprocess
import shutil
import signal
import json
import re

import base_test

class TestAPI(base_test.BaseTest):

    server = None

    def setUp(self):
        if os.path.exists(self.workdir):
            pid_file = open(os.path.join(self.workdir, 'lastpid.txt'), 'r')
            pid = pid_file.readline()
            os.kill(int(pid), signal.SIGKILL)
            shutil.rmtree(self.workdir, ignore_errors=True)

        self.server = subprocess.Popen(['python3', '../start.py', '-i',
                        '--user-db-filepath', self.user_db_filepath,
                        '--articles-db-filepath', self.article_db_filepath,
                        '--comments-db-filepath', self.comments_db_filepath,
                        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while True:
            nextline = self.server.stdout.readline()
            if nextline:
                break

        pid_file = open(os.path.join(self.workdir, 'lastpid.txt'), 'w+')
        pid_file.write(str(self.server.pid))

    def tearDown(self):
        self.server.terminate()
        for line in self.server.stderr:
            print(line.decode('utf8'))
        shutil.rmtree(self.workdir, ignore_errors=True)

    def check_structure(self, adress, required_headers, structure, structure_name):
        # wrong structure
        for key in list(structure.keys()):
            value = structure.pop(key)
            required_headers[structure_name] = json.dumps(structure)
            answer = requests.post(adress, headers=required_headers)
            self.assertEqual(answer.json()['status']['type'], 'ERROR',
                             msg='Error not raised when {0} key is missed'.format(key))
            self.assertEqual(answer.json()['status']['error_type'], 'OptionError',
                             msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                         answer.json()['status']['message']))
            structure[key] = value

        # wrong value in correct structure
        for key in list(structure.keys()):
            value = structure[key]
            structure[key] = None
            required_headers[structure_name] = json.dumps(structure)
            answer = requests.post(adress, headers=required_headers)
            self.assertEqual(answer.json()['status']['type'], 'ERROR',
                             msg='Error not raised when "{0}" key value is None'.format(key))
            self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                             msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                         answer.json()['status']['message']))
            structure[key] = value

    def check_no_headers(self, endpoint, request_type):
        # no headers
        if request_type == 'get':
            answer = requests.get(self.localhost + endpoint, headers={})
        else:
            answer = requests.post(self.localhost + endpoint, headers={})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'OptionError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_article_get(self):
        endpoint = '/article'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertIn('article', answer.json()['article'].keys())
        self.assertIn('preview_content', answer.json()['article'].keys())
        self.assertIn('author_preview', answer.json()['article'].keys())
        self.assertIn('answers', answer.json()['article'].keys())
        self.assertIn('likes_count', answer.json()['article'].keys())
        self.assertIn('likes_id', answer.json()['article'].keys())
        self.assertIn('comments_count', answer.json()['article'].keys())
        self.assertIn('tags', answer.json()['article'].keys())
        self.assertIn('created', answer.json()['article'].keys())

        # no headers
        self.check_no_headers(endpoint, 'get')

        # article-id have string value
        answer = requests.get(self.localhost + endpoint, headers={'article-id': 'hehe'})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_article_post(self):
        endpoint = '/article'
        user_id, password = self.add_user()
        article = {'name': 'test_name',
                   'preview_content': {'type': 'image', 'data': 'ref'},
                   'tags': '~tag1~tag2~tag3~',
                   'created': '01.01.2000',
                   'article': {'block1': 'text'}
        }

        # happy path
        answer = requests.post(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                     'article': json.dumps(article)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        # no headers
        self.check_no_headers(endpoint, 'post')

        # headers with wrong value
        answer = requests.post(self.localhost + endpoint, headers={'user-id': 'hehe', 'article': 'hehe'})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

        self.check_structure(self.localhost + endpoint, {'user-id': str(user_id)}, article, 'article')

    def test_pages(self):
        endpoint = '/pages'
        user_id, password = self.add_user()
        for i in range(20):
            article_id = self.add_arcticle(user_id=user_id)

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id), 'indexes': '~0~1~2~'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        # no headers
        self.check_no_headers(endpoint, 'get')

        # headers with wrong value
        answer = requests.get(self.localhost + endpoint, headers={'user-id': 'hehe', 'indexes': '~0~1~2~'})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))
        
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id), 'indexes': '~hehe~1~2~'})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_article_likes_comments(self):
        endpoint = '/article/likes_comments'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        # no headers
        self.check_no_headers(endpoint, 'get')

        # headers with wrong value
        answer = requests.get(self.localhost + endpoint, headers={'article-id': 'hehe'})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_user_new(self):
        endpoint = '/users/new'
        user_info = {'name': 'test_name_1',
                     'password': 'qwerty',
                     'page': 'page_link',
                     'avatar': 'avatar_link',
                     'blocked_tags': '~tag1~tag2~tag3~'}

        # happy path
        answer = requests.post(self.localhost + endpoint, headers={'user-info': json.dumps(user_info)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        # no headers
        self.check_no_headers(endpoint, 'post')

        user_info = {'name': 'test_name_2',
                     'password': 'qwerty'}
        self.check_structure(self.localhost + endpoint, {}, user_info, 'user-info')

    def test_user_update(self):
        endpoint = '/users/update'
        user_id, password = self.add_user()
        user_info = {'avatar': 'new_avatar_link',
                     'page': 'new_page_link',
                     'blocked_tags': '~tag0~tag8~'}

        # happy path
        answer = requests.post(self.localhost + endpoint, headers={'user-info': json.dumps(user_info),
                                                                   'user-id': str(user_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        # no headers
        self.check_no_headers(endpoint, 'post')

        # empty user-info
        answer = requests.post(self.localhost + endpoint, headers={'user-info': json.dumps({}),
                                                                   'user-id': str(user_id)})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'OptionError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_user_change_password(self):
        endpoint = '/users/change_password'
        user_id, password = self.add_user()        

        # happy path
        answer = requests.post(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'previous-password': password,
                                                                  'new-password': '1234'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        # no headers
        self.check_no_headers(endpoint, 'post')

        # wrong previous password
        answer = requests.post(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                   'previous-password': password,
                                                                   'new-password': '12345'})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_user_check_password(self):
        endpoint = '/users/check_password'
        user_id, password = self.add_user()

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'password': password})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['is-correct'], True, msg=str(answer.json()['status']))

        # no headers
        self.check_no_headers(endpoint, 'get')

        # wrong password
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'password': 'hehe'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['is-correct'], False, msg=str(answer.json()['status']))

    def test_get_comments_like(self):
        endpoint = '/article/comments/like'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        answer = requests.post(self.localhost + '/article/comments/add', headers={'user-id': str(user_id),
                                                                                  'article-id': str(article_id),
                                                                                  'root': str(-1),
                                                                                  'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        comment_id = answer.json()['comment-id']

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['likes-count'], 1)

        # no headers
        self.check_no_headers(endpoint, 'get')

        # wrong header value
        answer = requests.get(self.localhost + endpoint, headers={'comment-id': 'hehe'})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_like_article(self):
        endpoint = '/article/like'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        for i in range(4):
            answer = requests.post(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                       'article-id': str(article_id)})
            self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        answer = requests.get(self.localhost + '/article/likes_comments',
                              headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['likes-count'], 1)

        # no headers
        self.check_no_headers(endpoint, 'post')

        # wrong header value
        answer = requests.post(self.localhost + endpoint, headers={'user-id': 'hehe',
                                                                  'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_like_comment(self):
        endpoint = '/article/comments/like'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        answer = requests.post(self.localhost + '/article/comments/add', headers={'user-id': str(user_id),
                                                                                  'article-id': str(article_id),
                                                                                  'root': str(-1),
                                                                                  'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        comment_id = answer.json()['comment-id']

        # happy path
        for i in range(4):
            answer = requests.post(self.localhost + endpoint,
                                   headers={'comment-id': str(comment_id), 'user-id': str(user_id)})
            self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        answer = requests.get(self.localhost + endpoint, headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['likes-count'], 1)

        # no headers
        self.check_no_headers(endpoint, 'post')

        # wrong header value
        answer = requests.post(self.localhost + endpoint,
                               headers={'comment-id': 'hehe', 'user-id': str(user_id)})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_post_comment(self):
        endpoint = '/article/comments/add'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        
        # happy path
        answer = requests.post(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                   'article-id': str(article_id),
                                                                   'root': str(-1),
                                                                   'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        # no headers
        self.check_no_headers(endpoint, 'post')

        # wrong header value
        answer = requests.post(self.localhost + endpoint, headers={'user-id': 'hehe',
                                                                   'article-id': str(article_id),
                                                                   'root': str(-1),
                                                                   'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg ='Error type: {0}\nMessage: {1}'.format(answer.json()['status']['error_type'],
                                                                     answer.json()['status']['message']))

    def test_number_of_tests(self):
        api = open('../src/api.py', 'r')
        api_methods_count = 0
        for line in api:
            if re.fullmatch('def api_.*', line.strip()):
                api_methods_count += 1
        api.close()

        api_tests = open('test_api.py', 'r')
        test_methods_count = 0
        for line in api_tests:
            if re.fullmatch('def test_.*', line.strip()):
                test_methods_count += 1

        self.assertEqual(api_methods_count, test_methods_count - 1,
                         'Not all api methods have tests or the test_api file contains extra tests')
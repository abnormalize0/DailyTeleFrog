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
                                        '--working-directory', self.workdir
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

    def check_structure(self, endpoint:str, required_headers:dict, structure:dict, structure_name:str):
        # wrong structure
        for key in list(structure.keys()):
            value = structure.pop(key)
            required_headers[structure_name] = json.dumps(structure)
            answer = requests.post(self.localhost + endpoint, headers=required_headers)
            status_type = answer.json()['status']['type']
            error_type = answer.json()['status']['error_type']
            message = answer.json()['status']['message']
            self.assertEqual(status_type, 'ERROR',
                             msg = f'Error not raised when {key} key is missed')
            self.assertEqual(error_type, 'OptionError',
                             msg = f'Error type: {error_type}\nMessage: {message}')
            structure[key] = value

        # wrong value in correct structure
        for key in list(structure.keys()):
            value = structure[key]
            structure[key] = None
            required_headers[structure_name] = json.dumps(structure)
            answer = requests.post(self.localhost + endpoint, headers=required_headers)
            status_type = answer.json()['status']['type']
            error_type = answer.json()['status']['error_type']
            message = answer.json()['status']['message']
            self.assertEqual(status_type, 'ERROR',
                             msg = f'Error not raised when "{key}" key value is None')
            self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                             msg = f'Error type: {error_type}\nMessage: {message}')
            structure[key] = value

    def check_no_headers(self, endpoint:str, request_type):
        # no headers
        if request_type == 'get':
            answer = requests.get(self.localhost + endpoint, headers={})
        else:
            answer = requests.post(self.localhost + endpoint, headers={})
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(error_type, 'OptionError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

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
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

        self.check_structure(endpoint, {'user-id': str(user_id)}, article, 'article')

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
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')


    def test_article_likes_post(self):
        endpoint = '/article/likes'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        for i in range(3):
            answer = requests.post(self.localhost + '/article/dislikes', headers={'user-id': str(user_id + 1),
                                                                                  'article-id': str(article_id)})
            self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        answer = requests.post(self.localhost + endpoint, headers={'user-id': str(user_id + 1),
                                                                   'article-id': str(article_id)})

        # like must rewrite dislike
        answer = requests.get(self.localhost + '/article/dislikes',
                              headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['dislikes-count'], 0)

        # check like count
        answer = requests.get(self.localhost + endpoint,
                              headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['likes-count'], 1)

        # no headers
        self.check_no_headers(endpoint, 'post')

        # wrong header value
        answer = requests.post(self.localhost + endpoint, headers={'user-id': 'hehe',
                                                                   'article-id': str(article_id)})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_article_likes_get(self):
        endpoint = '/article/likes'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['likes-count'], 0)

        # no headers
        self.check_no_headers(endpoint, 'get')

        # headers with wrong value
        answer = requests.get(self.localhost + endpoint, headers={'article-id': 'hehe'})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_article_dislikes_post(self):
        endpoint = '/article/dislikes'
        user_id, password = self.add_user()
        self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        for i in range(3):
            answer = requests.post(self.localhost + '/article/likes', headers={'user-id': str(user_id + 1),
                                                                               'article-id': str(article_id)})
            self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        answer = requests.post(self.localhost + endpoint, headers={'user-id': str(user_id + 1),
                                                                   'article-id': str(article_id)})

        # dislike must rewrite like
        answer = requests.get(self.localhost + '/article/likes',
                              headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['likes-count'], 0)

        # check dislike count
        answer = requests.get(self.localhost + endpoint,
                              headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['dislikes-count'], 1)

        # no headers
        self.check_no_headers(endpoint, 'post')

        # wrong header value
        answer = requests.post(self.localhost + endpoint, headers={'user-id': 'hehe',
                                                                   'article-id': str(article_id)})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_article_dislikes_get(self):
        endpoint = '/article/dislikes'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['dislikes-count'], 0)

        # no headers
        self.check_no_headers(endpoint, 'get')

        # headers with wrong value
        answer = requests.get(self.localhost + endpoint, headers={'article-id': 'hehe'})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_article_comments_get(self):
        endpoint = '/article/comments'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        # no headers
        self.check_no_headers(endpoint, 'get')

        # headers with wrong value
        answer = requests.get(self.localhost + endpoint, headers={'article-id': 'hehe'})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_article_comments_post(self):
        endpoint = '/article/comments'
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
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_article_comments_likes_post(self):
        endpoint = '/article/comments/likes'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        answer = requests.post(self.localhost + '/article/comments', headers={'user-id': str(user_id),
                                                                              'article-id': str(article_id),
                                                                              'root': str(-1),
                                                                              'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        comment_id = answer.json()['comment-id']

        # happy path
        for i in range(3):
            answer = requests.post(self.localhost + '/article/comments/dislikes',
                                   headers={'comment-id': str(comment_id), 'user-id': str(user_id + 1)})
            self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        answer = requests.post(self.localhost + endpoint,
                                   headers={'comment-id': str(comment_id), 'user-id': str(user_id + 1)})

        # like must rewrite dislike
        answer = requests.get(self.localhost + '/article/comments/dislikes', headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['dislikes-count'], 0)

        # check likes count
        answer = requests.get(self.localhost + endpoint, headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['likes-count'], 1)

        # no headers
        self.check_no_headers(endpoint, 'post')

        # wrong header value
        answer = requests.post(self.localhost + endpoint,
                               headers={'comment-id': 'hehe', 'user-id': str(user_id)})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_article_comments_likes_get(self):
        endpoint = '/article/comments/likes'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        answer = requests.post(self.localhost + '/article/comments', headers={'user-id': str(user_id),
                                                                              'article-id': str(article_id),
                                                                              'root': str(-1),
                                                                              'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        comment_id = answer.json()['comment-id']

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['likes-count'], 0)

        # no headers
        self.check_no_headers(endpoint, 'get')

        # wrong header value
        answer = requests.get(self.localhost + endpoint, headers={'comment-id': 'hehe'})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_article_comments_dislikes_post(self):
        endpoint = '/article/comments/dislikes'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        answer = requests.post(self.localhost + '/article/comments', headers={'user-id': str(user_id),
                                                                              'article-id': str(article_id),
                                                                              'root': str(-1),
                                                                              'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        comment_id = answer.json()['comment-id']

        # happy path
        for i in range(3):
            answer = requests.post(self.localhost + '/article/comments/likes',
                                   headers={'comment-id': str(comment_id), 'user-id': str(user_id + 1)})
            self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        answer = requests.post(self.localhost + endpoint,
                               headers={'comment-id': str(comment_id), 'user-id': str(user_id + 1)})

        # dislike must rewrite like
        answer = requests.get(self.localhost + '/article/comments/likes', headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['likes-count'], 0)

        # check dislikes count
        answer = requests.get(self.localhost + endpoint, headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['dislikes-count'], 1)

        # no headers
        self.check_no_headers(endpoint, 'post')

        # wrong header value
        answer = requests.post(self.localhost + endpoint,
                               headers={'comment-id': 'hehe', 'user-id': str(user_id)})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_article_comments_dislikes_get(self):
        endpoint = '/article/comments/dislikes'
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        answer = requests.post(self.localhost + '/article/comments', headers={'user-id': str(user_id),
                                                                              'article-id': str(article_id),
                                                                              'root': str(-1),
                                                                              'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        comment_id = answer.json()['comment-id']

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['dislikes-count'], 0)

        # no headers
        self.check_no_headers(endpoint, 'get')

        # wrong header value
        answer = requests.get(self.localhost + endpoint, headers={'comment-id': 'hehe'})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

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
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id), 'indexes': '~hehe~1~2~'})
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_users_post(self):
        endpoint = '/users'
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
        self.check_structure(endpoint, {}, user_info, 'user-info')

    def test_users_update_post(self):
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
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'OptionError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_user_password_post(self):
        endpoint = '/users/password'
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
        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR', msg = str(answer.json()['status']))
        self.assertEqual(answer.json()['status']['error_type'], 'ValueError',
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def test_user_password_check_get(self):
        endpoint = '/users/password/check'
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
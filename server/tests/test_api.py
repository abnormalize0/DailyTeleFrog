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

    def test_article_get(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        answer = requests.get(self.localhost + '/article', headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))

    def test_article_post(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

    def test_pages(self):
        user_id, password = self.add_user()
        for i in range(20):
            self.add_arcticle(user_id=user_id)
        answer = requests.get(self.localhost + '/pages', headers={'user-id': str(user_id),
                                                         'indexes': '1,2'})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))

    def test_article_likes_comments(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        answer = requests.get(self.localhost + '/article/likes_comments', headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))

    def test_user_new(self):
        user_id, password = self.add_user()

    def test_user_update(self):
        user_id, password = self.add_user()
        user_info = {'avatar': 'avatar_link'}
        answer = requests.post(self.localhost + '/users/update', headers={'user-info': json.dumps(user_info),
                                                                          'user-id': str(user_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))

    def test_user_change_password(self):
        user_id, password = self.add_user()
        answer = requests.post(self.localhost + '/users/change_password', headers={'user-id': str(user_id),
                                                                                   'previous-password': password,
                                                                                   'new-password': '1234'})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))

    def test_user_check_password(self):
        user_id, password = self.add_user()
        answer = requests.get(self.localhost + '/users/check_password', headers={'user-id': str(user_id),
                                                                                 'password': password,})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))

    def test_get_comments_like(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        answer = requests.post(self.localhost + '/article/comments/add', headers={'user-id': str(user_id),
                                                                                  'article-id': str(article_id),
                                                                                  'root': str(-1),
                                                                                  'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))

        comment_id = answer.json()['comment-id']
        answer = requests.get(self.localhost + '/article/comments/like',
                              headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['likes-count'], 1)

    def test_like_article(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        for i in range(4):
            answer = requests.post(self.localhost + '/article/like', headers={'user-id': str(user_id),
                                                                            'article-id': str(article_id)})
            self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        answer = requests.get(self.localhost + '/article/likes_comments',
                              headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['likes_count'], 1)

    def test_like_comment(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        answer = requests.post(self.localhost + '/article/comments/add', headers={'user-id': str(user_id),
                                                                        'article-id': str(article_id),
                                                                        'root': str(-1),
                                                                        'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))
        comment_id = answer.json()['comment-id']
        for i in range(4):
            answer = requests.post(self.localhost + '/article/comments/like',
                                headers={'comment-id': str(comment_id),
                                            'user-id': str(user_id)})
            self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))
        answer = requests.get(self.localhost + '/article/comments/like',
                              headers={'comment-id': str(comment_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['likes-count'], 1)

    def test_post_comment(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        comment_text = "comment 1"
        answer = requests.post(self.localhost + '/article/comments/add', headers={'user-id': str(user_id),
                                                                                  'article-id': str(article_id),
                                                                                  'root': str(-1),
                                                                                  'text': comment_text})
        self.assertEqual(answer.json()['status']['type'], 'OK',msg=str(answer.json()['status']))

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

        self.assertEqual(api_methods_count + 1, test_methods_count,
                         'Not all api methods have tests or the test_api file contains extra tests')
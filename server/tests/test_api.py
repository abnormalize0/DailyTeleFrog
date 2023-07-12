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
        shutil.rmtree(self.workdir, ignore_errors=True)

    def test_article_get(self):
        login, password = self.add_user()
        article_id = self.add_arcticle(login=login)
        requests.get(self.localhost + '/article', headers={'article-id': str(article_id)})

    def test_article_post(self):
        login, password = self.add_user()
        article_id = self.add_arcticle(login=login)

    def test_pages(self):
        login, password = self.add_user()
        for i in range(20):
            self.add_arcticle(login=login)
        requests.get(self.localhost + '/pages', headers={'login': str(login),
                                                         'indexes': '1,2'})

    def test_article_likes_comments(self):
        login, password = self.add_user()
        article_id = self.add_arcticle(login=login)
        requests.get(self.localhost + '/article/likes_comments', headers={'article-id': str(article_id)})

    def test_user_new(self):
        login, password = self.add_user()

    def test_user_update(self):
        login, password = self.add_user()
        user_info = {'nickname': 'new_name'}
        requests.post(self.localhost + '/users/update', headers={'user-info': json.dumps(user_info)})

    def test_user_change_password(self):
        login, password = self.add_user()
        requests.post(self.localhost + '/users/change_password', headers={'login': str(login),
                                                                 'previous-password': password,
                                                                 'new-password': '1234'})
    
    def test_user_check_password(self):
        login, password = self.add_user()
        requests.get(self.localhost + '/users/check_password', headers={'login': str(login),
                                                                 'password': password,})

    def test_get_comments_like(self):
        login, password = self.add_user()
        article_id = self.add_arcticle(login=login)
        comment_text = "comment 1"
        comment_id = requests.post(self.localhost + '/article/comments/add', headers={'login': str(login),
                                                                        'article-id': str(article_id),
                                                                        'root': str(-1),
                                                                        'text': comment_text})
        comment_id = comment_id.json()['comment-id']
        likes_count = requests.get(self.localhost + '/article/comments/like', 
                                    headers={'comment-id': str(comment_id)})
        self.assertEqual(likes_count.json()['likes-count'], 1, 'Like doesnt work')

    def test_like_article(self):
        login, password = self.add_user()
        article_id = self.add_arcticle(login=login)
        requests.post(self.localhost + '/article/like', headers={'login': str(login),
                                                                 'article-id': str(article_id)})

    def test_like_comment(self):
        login, password = self.add_user()
        article_id = self.add_arcticle(login=login)
        comment_text = "comment 1"
        comment_id = requests.post(self.localhost + '/article/comments/add', headers={'login': str(login),
                                                                        'article-id': str(article_id),
                                                                        'root': str(-1),
                                                                        'text': comment_text})
        comment_id = comment_id.json()['comment-id']
        requests.post(self.localhost + '/article/comments/like', 
                      headers={'comment-id': str(comment_id),
                               'login': str(login)})

    def test_post_comment(self):
        login, password = self.add_user()
        article_id = self.add_arcticle(login=login)
        comment_text = "comment 1"
        requests.post(self.localhost + '/article/comments/add', headers={'login': str(login),
                                                                        'article-id': str(article_id),
                                                                        'root': str(-1),
                                                                        'text': comment_text})

    def test_number_of_tests(self):
        api = open('../src/api.py', 'r')
        api_methods_count = 0
        for line in api:
            if re.fullmatch('def api_.*', line.strip()):\
                api_methods_count += 1
        api.close()

        api_tests = open('test_api.py', 'r')
        test_methods_count = 0
        for line in api_tests:
            if re.fullmatch('def test_.*', line.strip()):
                test_methods_count += 1

        self.assertEqual(api_methods_count + 1, test_methods_count,
                          'Not all api methods have tests or the test_api file contains extra tests')
import os
import requests
import subprocess
import shutil
import signal
import json
import importlib
import sys
import re
import inspect

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
                        ], stdout=subprocess.PIPE)

        while True:
            nextline = self.server.stdout.readline()
            if nextline:
                break

        pid_file = open(os.path.join(self.workdir, 'lastpid.txt'), 'w+')
        pid_file.write(str(self.server.pid))

    def tearDown(self):
        shutil.rmtree(self.workdir, ignore_errors=True)
        self.server.terminate()

    def test_article_get(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        requests.get(self.localhost + '/article', headers={'article_id': str(article_id)})

    def test_article_post(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

    def test_pages(self):
        user_id, password = self.add_user()
        for i in range(20):
            self.add_arcticle(user_id=user_id)
        requests.get(self.localhost + '/pages', headers={'user_id': str(user_id),
                                                         'indexes': '1,2'})

    def test_article_likes_comments(self):
        user_id, password = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        requests.get(self.localhost + '/article/likes_comments', headers={'article_id': str(article_id)})

    def test_user_new(self):
        user_id, password = self.add_user()

    def test_user_update(self):
        user_id, password = self.add_user()
        user_info = {'name': 'new_name'}
        requests.post(self.localhost + '/users/update', headers={'user_info': json.dumps(user_info)})

    def test_user_change_password(self):
        user_id, password = self.add_user()
        requests.post(self.localhost + '/users/change_password', headers={'user_id': str(user_id),
                                                                 'previous_password': password,
                                                                 'new_password': '1234'})
    
    def test_user_check_password(self):
        user_id, password = self.add_user()
        requests.get(self.localhost + '/users/check_password', headers={'user_id': str(user_id),
                                                                 'password': password,})

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
'''
Этот файл служит для хранения тестов на публичные API методы сервера.
Названия для тестов  формируются следующим образом: test_%METHOD_NAME%_%REQUEST_TYPE%.
Префикс test_ обязателен, так как его наличие используется для подсчета тестов.
%METHOD_NAME% и %REQUEST_TYPE% такие же как и в /server/src/api.py
'''

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
        # if server didnt close correctly in previuos attempt then kill it
        if os.path.exists(self.workdir):
            pid_file = open(os.path.join(self.workdir, 'lastpid.txt'), 'r')
            pid = pid_file.readline()
            os.kill(int(pid), signal.SIGKILL)
            shutil.rmtree(self.workdir, ignore_errors=True)

        self.server = subprocess.Popen(['python3', '../start.py', '-i',
                                        '--working-directory', self.workdir
                                        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # wait until server startup
        while True:
            nextline = self.server.stdout.readline()
            if nextline:
                break

        pid_file = open(os.path.join(self.workdir, 'lastpid.txt'), 'w+')
        pid_file.write(str(self.server.pid))

    def tearDown(self):
        self.server.terminate()
        # print all server output
        for line in self.server.stderr:
            print(line.decode('utf8'))
        shutil.rmtree(self.workdir, ignore_errors=True)

    def set_list_value(self, structure):
        result = '~'
        for parameter in structure:
            result += parameter['name'] + '~'
        return result

    def set_values(self, structure:list):
        headers = {}
        for parameter in structure:
            if parameter['type'] == 'json' and parameter['structure']:
                headers[parameter['name']] = self.set_values(parameter['structure'])
            elif parameter['type'] == 'list':
                headers[parameter['name']] = self.set_list_value(parameter['structure'])
            else:
                headers[parameter['name']] = self.default_values[parameter['type']]
        return headers

    def check_excepted_error(self, endpoint, method, headers:dict, body:dict, checked_key, excepted_error):
        request_headers = {}
        for k, v in headers.items():
            # dont dumps str because json.loads(json.dumps({[}])) dont raise value error
            if type(v) is not str:
                request_headers[k] = json.dumps(v)
            else:
                request_headers[k] = v

        if method == 'post':
            answer = requests.post(self.localhost + endpoint, headers=request_headers, json=body)
        else:
            answer = requests.get(self.localhost + endpoint, headers=request_headers, json=body)

        status_type = answer.json()['status']['type']
        error_type = answer.json()['status']['error_type']
        message = answer.json()['status']['message']
        self.assertEqual(status_type, 'ERROR',
                         msg = f'Error not raised for {checked_key} key')
        self.assertEqual(error_type, excepted_error,
                         msg = f'Error type: {error_type}\nMessage: {message}')

    def insert_nested_values(self, structure:dict, position:list, values):
        if not position:
            structure.update(values)
        else:
            next_step = position.pop(0)
            structure[next_step] = self.insert_nested_values(structure[next_step], position, values)
        return structure

    def delete_nested_values(self, structure:dict, position:list):
        if len(position) == 1:
            structure.pop(position[0])
        else:
            next_step = position.pop(0)
            structure[next_step] = self.delete_nested_values(structure[next_step], position)
        return structure

    def update_structure(self, body, headers, position, values, container):
        if container == 'body':
            body = self.insert_nested_values(body, position, values)
        elif container == 'header':
            headers = self.insert_nested_values(headers, position, values)
        return body, headers

    def restore_structure(self, body, headers, position, container):
        if container == 'body':
            body = self.delete_nested_values(body, position)
        elif container == 'header':
            headers = self.delete_nested_values(headers, position)
        return body, headers

    def check_structure(self, endpoint:str, method:str, structure:list,):
        info_body = []
        bodies = {}
        info_headers = []
        headers = {}
        for object in structure:
            match object['container']:
                case 'body':
                    info_body.append(object)
                case 'header':
                    info_headers.append(object)

        if info_body:
            bodies = self.set_values(info_body)
        if info_headers:
            headers = self.set_values(info_headers)

        for i, _ in enumerate(info_body):
            body = info_body.pop(i)
            body_value = bodies.pop(body['name'])
            self.structure_check_step(endpoint, method, body, bodies, headers, [], container='body')
            info_body.insert(i, body)
            bodies[body['name']] = body_value

        for i, _ in enumerate(info_headers):
            header = info_headers.pop(i)
            header_value = headers.pop(header['name'])
            self.structure_check_step(endpoint, method, header, bodies, headers, [], container='header')
            info_headers.insert(i, header)
            headers[header['name']] = header_value

    def structure_check_step(self, endpoint, method, structure:list, body, headers, position, container):
        # set wrong value to header
        values = {structure['name']: self.wrong_values[structure['type']]}
        body, headers = self.update_structure(body, headers, position[:], values, container)

        self.check_excepted_error(endpoint=endpoint,
                                    method=method,
                                    headers=headers,
                                    body=body,
                                    checked_key=structure['name'],
                                    excepted_error='ValueError')

        # restore correct headers
        position.append(structure['name'])
        body, headers = self.restore_structure(body, headers, position[:], container)
        position.pop(-1)

        # missed required header
        if structure['is_required']:
            self.check_excepted_error(endpoint=endpoint,
                                        method=method,
                                        headers=headers,
                                        body=body,
                                        checked_key=structure['name'],
                                        excepted_error='OptionError')

        # check nested structure
        if structure['type'] == 'json' and structure['structure']:
            for i, _ in enumerate(structure['structure']):
                nested_structure = structure['structure'].pop(i)
                values = {structure['name']: self.set_values(structure['structure'])}
                body, headers = self.update_structure(body, headers, position[:], values, container)

                position.append(structure['name'])
                self.structure_check_step(endpoint=endpoint,
                                          method=method,
                                          structure=nested_structure,
                                          body=body,
                                          headers=headers,
                                          position=position, 
                                          container=container)

                body, headers = self.restore_structure(body, headers, position[:], container)
                structure['structure'].insert(i, nested_structure)
                position.pop(-1)

    def test_article_post(self):
        endpoint = '/article'
        method = 'post'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        user_id, password, user_name = self.add_user()
        article = {'name': 'test_name',
                   'preview-content': {'type': 'image', 'data': 'ref'},
                   'tags': '~tag1~tag2~tag3~',
                   'created': '01.01.2000',
                   'article-body': {'block1': 'text'}
        }

        # happy path
        answer = requests.post(self.localhost + endpoint, headers={'user-id': str(user_id)}, json=article)
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

    def test_article_get(self):
        endpoint = '/article'
        method = 'get'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        user_id, password, user_name = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        answer = requests.get(self.localhost + endpoint, headers={'article-id': str(article_id)})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertIn('article_body', answer.json()['article'].keys())
        self.assertIn('preview_content', answer.json()['article'].keys())
        self.assertIn('author_preview', answer.json()['article'].keys())
        self.assertIn('answers', answer.json()['article'].keys())
        self.assertIn('likes_count', answer.json()['article'].keys())
        self.assertIn('likes_id', answer.json()['article'].keys())
        self.assertIn('comments_count', answer.json()['article'].keys())
        self.assertIn('tags', answer.json()['article'].keys())
        self.assertIn('created', answer.json()['article'].keys())

    def test_article_data_post(self):
        endpoint = '/article/data'
        method = 'post'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        user_id, password, user_name = self.add_user()
        _ = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)

        # happy path
        like_article = {}
        dislike_article = {}
        add_comment = {'text': 'Hello, world!', 'root': -1}
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id),
                                        'article-id': str(article_id)},
                               json={'add-comment': add_comment})
        comment_id = answer.json()['comment_id']
        like_comment = {'comment_id': comment_id}
        dislike_comment = {'comment_id': comment_id}

        self.assertEqual(answer.json()['status']['type'], 'OK',
                         msg=str(answer.json()['status']))
        self.assertIn('comment_id', answer.json())

        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'like-article': like_article})

        self.assertEqual(answer.json()['status']['type'], 'OK',
                         msg=str(answer.json()['status']))

        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})

        self.assertEqual(answer.json()['status']['type'], 'OK',
                         msg=str(answer.json()['status']))

        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'like-comment': like_comment})

        self.assertEqual(answer.json()['status']['type'], 'OK',
                         msg=str(answer.json()['status']))

        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'dislike-comment': dislike_comment})

        self.assertEqual(answer.json()['status']['type'], 'OK',
                         msg=str(answer.json()['status']))

        # check like post
        article_id = self.add_arcticle(user_id=user_id)
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'like-article': like_article})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        request_data = '~likes_count~'
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'article-id': str(article_id),
                                                                  'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['data']['likes_count'], 1)

        # check like rewrite like
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'like-article': like_article})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'article-id': str(article_id),
                                                                  'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['data']['likes_count'], 0)

        # check dislike post
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        request_data = '~dislikes_count~'
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'article-id': str(article_id),
                                                                  'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['data']['dislikes_count'], 1)

        # check dislike rewrite dislike
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'article-id': str(article_id),
                                                                  'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['data']['dislikes_count'], 0)

        # check like rewrite dislike
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'like-article': like_article})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        request_data = '~likes_count~dislikes_count~'
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'article-id': str(article_id),
                                                                  'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['data']['likes_count'], 1)
        self.assertEqual(answer.json()['data']['dislikes_count'], 0)

        # check dislike rewrite like
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id + 1),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'article-id': str(article_id),
                                                                  'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        self.assertEqual(answer.json()['data']['likes_count'], 0)
        self.assertEqual(answer.json()['data']['dislikes_count'], 1)

        # check user rating
        user_endpoint = '/users/data'
        user_id, password, user_name = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_id),
                                        'article-id': str(article_id)},
                               json={'add-comment': add_comment})
        request_data = '~rating~'
        comment_id = answer.json()['comment_id']
        like_comment = {'comment_id': comment_id}
        dislike_comment = {'comment_id': comment_id}
        user_2, password, user_name = self.add_user()

        # check that like increase rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'like-article': like_article})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], 1)

        # check that undo like decrease rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'like-article': like_article})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], 0)

        # check that dislike decrease rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], -1)

        # check that undo dislike increase rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], 0)

        # check that like on dislike increase rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], -1)
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'like-article': like_article})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], 1)

         # check that like on dislike increase rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], -1)
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'dislike-article': dislike_article})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], 0)

        # check rating with comments
        # check that like increase rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'like-comment': like_comment})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], 1)

        # check that undo like decrease rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'like-comment': like_comment})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], 0)

        # check that dislike decrease rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'dislike-comment': dislike_comment})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], -1)

        # check that undo dislike increase rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'dislike-comment': dislike_comment})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], 0)

        # check that like on dislike increase rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'dislike-comment': dislike_comment})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], -1)
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'like-comment': like_comment})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], 1)

         # check that like on dislike increase rating
        answer = requests.post(self.localhost + endpoint, 
                               headers={'user-id': str(user_2),
                                        'article-id': str(article_id)},
                               json={'dislike-comment': dislike_comment})
        answer = requests.get(self.localhost + user_endpoint, headers={'user-id': str(user_id),
                                                                      'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['data']['rating'], -1)

    def test_article_data_get(self):
        endpoint = '/article/data'
        method = 'get'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        user_id, password, user_name = self.add_user()
        article_id = self.add_arcticle(user_id=user_id)
        request_data = '~likes_count~likes_id~dislikes_count~dislikes_id~comments_count~'
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'article-id': str(article_id),
                                                                  'requested-data': f'{request_data}'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=answer.json()['status'])
        request_data = request_data.split('~')[1:-1]
        for field in request_data:
            self.assertIn(field, answer.json()['data'])

    def test_pages(self):
        endpoint = '/pages'
        method = 'get'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        user_id, password, user_name = self.add_user()
        for i in range(20):
            article_id = self.add_arcticle(user_id=user_id)

        # happy path
        
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id), 'indexes': '~0~1~2~'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertIn('pages', answer.json())
        self.assertIn('0', answer.json()['pages'])
        self.assertIn('1', answer.json()['pages'])
        self.assertIn('2', answer.json()['pages'])

    def test_users_post(self):
        endpoint = '/users'
        method = 'post'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        name = 'test_name_1'
        password = 'password'
        avatar = 'avatar'
        blocked_tags = '~tag1~tag2~tag3~'

        # happy path
        answer = requests.post(self.localhost + endpoint, json={'name': name,
                                                                'password': password,
                                                                'avatar': avatar,
                                                                'blocked-tags': blocked_tags})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertIn('user-id', answer.json())

        user_id = answer.json()['user-id']
        requested_data = '~name~name_history~avatar~blocked_tags~registration_date~rating~'
        answer = requests.get(self.localhost + '/users/data', headers={'user-id': str(user_id),
                                                                       'requested-data': requested_data})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(name, answer.json()['data']['name'])
        self.assertEqual('~' + name + '~', answer.json()['data']['name_history'])
        self.assertEqual(avatar, answer.json()['data']['avatar'])
        self.assertEqual(blocked_tags, answer.json()['data']['blocked_tags'])
        self.assertEqual(0, answer.json()['data']['rating'])
        self.assertIn('registration_date', answer.json()['data'])

    def test_users_data_get(self):
        endpoint = '/users/data'
        method = 'get'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        user_id, password, user_name = self.add_user()

        # happy path
        requested_data = '~name~name_history~avatar~blocked_tags~registration_date~rating~'
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'requested-data': requested_data})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertIn('name', answer.json()['data'])
        self.assertIn('name_history', answer.json()['data'])
        self.assertIn('avatar', answer.json()['data'])
        self.assertIn('blocked_tags', answer.json()['data'])
        self.assertIn('registration_date', answer.json()['data'])
        self.assertIn('rating', answer.json()['data'])

    def test_users_data_post(self):
        endpoint = '/users/data'
        method = 'post'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        user_id, password, user_name = self.add_user()

        # happy path
        name = 'new_name'
        avatar = 'avatar_link'
        blocked_tags = '~tag1~tag2~'
        answer = requests.post(self.localhost + endpoint,
                               headers={'user-id': str(user_id)},
                               json={'name': name,
                                     'avatar': avatar,
                                     'blocked-tags': blocked_tags})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

        requested_data = '~name~name_history~avatar~blocked_tags~'
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'requested-data': requested_data})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['data']['name'], name)
        self.assertEqual(answer.json()['data']['name_history'], '~' + user_name + '~' + name + '~')
        self.assertEqual(answer.json()['data']['avatar'], avatar)
        self.assertEqual(answer.json()['data']['blocked_tags'], blocked_tags)

    def test_user_password_post(self):
        endpoint = '/users/password'
        method = 'post'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        user_id, password, user_name = self.add_user()

        # happy path
        answer = requests.post(self.localhost + endpoint,
                               headers={'user-id': str(user_id),
                                        'previous-password': password},
                               json={'new-password': '1234'})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))

    def test_login_get(self):
        endpoint = '/login'
        method = 'get'
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(endpoint=endpoint,
                             method=method,
                             structure=answer.json()[method])

        user_id, password, user_name = self.add_user()

        # happy path 
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id),
                                                                  'password': password})
        self.assertEqual(answer.json()['status']['type'], 'OK', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['is-correct'], True, msg=str(answer.json()['status']))

        # special rule: incorrect id return is-correct = False
        answer = requests.get(self.localhost + endpoint, headers={'user-id': str(user_id+1),
                                                                   'password': password})
        self.assertEqual(answer.json()['status']['type'], 'ERROR', msg=str(answer.json()['status']))
        self.assertEqual(answer.json()['is-correct'], False, msg=str(answer.json()['is-correct']))

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
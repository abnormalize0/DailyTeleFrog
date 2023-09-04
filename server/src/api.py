from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys

from . import backend
from . import request_status

app = Flask(__name__)
cors = CORS(app)

def safe_parser(func):
    def wrapper(**kwargs):
        try:
            headers = func(**kwargs)
        except ValueError as err:
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.ValueError,
                                         msg='''Cannot convert {0}
                                         with value {1}
                                         to {2}'''.format(kwargs['header_name'],
                                                          err.args[0].split(':')[-1],
                                                          func.__convert_type__)
                                        ), None
        return request_status.Status(request_status.StatusType.OK), headers
    return wrapper

@safe_parser
def parse_int(**kwargs):
    @property
    def __convert_type__():
        return 'int'
    return int(kwargs['request'].headers.get(kwargs['header_name']))

@safe_parser
def parse_list_of_int(**kwargs):
    @property
    def __convert_type__():
        return 'list of int'
    indexes = kwargs['request'].headers.get(kwargs['header_name'])
    indexes = indexes.split(',')
    indexes = [int(index) for index in indexes]
    return indexes

@safe_parser
def parse_json(**kwargs):
    @property
    def __convert_type__():
        return 'json'
    return json.loads(kwargs['request'].headers.get(kwargs['header_name']))

@safe_parser
def parse_str(**kwargs):
    @property
    def __convert_type__():
        return 'str'
    return str(kwargs['request'].headers.get(kwargs['header_name']))

def parse_headers(request, headers):
    result = {}
    for header_name, value_type in headers.items():
        status = None
        value = None
        match value_type:
            case 'int':
                status, value = parse_int(request=request, header_name=header_name)
            case 'list_of_int':
                status, value = parse_list_of_int(request=request, header_name=header_name)
            case 'json':
                status, value = parse_json(request=request, header_name=header_name)
            case 'str':
                status, value = parse_str(request=request, header_name=header_name)
        if status.is_error:
            return status, None
        result[header_name] = value
    return request_status.Status(request_status.StatusType.OK), result

@app.route('/article', methods=['GET'])
def api_get_article():
    status, headers = parse_headers(request, {'article-id': 'int'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    article = backend.get_article(headers['article-id'])
    return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK)), 'article': article})

@app.route('/article/likes_comments', methods=['GET'])
def api_get_article_likes_comments():
    status, headers = parse_headers(request, {'article-id': 'int'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status, likes_comments = backend.get_article_likes_comments(headers['article-id'])
    return json.dumps({'status': dict(status),
                       'likes_count': likes_comments['likes_count'],
                       'comments_count': likes_comments['comments_count']})

@app.route('/article', methods=['POST'])
def api_post_article():
    status, headers = parse_headers(request, {'article': 'json',
                                              'user-id': 'int'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status, article_id = backend.post_article(headers['article'],
                                              headers['user-id'])
    return json.dumps({'status': dict(status), 'article-id': article_id})

@app.route('/article/like', methods=['POST'])
def api_like_article():
    status, headers = parse_headers(request, {'article-id': 'int',
                                              'user-id': 'int'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status = backend.like_article(headers['article-id'],
                                  headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/article/comments/add', methods=['POST'])
def api_add_comment():
    status, headers = parse_headers(request, {'article-id': 'int',
                                              'user-id': 'int',
                                              'root': 'int',
                                              'text': 'str'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status, id = backend.article_add_comment(headers['article-id'],
                                             headers['root'],
                                             headers['text'],
                                             headers['user-id'])
    return json.dumps({'status': dict(status), 'comment-id': id})

@app.route('/article/comments/like', methods=['POST'])
def api_like_comment():
    status, headers = parse_headers(request, {'comment-id': 'int',
                                              'user-id': 'int'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status = backend.like_comment(headers['comment-id'],
                                  headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/article/comments/like', methods=['GET'])
def api_get_comments_likes():
    status, headers = parse_headers(request, {'comment-id': 'int'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status, likes_count = backend.get_comment_likes(headers['comment-id'])
    return json.dumps({'status': dict(status), 'likes-count': likes_count})

@app.route('/pages', methods=['GET'])
def api_get_pages():
    status, headers = parse_headers(request, {'user-id': 'int',
                                              'indexes': 'list_of_int'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status, pages = backend.get_pages(headers['indexes'],
                                      headers['user-id'])
    return json.dumps({'status': dict(status), 'pages': pages})

@app.route('/users/new', methods=['POST'])
def api_add_user():
    status, headers = parse_headers(request, {'user-info': 'json'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status, user_id = backend.add_user(headers['user-info'])
    return json.dumps({'status': dict(status), 'user-id': user_id})

@app.route('/users/update', methods=['POST'])
def api_update_user_info():
    status, headers = parse_headers(request, {'user-id': 'int',
                                              'user-info': 'json'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status = backend.update_user_info(headers['user-info'],
                                      headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/users/change_password', methods=['POST'])
def api_change_user_password():
    status, headers = parse_headers(request, {'user-id': 'int',
                                              'previous-password': 'str',
                                              'new-password': 'str'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status = backend.change_password(headers['previous-password'],
                                     headers['new-password'],
                                     headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/users/check_password', methods=['GET'])
def api_check_user_password():
    status, headers = parse_headers(request, {'user-id': 'int',
                                              'password': 'str'})
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status, is_password_correct = backend.check_password(headers['password'],
                                                         headers['user-id'])
    return json.dumps({'status': dict(status), 'is_password_correct': is_password_correct})

def run_server():
    print('Running...')
    app.run(host='0.0.0.0', port=5000)
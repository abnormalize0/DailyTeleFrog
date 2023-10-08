from flask import Flask, request
from flask_cors import CORS
import json

from . import backend
from . import request_status
from . import config
from . import log

app = Flask(__name__)
cors = CORS(app)

class Parameter():
    def __init__(self, name:str, parameter_type:str, is_requiered:bool):
        self.name = name
        self.type = parameter_type
        self.is_requiered = is_requiered

def safe_parser(func):
    def wrapper(**kwargs):
        try:
            headers = func(**kwargs)
        except ValueError as err:
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.ValueError,
                                         msg=f'''Cannot convert {kwargs['parameter_name']}
                                         with value {err.args[0].split(':')[-1]}
                                         to {kwargs['convert_type']} or value is forbidden'''), None
        return request_status.Status(request_status.StatusType.OK), headers
    return wrapper

@safe_parser
def parse_int(**kwargs):
    return int(kwargs['headers'].get(kwargs['parameter_name']))

@safe_parser
def parse_list_of_int(**kwargs):
    indexes = kwargs['headers'].get(kwargs['parameter_name'])
    indexes = indexes.split('~')[1:-1]
    indexes = [int(index) for index in indexes]
    return indexes

@safe_parser
def parse_json(**kwargs):
    try:
        result = json.loads(kwargs['headers'].get(kwargs['parameter_name']))
        if result is None:
            raise ValueError(f'Value is None: {result}')
        return result
    except:
        result = kwargs['headers'].get(kwargs['parameter_name'])
        if result is None:
            raise ValueError(f'Value is None: {result}')
        result = json.dumps(result)
        return json.loads(result)


@safe_parser
def parse_str(**kwargs):
    forbidden_values = ['none', 'nan', 'null']
    result = str(kwargs['headers'].get(kwargs['parameter_name']))
    if result.lower() in forbidden_values:
        raise ValueError(f'Cannot convert to string value: {result}')
    return result

def parse_structure(headers, structure:list):
    result = {}
    requested_headers = ''
    parameter:Parameter
    for parameter in structure:
        if parameter.name not in headers and parameter.is_requiered:
            return request_status.Status(request_status.StatusType.ERROR,
                                         request_status.ErrorType.OptionError,
                                         msg = f'Missed required key {parameter.name}'), None
        if parameter.name not in headers:
            requested_headers += parameter.name + ', '
            continue
        status:request_status.Status
        status = None
        value = None
        match parameter.type:
            case 'int':
                status, value = parse_int(headers=headers,
                                          parameter_name=parameter.name,
                                          convert_type='int')
            case 'list_of_int':
                status, value = parse_list_of_int(headers=headers,
                                                  parameter_name=parameter.name,
                                                  convert_type='list of int')
            case 'json':
                status, value = parse_json(headers=headers,
                                           parameter_name=parameter.name,
                                           convert_type='json')
            case 'str':
                status, value = parse_str(headers=headers,
                                          parameter_name=parameter.name,
                                          convert_type='str')
        if status.is_error:
            return status, None
        result[parameter.name] = value

    if not result:
        requested_headers = requested_headers[:-2]
        return request_status.Status(request_status.StatusType.ERROR,
                                     request_status.ErrorType.OptionError,
                                     msg = f'Request doesnt have any of ({requested_headers}) headers'), None

    return request_status.Status(request_status.StatusType.OK), result

@app.route('/article', methods=['POST'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_post():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True),
                                                        Parameter('article', 'json', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, article = parse_structure(headers['article'], [Parameter('article', 'json', True),
                                                           Parameter('preview_content', 'json', True),
                                                           Parameter('name', 'str', True),
                                                           Parameter('tags', 'str', True),
                                                           Parameter('created', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, article_id = backend.post_article(article,
                                              headers['user-id'])
    return json.dumps({'status': dict(status), 'article-id': article_id})

@app.route('/article', methods=['GET'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_get():
    status, headers = parse_structure(request.headers, [Parameter('article-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    article = backend.get_article(headers['article-id'])
    return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK)), 'article': article})

@app.route('/article/likes', methods=['POST'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_likes_post():
    status, headers = parse_structure(request.headers, [Parameter('article-id', 'int', True),
                                                        Parameter('user-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status = backend.like_article(headers['article-id'],
                                  headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/article/likes', methods=['GET'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_likes_get():
    status, headers = parse_structure(request.headers, [Parameter('article-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, likes = backend.get_article_likes(headers['article-id'])
    return json.dumps({'status': dict(status),
                       'likes-count': likes})

@app.route('/article/dislikes', methods=['POST'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_dislike_post():
    status, headers = parse_structure(request.headers, [Parameter('article-id', 'int', True),
                                                        Parameter('user-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status = backend.dislike_article(headers['article-id'],
                                     headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/article/dislikes', methods=['GET'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_dislike_get():
    status, headers = parse_structure(request.headers, [Parameter('article-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, dislikes = backend.get_article_dislikes(headers['article-id'])
    return json.dumps({'status': dict(status),
                       'dislikes-count': dislikes})

@app.route('/article/comments', methods=['POST'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_comments_post():
    status, headers = parse_structure(request.headers, [Parameter('article-id', 'int', True),
                                                        Parameter('user-id', 'int', True),
                                                        Parameter('root', 'int', True),
                                                        Parameter('text', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, id = backend.article_add_comment(headers['article-id'],
                                             headers['root'],
                                             headers['text'],
                                             headers['user-id'])
    return json.dumps({'status': dict(status), 'comment-id': id})

@app.route('/article/comments', methods=['GET'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_comments_get():
    status, headers = parse_structure(request.headers, [Parameter('article-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, comments = backend.get_article_comments(headers['article-id'])
    return json.dumps({'status': dict(status),
                       'comments-count': comments})

@app.route('/article/comments/likes', methods=['POST'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_comments_like_post():
    status, headers = parse_structure(request.headers, [Parameter('comment-id', 'int', True),
                                                        Parameter('user-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status = backend.like_comment(headers['comment-id'],
                                  headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/article/comments/likes', methods=['GET'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_comments_like_get():
    status, headers = parse_structure(request.headers, [Parameter('comment-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, likes_count = backend.get_comment_likes(headers['comment-id'])
    return json.dumps({'status': dict(status), 'likes-count': likes_count})

@app.route('/article/comments/dislikes', methods=['POST'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_comments_dislikes_post():
    status, headers = parse_structure(request.headers, [Parameter('comment-id', 'int', True),
                                                        Parameter('user-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status = backend.dislike_comment(headers['comment-id'],
                                  headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/article/comments/dislikes', methods=['GET'])
@log.log_headers
@log.timer(config.log_server_api)
def api_article_comments_dislikes_get():
    status, headers = parse_structure(request.headers, [Parameter('comment-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, dislike = backend.get_comment_dislikes(headers['comment-id'])
    return json.dumps({'status': dict(status), 'dislikes-count': dislike})

@app.route('/pages', methods=['GET'])
@log.log_headers
@log.timer(config.log_server_api)
def api_pages_get():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True),
                                                        Parameter('indexes', 'list_of_int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, pages = backend.get_pages(headers['indexes'],
                                      headers['user-id'])
    return json.dumps({'status': dict(status), 'pages': pages})

@app.route('/users', methods=['POST'])
@log.log_headers
@log.timer(config.log_server_api)
def api_users_post():
    status, headers = parse_structure(request.headers, [Parameter('user-info', 'json', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, user_info = parse_structure(headers['user-info'], [Parameter('name', 'str', True),
                                                               Parameter('password', 'str', True),
                                                               Parameter('page', 'str', False),
                                                               Parameter('avatar', 'str', False),
                                                               Parameter('blocked_tags', 'str', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, user_id = backend.add_user(user_info)
    return json.dumps({'status': dict(status), 'user-id': user_id})

@app.route('/users/update', methods=['POST'])
@log.log_headers
@log.timer(config.log_server_api)
def api_users_update_post():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True),
                                                        Parameter('user-info', 'json', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, user_info = parse_structure(headers['user-info'], [Parameter('page', 'str', False),
                                                               Parameter('avatar', 'str', False),
                                                               Parameter('blocked_tags', 'str', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status = backend.update_user_info(user_info,
                                      headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/users/password', methods=['POST'])
@log.log_headers
@log.timer(config.log_server_api)
def api_users_password_post():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True),
                                                        Parameter('previous-password', 'str', True),
                                                        Parameter('new-password', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})
    status = backend.change_password(headers['previous-password'],
                                     headers['new-password'],
                                     headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/users/password/check', methods=['GET'])
@log.log_headers
@log.timer(config.log_server_api)
def api_users_password_check_get():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True),
                                                        Parameter('password', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, is_password_correct = backend.check_password(headers['password'],
                                                         headers['user-id'])
    return json.dumps({'status': dict(status), 'is-correct': is_password_correct})

def run_server():
    print('Running...')
    app.run(host='0.0.0.0', port=5000)
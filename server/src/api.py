'''
Этот файл служит для хранения логики предобработки пользовательских запросов.
В предобработку входит проверка необходимых заголовков, параметров запроса и тела запроса при наличии.
В рамках предобработки этих полей выполняется преобразования к необходимым типам данных.

Пометка для добавления нового API метода:
1. Названия методов формируются следующим образом: api_%METHOD_NAME%_%REQUEST_TYPE%
Префикс api_ обрабатывается в тестах, поэтому он обязателен.
Остальная часть названия метода позволяет избежать дублирования названий функций.
2. Для каждого метода должен присутствовать тест в файле /server/test/test_api.py
и ответ на запрос OPTIONS в файле /server/src/api_info.py
3. Каждый запрос должен принимать на вход user-id заголовок.
По договоренности считаем, что в этом заголвке указан автор запроса.
Значение -1 характеризует неавторизванного пользователя.
4. Каждый API метод обязан возвращать статус операции.
5. Последовательность API методов должна быть одинаковой для этого файла, документации, тестов и запросов OPTIONS.
6. Каждый запрос должен быть декорирован таймером и логгированием принимаемых аргументов.
Логгирование аргументов позволит облегчить поиск проблем, когда такие возникнут.
Таймер позволит иметь конкретные значения времени выполнения запроса, что облегчит решение проблем аля "ВСЕ ТОРМОЗИТ!!!"
7. Для API методов типа POST обязательно должно присутсвовать тело запроса.
В этом теле располагаются данные, которые будут добавлены на сервер. Остальные параметры перечислены в заголовках.
'''

from flask import Flask, request
from flask_cors import CORS
import json

from . import backend
from . import request_status
from . import config
from . import log
from . import api_info

app = Flask(__name__)
app.register_blueprint(api_info.info)
cors = CORS(app)

class Parameter():
    def __init__(self, name:str, parameter_type:str, is_required:bool):
        self.name = name
        self.type = parameter_type
        self.is_required = is_required

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
    if not indexes:
        raise ValueError(f'Value is None: {indexes}')
    return indexes

@safe_parser
def parse_json(**kwargs):
    result = kwargs['headers'].get(kwargs['parameter_name'])
    if type(result) is dict:
        return result
    return json.loads(result)

@safe_parser
def parse_str(**kwargs):
    # possible errors converted to string
    forbidden_values = ['none', 'nan', 'null', '']
    result = str(kwargs['headers'].get(kwargs['parameter_name']))
    if result.lower() in forbidden_values:
        raise ValueError(f'Cannot convert to string value: {result}')
    return result

@safe_parser
def parse_list(**kwargs):
    # [], {}, \"\", \'\' converted to str
    forbidden_values = ['"', "'", '[', '{']
    result = kwargs['headers'].get(kwargs['parameter_name'])
    result = result.split('~')[1:-1]
    if not result or result[0] in forbidden_values:
        raise ValueError(f'Cannot convert to list value: {result}')
    return result

def parse_fields(request_part, structure:list):
    skipped = ''
    fields = []
    for parameter in structure:
        parameter:Parameter
        if parameter.name not in request_part:
            skipped += parameter.name + ', '
        else:
            fields.append(parameter.name)
    if not fields:
        skipped = skipped[:-2]
        return request_status.Status(request_status.StatusType.ERROR,
                                     request_status.ErrorType.OptionError,
                                     msg = f'Request doesnt have any of ({skipped}) headers'), None
    return request_status.Status(request_status.StatusType.OK), fields

def parse_structure(request_part:dict, structure:list):
    result = {}
    requested_headers = ''
    parameter:Parameter
    for parameter in structure:
        if parameter.name not in request_part and parameter.is_required:
            return request_status.Status(request_status.StatusType.ERROR,
                                         request_status.ErrorType.OptionError,
                                         msg = f'Missed required key {parameter.name}'), None
        if parameter.name not in request_part:
            requested_headers += parameter.name + ', '
            continue
        status:request_status.Status
        status = None
        value = None
        match parameter.type:
            case 'int':
                status, value = parse_int(headers=request_part,
                                          parameter_name=parameter.name,
                                          convert_type='int')
            case 'list_of_int':
                status, value = parse_list_of_int(headers=request_part,
                                                  parameter_name=parameter.name,
                                                  convert_type='list of int')
            case 'json':
                status, value = parse_json(headers=request_part,
                                           parameter_name=parameter.name,
                                           convert_type='json')
            case 'str':
                status, value = parse_str(headers=request_part,
                                          parameter_name=parameter.name,
                                          convert_type='str')
            case 'list':
                status, value = parse_list(headers=request_part,
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
@log.log_request
@log.timer(config.log_server_api)
def api_article_post():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, article = parse_structure(request.json, [Parameter('article-body', 'json', True),
                                                     Parameter('preview-content', 'json', True),
                                                     Parameter('name', 'str', True),
                                                     Parameter('tags', 'str', True),
                                                     Parameter('created', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    # replace "-" with "_" because field in db named with "_"
    article['article_body'] = article.pop('article-body')
    article['preview_content'] = article.pop('preview-content')

    status, article_id = backend.post_article(article, headers['user-id'])
    return json.dumps({'status': dict(status), 'article-id': article_id})

@app.route('/article', methods=['GET'])
@log.log_request
@log.timer(config.log_server_api)
def api_article_get():
    status, headers = parse_structure(request.headers, [Parameter('article-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    article = backend.get_article(headers['article-id'])
    return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK)), 'article': article})

@app.route('/article/data', methods=['POST'])
@log.log_request
@log.timer(config.log_server_api)
def api_article_data_post():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True),
                                                        Parameter('article-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, command = parse_structure(request.json, [Parameter('like-article', 'json', False),
                                                     Parameter('dislike-article', 'json', False),
                                                     Parameter('like-comment', 'json', False),
                                                     Parameter('dislike-comment', 'json', False),
                                                     Parameter('add-comment', 'json', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    if 'like-comment' in command:
        status, _ = parse_structure(command['like-comment'], [Parameter('comment_id', 'int', True)])
        if status.is_error:
            return json.dumps({'status': dict(status)})

    if 'dislike-comment' in command:
        status, _ = parse_structure(command['dislike-comment'], [Parameter('comment_id', 'int', True)])
        if status.is_error:
            return json.dumps({'status': dict(status)})

    if 'add-comment' in command:
        status, _ = parse_structure(command['add-comment'], [Parameter('root', 'int', True),
                                                             Parameter('text', 'str', True)])
        if status.is_error:
            return json.dumps({'status': dict(status)})

    if 'like-article' in command:
        status = backend.like_article(headers['article-id'], headers['user-id'])
        return json.dumps({'status': dict(status)})

    if 'dislike-article' in command:
        status = backend.dislike_article(headers['article-id'], headers['user-id'])
        return json.dumps({'status': dict(status)})

    if 'like-comment' in command:
        status = backend.like_comment(command['like-comment']['comment_id'], headers['user-id'])
        return json.dumps({'status': dict(status)})

    if 'dislike-comment' in command:
        status = backend.dislike_comment(command['dislike-comment']['comment_id'], headers['user-id'])
        return json.dumps({'status': dict(status)})

    if 'add-comment' in command:
        status, comment_id = backend.add_comment(headers['article-id'],
                                                 command['add-comment']['root'],
                                                 command['add-comment']['text'],
                                                 headers['user-id'])
        return json.dumps({'status': dict(status), 'comment_id': comment_id})

@app.route('/article/data', methods=['GET'])
@log.log_request
@log.timer(config.log_server_api)
def api_article_data_get():
    status, headers = parse_structure(request.headers, [Parameter('article-id', 'int', True),
                                                        Parameter('requested-data', 'list', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, requested_data = parse_fields(headers['requested-data'], [Parameter('likes_count', 'field', False),
                                                                      Parameter('likes_id', 'field', False),
                                                                      Parameter('dislikes_count', 'field', False),
                                                                      Parameter('dislikes_id', 'field', False),
                                                                      Parameter('comments_count', 'field', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, data = backend.get_article_data(headers['article-id'], requested_data)
    return json.dumps({'status': dict(status), 'data': data})

@app.route('/pages', methods=['GET'])
@log.log_request
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
@log.log_request
@log.timer(config.log_server_api)
def api_users_post():
    status, user_info = parse_structure(request.json, [Parameter('name', 'str', True),
                                                       Parameter('password', 'str', True),
                                                       Parameter('avatar', 'str', False),
                                                       Parameter('blocked-tags', 'str', False),
                                                       Parameter('description', 'str', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    # replace "-" with "_" because field in db named with "_"
    if 'blocked-tags' in user_info:
        user_info['blocked_tags'] = user_info.pop('blocked-tags')

    status, user_id = backend.add_user(user_info)
    return json.dumps({'status': dict(status), 'user-id': user_id})

@app.route('/users/data', methods=['GET'])
@log.log_request
@log.timer(config.log_server_api)
def api_users_data_get():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True),
                                                        Parameter('requested-data', 'list', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, requested_data = parse_fields(headers['requested-data'], [Parameter('name_history', 'str', False),
                                                                      Parameter('avatar', 'str', False),
                                                                      Parameter('blocked_tags', 'str', False),
                                                                      Parameter('name', 'str', False),
                                                                      Parameter('description', 'str', False)])

    status, data = backend.get_user_data(headers['user-id'], requested_data)
    return json.dumps({'status': dict(status), 'data': data})

@app.route('/users/data', methods=['POST'])
@log.log_request
@log.timer(config.log_server_api)
def api_users_data_post():
    status, user_id = parse_structure(request.headers, [Parameter('user-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})
    user_id = user_id['user-id']

    status, fields = parse_structure(request.json, [Parameter('avatar', 'str', False),
                                                    Parameter('blocked-tags', 'str', False),
                                                    Parameter('name', 'str', False),
                                                    Parameter('description', 'str', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    # replace "-" with "_" because field in db named with "_"
    if 'blocked-tags' in fields:
        fields['blocked_tags'] = fields.pop('blocked-tags')

    status = backend.update_user_info(fields,
                                      user_id)
    return json.dumps({'status': dict(status)})

@app.route('/users/password', methods=['POST'])
@log.log_request
@log.timer(config.log_server_api)
def api_users_password_post():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True),
                                                        Parameter('previous-password', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, new_password = parse_structure(request.json, [Parameter('new-password', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status = backend.change_password(headers['previous-password'],
                                     new_password['new-password'],
                                     headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/login', methods=['GET'])
@log.log_request
@log.timer(config.log_server_api)
def api_login_get():
    status, headers = parse_structure(request.headers, [Parameter('user-id', 'int', True),
                                                        Parameter('password', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, is_password_correct = backend.login(headers['password'], headers['user-id'])
    return json.dumps({'status': dict(status), 'is-correct': is_password_correct})

def run_server():
    # used in test_api to startup check
    print('Running...')
    app.run(host='0.0.0.0', port=5000)
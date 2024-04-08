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

from .. import backend
from .. import request_status
from .. import config
from .. import log
from . import api_info
from . import api_types

app = Flask(__name__)
app.register_blueprint(api_info.info)
cors = CORS(app)


@app.route('/article', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_post():
    status, headers = api_types.parse_structure(request.headers, [api_types.Parameter('user-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    if headers['user-id'] == 0:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})

    status, article = api_types.parse_structure(request.json, [api_types.Parameter('article-body', 'json', True),
                                                               api_types.Parameter('preview-content', 'json', True),
                                                               api_types.Parameter('name', 'str', True),
                                                               api_types.Parameter('tags', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    # replace "-" with "_" because field in db named with "_"
    article['article_body'] = article.pop('article-body')
    article['preview_content'] = article.pop('preview-content')

    status, article_id = backend.post_article(article, headers['user-id'])
    return json.dumps({'status': dict(status), 'article_id': article_id})

@app.route('/article', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_get():
    status, headers = api_types.parse_structure(request.headers, [api_types.Parameter('article-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    article = backend.get_article(headers['article-id'])
    if not article:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                                                error_type=request_status.ErrorType.ValueError,
                                                                msg=f"Article does not exist"))})
    return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK)), 'article': article})

@app.route('/article/data', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_data_post():
    status, headers = api_types.parse_structure(request.headers, [api_types.Parameter('user-id', 'int', True),
                                                                  api_types.Parameter('article-id', 'int', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    if headers['user-id'] == 0:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})

    status, command = api_types.parse_structure(request.json, [api_types.Parameter('like-article', 'json', False),
                                                               api_types.Parameter('dislike-article', 'json', False),
                                                               api_types.Parameter('like-comment', 'json', False),
                                                               api_types.Parameter('dislike-comment', 'json', False),
                                                               api_types.Parameter('add-comment', 'json', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    if 'like-comment' in command:
        status, _ = api_types.parse_structure(command['like-comment'], [api_types.Parameter('comment_id', 'int', True)])
        if status.is_error:
            return json.dumps({'status': dict(status)})

    if 'dislike-comment' in command:
        status, _ = api_types.parse_structure(command['dislike-comment'],
                                              [api_types.Parameter('comment_id', 'int', True)])
        if status.is_error:
            return json.dumps({'status': dict(status)})

    if 'add-comment' in command:
        status, _ = api_types.parse_structure(command['add-comment'], [api_types.Parameter('root', 'int', True),
                                                                       api_types.Parameter('text', 'str', True)])
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
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_data_get():
    status, headers = api_types.parse_structure(request.headers, [api_types.Parameter('article-id', 'int', True),
                                                                  api_types.Parameter('requested-data', 'list', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, requested_data = api_types.parse_fields(headers['requested-data'],
                                                    [api_types.Parameter('rating', 'field', False),
                                                     api_types.Parameter('likes_count', 'field', False),
                                                     api_types.Parameter('likes_id', 'field', False),
                                                     api_types.Parameter('dislikes_count', 'field', False),
                                                     api_types.Parameter('dislikes_id', 'field', False),
                                                     api_types.Parameter('comments_count', 'field', False),
                                                     api_types.Parameter('creation_date', 'field', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, data = backend.get_article_data(headers['article-id'], requested_data)

    if status.is_error:
        return json.dumps({'status': dict(status)})

    answer = {'status': dict(status)}
    answer.update(data)
    return json.dumps(answer)

@app.route('/pages', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_pages_get():
    status, headers = api_types.parse_structure(request.headers,
                                                [api_types.Parameter('user-id', 'int', True),
                                                 api_types.Parameter('indexes', 'list_of_int', True),
                                                 api_types.Parameter('include-nonsub', 'bool', True),
                                                 api_types.Parameter('sort-column', 'str', True),
                                                 api_types.Parameter('sort-direction', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status, include = api_types.parse_structure(request.headers,
                                               [api_types.Parameter('include-tags', 'list', False),
                                                api_types.Parameter('include-authors', 'list', False),
                                                api_types.Parameter('include-communities', 'list', False)])
    if status.is_error and status._error_type == request_status.ErrorType.ValueError:
        return json.dumps({'status': dict(status)})

    status, exclude = api_types.parse_structure(request.headers,
                                               [api_types.Parameter('exclude-tags', 'list', False),
                                                api_types.Parameter('exclude-authors', 'list', False),
                                                api_types.Parameter('exclude-communities', 'list', False)])
    if status.is_error and status._error_type == request_status.ErrorType.ValueError:
        return json.dumps({'status': dict(status)})

    status, bound = api_types.parse_structure(request.headers,
                                               [api_types.Parameter('upper-date', 'int', False),
                                                api_types.Parameter('lower-date', 'int', False),
                                                api_types.Parameter('upper-rating', 'int', False),
                                                api_types.Parameter('lower-rating', 'int', False)])
    if status.is_error and status._error_type == request_status.ErrorType.ValueError:
        return json.dumps({'status': dict(status)})

    if headers['sort-column'] not in ['creation_date', 'rating']:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Header "type" must have value "creation_date" or "rating"'))})

    if headers['sort-direction'] not in ['descending', 'ascending']:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Header "sort" must have value "descending" or "ascending"'))})

    if include:
        if 'include-tags' in include.keys():
            include['tags'] = include.pop('include-tags')
        if 'include-authors' in include.keys():
            include['authors'] = include.pop('include-authors')
        if 'include-community' in include.keys():
            include['community'] = include.pop('include-community')

    if exclude:
        if 'exclude-tags' in exclude.keys():
            exclude['tags'] = exclude.pop('exclude-tags')
        if 'exclude-authors' in exclude.keys():
            exclude['authors'] = exclude.pop('exclude-authors')
        if 'exclude-community' in exclude.keys():
            exclude['community'] = exclude.pop('exclude-community')

    status, pages = backend.get_pages(headers['indexes'],
                                      headers['user-id'],
                                      headers['include-nonsub'],
                                      headers['sort-column'],
                                      headers['sort-direction'],
                                      include,
                                      exclude,
                                      bound)
    return json.dumps({'status': dict(status), 'pages': pages})

@app.route('/users', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_post():
    status, user_info = api_types.parse_structure(request.json, 
                                                  [api_types.Parameter('username', 'str', True),
                                                   api_types.Parameter('nickname', 'str', True),
                                                   api_types.Parameter('email', 'str', True),
                                                   api_types.Parameter('password', 'str', True),
                                                   api_types.Parameter('avatar', 'str', False),
                                                   api_types.Parameter('sub-tags', 'list', False),
                                                   api_types.Parameter('blocked-tags', 'list', False),
                                                   api_types.Parameter('sub-users', 'list', False),
                                                   api_types.Parameter('blocked-users', 'list', False),
                                                   api_types.Parameter('sub-communities', 'list', False),
                                                   api_types.Parameter('blocked-communities', 'list', False),
                                                   api_types.Parameter('description', 'str', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    # replace "-" with "_" because field in db named with "_"
    if 'sub-tags' in user_info.keys():
        user_info['sub_tags'] = user_info.pop('sub-tags')
    if 'blocked-tags' in user_info.keys():
        user_info['blocked_tags'] = user_info.pop('blocked-tags')
    if 'sub-users' in user_info.keys():
        user_info['sub_users'] = user_info.pop('sub-users')
    if 'blocked-users' in user_info.keys():
        user_info['blocked_users'] = user_info.pop('blocked-users')
    if 'sub-communities' in user_info.keys():
        user_info['sub_communities'] = user_info.pop('sub-communities')
    if 'blocked-communities' in user_info.keys():
        user_info['blocked_communities'] = user_info.pop('blocked-communities')

    backend.add_user(user_info)
    return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK))})

@app.route('/users/data', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_data_get():
    status, headers = api_types.parse_structure(request.headers, [api_types.Parameter('user-id', 'str', True),
                                                                  api_types.Parameter('requested-data', 'list', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    if headers['user-id'] == '0':
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})

    status, requested_data = api_types.parse_fields(headers['requested-data'],
                                                    [api_types.Parameter('name_history', 'str', False),
                                                     api_types.Parameter('avatar', 'str', False),
                                                     api_types.Parameter('sub_tags', 'list', False),
                                                     api_types.Parameter('blocked_tags', 'list', False),
                                                     api_types.Parameter('sub_users', 'list', False),
                                                     api_types.Parameter('blocked_users', 'list', False),
                                                     api_types.Parameter('sub_communities', 'list', False),
                                                     api_types.Parameter('blocked_communities', 'list', False),
                                                     api_types.Parameter('nickname', 'str', False),
                                                     api_types.Parameter('email', 'str', False),
                                                     api_types.Parameter('description', 'str', False),
                                                     api_types.Parameter('creation_date', 'str', False),
                                                     api_types.Parameter('rating', 'str', False)])

    data = backend.get_user_data(headers['user-id'], requested_data)

    if status.is_error:
        return json.dumps({'status': dict(status)})

    answer = {'status': dict(status)}
    answer.update(data)
    return json.dumps(answer)

@app.route('/users/data', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_data_post():
    status, user_id = api_types.parse_structure(request.headers, [api_types.Parameter('user-id', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})
    user_id = user_id['user-id']

    if user_id == '0':
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})

    status, fields = api_types.parse_structure(request.json, [api_types.Parameter('avatar', 'str', False),
                                                              api_types.Parameter('sub-tags', 'str', False),
                                                              api_types.Parameter('blocked-tags', 'str', False),
                                                              api_types.Parameter('sub-users', 'str', False),
                                                              api_types.Parameter('blocked-users', 'str', False),
                                                              api_types.Parameter('sub-communities', 'str', False),
                                                              api_types.Parameter('blocked-communities', 'str', False),
                                                              api_types.Parameter('nickname', 'str', False),
                                                              api_types.Parameter('email', 'str', False),
                                                              api_types.Parameter('description', 'str', False)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    # replace "-" with "_" because field in db named with "_"
    if 'sub-tags' in fields.keys():
        fields['sub_tags'] = fields.pop('sub-tags')
    if 'blocked-tags' in fields.keys():
        fields['blocked_tags'] = fields.pop('blocked-tags')
    if 'sub-users' in fields.keys():
        fields['sub_users'] = fields.pop('sub-users')
    if 'blocked-users' in fields.keys():
        fields['blocked_users'] = fields.pop('blocked-users')
    if 'sub-communities' in fields.keys():
        fields['sub_communities'] = fields.pop('sub-communities')
    if 'blocked-communities' in fields.keys():
        fields['blocked_communities'] = fields.pop('blocked-communities')

    backend.update_user_info(fields, user_id)
    return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK))})

@app.route('/users/password', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_password_post():
    status, headers = api_types.parse_structure(request.headers,
                                                [api_types.Parameter('user-id', 'str', True),
                                                 api_types.Parameter('previous-password', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    if headers['user-id'] == 0:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})

    status, new_password = api_types.parse_structure(request.json, [api_types.Parameter('new-password', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    status = backend.change_password(headers['previous-password'],
                                     new_password['new-password'],
                                     headers['user-id'])
    return json.dumps({'status': dict(status)})

@app.route('/login', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_login_get():
    status, password = api_types.parse_structure(request.headers, [api_types.Parameter('password', 'str', True)])
    if status.is_error:
        return json.dumps({'status': dict(status)})
    password = password['password']

    status, login = api_types.parse_structure(request.headers, [api_types.Parameter('email', 'str', False),
                                                                api_types.Parameter('user-id', 'str', False),])
    if status.is_error:
        return json.dumps({'status': dict(status)})

    if login['user-id'] and login['email']:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='User can login via user-id OR via email.'))})

    if login['user-id'] == '0':
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})

    if login['user-id']:
        is_password_correct = backend.login(password, user_id=login['user-id'])
    else:
        is_password_correct = backend.login(password, email=login['email'])
    return json.dumps({'status': dict(status), 'is-correct': is_password_correct})

def run_server():
    # used in test_api to startup check
    print('Running...')
    app.run(host='0.0.0.0', port=5000)
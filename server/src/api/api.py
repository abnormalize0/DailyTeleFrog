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
3. Каждый запрос должен принимать на вход username заголовок.
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
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy.orm import Session
import json
import os
import builtins

from .. import backend
from .. import request_status
from .. import config
from .. import log
from . import api_info
from . import api_types

app = Flask(__name__)
app.register_blueprint(api_info.info)
cors = CORS(app)

global db_url

def check_list_elements(data, pattern):
    for element in data:
        is_found = False
        for requested_element in pattern:
            if element != requested_element['name']:
                continue
            else:
                is_found = True
        if is_found == False:
            return False
    return True

def check_structure(data, pattern):
    for element in pattern:
        if element['is_required'] == False:
            if element['name'] not in data:
                continue
        if element['name'] not in data:
                return False, request_status.ErrorType.OptionError
        if not type(data[element['name']]) == getattr(builtins, element['type'], None):
            return False, request_status.ErrorType.ValueError
        if element['type'] == 'json':
            is_ok, error = check_structure(data[element['name']], element['structure'])
            if not is_ok:
                return False, error
        if element['type'] == 'list':
            if element['structure']:
                is_ok = check_list_elements(data[element['name']], element['structure'])
                if not is_ok:
                    return False, request_status.ErrorType.ValueError
    return True, None

def fill_default(data, pattern):
    for value in pattern:
        if value['name'] not in data:
            data[value['name']] = api_info.type_defaults[value['type']]
    return data


@app.route('/article', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_post():
    is_right_structure, error = check_structure(request.json, api_info.article_post)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    if request.json['username'] == 'unlogged_user':
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})
    parameters = fill_default(request.json, api_info.article_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, article_id = backend.post_article(session, parameters['username'], parameters['title'], parameters['body'], parameters['preview'], parameters['tags'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK)), 'article_id': article_id})

@app.route('/article', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_get():
    is_right_structure, error = check_structure(request.json, api_info.article_get)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    parameters = fill_default(request.json, api_info.article_get)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, article = backend.get_article(session, parameters['article_id'], parameters['username'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK)), 'article': article})


@app.route('/article/like', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_like_post():
    is_right_structure, error = check_structure(request.json, api_info.article_like_post)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    parameters = fill_default(request.json, api_info.article_like_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.article_like(session, parameters['article_id'], parameters['username'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK))})


@app.route('/article/dislike', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_dislike_post():
    is_right_structure, error = check_structure(request.json, api_info.article_dislike_post)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    parameters = fill_default(request.json, api_info.article_dislike_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.article_dislike(session, parameters['article_id'], parameters['username'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK))})


@app.route('/article/comment', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_comment_post():
    is_right_structure, error = check_structure(request.json, api_info.article_comment_post)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    parameters = fill_default(request.json, api_info.article_comment_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, id = backend.add_comment(session=session,
                                     article_id=parameters['article_id'],
                                     username=parameters['username'],
                                     comment_text=parameters['text'],
                                     root=parameters['root'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK)), 'id': id})


@app.route('/article/comment/like', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_comment_like_post():
    is_right_structure, error = check_structure(request.json, api_info.article_comment_like_post)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    parameters = fill_default(request.json, api_info.article_comment_like_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.comment_like(session, parameters['comment_id'], parameters['username'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK))})


@app.route('/article/comment/dislike', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_comment_dislike_post():
    is_right_structure, error = check_structure(request.json, api_info.article_comment_dislike_post)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    parameters = fill_default(request.json, api_info.article_comment_dislike_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.comment_dislike(session, parameters['comment_id'], parameters['username'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK))})

@app.route('/article/comment/data', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_comment_data_get():
    is_right_structure, error = check_structure(request.json, api_info.article_comment_data_get)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    parameters = fill_default(request.json, api_info.article_comment_data_get)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, data = backend.get_comment_data(session, parameters['comment_id'], parameters['username'], parameters['requested_data'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        answer = {'status': dict(status)}
        answer.update(data)
        return json.dumps(answer)

@app.route('/article/data', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_article_data_get():
    is_right_structure, error = check_structure(request.json, api_info.article_data_get)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    parameters = fill_default(request.json, api_info.article_data_get)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, data = backend.get_article_data(session, parameters['article_id'], parameters['username'], parameters['requested_data'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        answer = {'status': dict(status)}
        answer.update(data)
        return json.dumps(answer)

@app.route('/pages', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_pages_get():
    is_right_structure, error = check_structure(request.json, api_info.article_data_get)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})

    parameters = fill_default(request.json, api_info.article_data_get)

    sort_column = parameters.get('sort_column')
    if sort_column and sort_column not in ['creation_date', 'rating']:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Header "type" must have value "creation_date" or "rating"'))})

    sort_direction = parameters.get("sort_direction")
    if sort_direction and sort_direction not in ['descending', 'ascending']:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Header "sort" must have value "descending" or "ascending"'))})

    include = {}
    if parameters.pop("include-tags"):
        include['tags'] = parameters.pop('include-tags')
    if parameters.pop("include-authors"):
        include['authors'] = parameters.pop('include-authors')
    if parameters.pop("include-community"):
        include['community'] = parameters.pop('include-community')

    exclude = {}
    if parameters.pop("exclude-tags"):
        exclude['tags'] = parameters.pop('exclude-tags')
    if parameters.pop("exclude-authors"):
        exclude['authors'] = parameters.pop('exclude-authors')
    if parameters.pop("exclude-community"):
        exclude['community'] = parameters.pop('exclude-community')

    bounds = {
        "lower": parameters.get("lower_bounds"),
        "upper": parameters.get("upper_bounds"),
    }

    status, pages = backend.get_pages(parameters["indexes"],
                                      parameters['username'],
                                      parameters['include-nonsub'],
                                      sort_column,
                                      sort_direction,
                                      include,
                                      exclude,
                                      bounds)
    return json.dumps({'status': dict(status), 'pages': pages})

@app.route('/users', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_post():
    is_right_structure, error = check_structure(request.json, api_info.users_post)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})

    parameters = fill_default(request.json, api_info.users_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status = backend.add_user(session, parameters)
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK))})

@app.route('/users/data', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_data_get():
    is_right_structure, error = check_structure(request.json, api_info.users_data_get)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    if request.json['username'] == 'unlogged_user':
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})
    parameters = fill_default(request.json, api_info.users_data_get)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, data = backend.get_user_data(session, parameters['username'], parameters['requested_data'])
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        answer = {'status': dict(status)}
        answer.update(data)
        return json.dumps(answer)

@app.route('/users/data', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_data_post():
    is_right_structure, error = check_structure(request.json, api_info.users_data_post)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    if request.json['username'] == 'unlogged_user':
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})
    #parameters = fill_default(request.json, api_info.users_data_post)
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        username = request.json.pop('username')
        status = backend.update_user_info(session, username, request.json)
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(status)})

@app.route('/users/password', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_users_password_post():
    is_right_structure, error = check_structure(request.json, api_info.user_password_post)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})
    if request.json['username'] == 'unlogged_user':
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        username = request.json.pop('username')
        previous_password = request.json.pop('previous_password')
        new_password = request.json.pop('new_password')
        status = backend.change_password(session, previous_password, new_password, username)
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(status)})

@app.route('/login', methods=['GET'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def api_login_get():
    is_right_structure, error = check_structure(request.json, api_info.login_get)
    if not is_right_structure:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=error,
                                          msg='Wrong request parameters structure.'))})

    parameters = fill_default(request.json, api_info.login_get)
    if request.json['username'] and request.json['email']:
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='User cant login via username and email.'))})
    if request.json['username'] == 'unlogged_user':
        return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                          error_type=request_status.ErrorType.ValueError,
                                          msg='Unlogged user cannot use this method'))})
    global db_url
    engine = create_engine(db_url)
    with Session(engine) as session:
        status, is_password_correct = backend.login(session, parameters)
        if status.is_error:
            session.rollback()
            return json.dumps({'status': dict(status)})

        session.commit()
        return json.dumps({'status': dict(status), 'is-correct': is_password_correct})

def run_server(server_mode='production'):
    global db_url
    if server_mode == 'test':
        db_url = os.getenv("MVP_DB_URL_TEST")
    else:
        db_url = os.getenv('MVP_DB_URL_PRODUCTION')
    app.run(host='0.0.0.0', port=5000)
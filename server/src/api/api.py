# '''
# Этот файл служит для хранения логики предобработки пользовательских запросов.
# В предобработку входит проверка необходимых заголовков, параметров запроса и тела запроса при наличии.
# В рамках предобработки этих полей выполняется преобразования к необходимым типам данных.
#
# Пометка для добавления нового API метода:
# 1. Названия методов формируются следующим образом: api_%METHOD_NAME%_%REQUEST_TYPE%
# Префикс api_ обрабатывается в тестах, поэтому он обязателен.
# Остальная часть названия метода позволяет избежать дублирования названий функций.
# 2. Для каждого метода должен присутствовать тест в файле /server/test/test_api.py
# и ответ на запрос OPTIONS в файле /server/src/api_info.py
# 3. Каждый запрос должен принимать на вход username заголовок.
# По договоренности считаем, что в этом заголвке указан автор запроса.
# Значение -1 характеризует неавторизванного пользователя.
# 4. Каждый API метод обязан возвращать статус операции.
# 5. Последовательность API методов должна быть одинаковой для этого файла, документации, тестов и запросов OPTIONS.
# 6. Каждый запрос должен быть декорирован таймером и логгированием принимаемых аргументов.
# Логгирование аргументов позволит облегчить поиск проблем, когда такие возникнут.
# Таймер позволит иметь конкретные значения времени выполнения запроса, что облегчит решение проблем аля "ВСЕ ТОРМОЗИТ!!!"
# 7. Для API методов типа POST обязательно должно присутсвовать тело запроса.
# В этом теле располагаются данные, которые будут добавлены на сервер. Остальные параметры перечислены в заголовках.
# '''
#
# from flask import Flask, request
# from flask_cors import CORS
# from dotenv import load_dotenv
# from sqlalchemy import engine_from_config, create_engine
# from sqlalchemy.orm import Session
# import json
# import os
# import builtins
#
# from .. import backend
# from .. import request_status
# from .. import config
# from .. import log
# from . import api_info
# from . import api_types
#
# app = Flask(__name__)
# app.register_blueprint(api_info.info)
# cors = CORS(app)
#
# def check_list_elements(data, pattern):
#     for element in data:
#         is_found = False
#         for requested_element in pattern:
#             if element != requested_element['name']:
#                 continue
#             else:
#                 is_found = True
#         if is_found == False:
#             return False
#     return True
#
# def check_structure(data, pattern):
#     import sys
#     for element in pattern:
#         if element['is_required'] == False:
#             if element['name'] not in data:
#                 continue
#         if element['name'] not in data:
#                 return False, request_status.ErrorType.OptionError
#         if not type(data[element['name']]) == getattr(builtins, element['type'], None):
#             return False, request_status.ErrorType.ValueError
#         if element['type'] == 'json':
#             is_ok, error = check_structure(data[element['name']], element['structure'])
#             if not is_ok:
#                 return False, error
#         if element['type'] == 'list':
#             if element['structure']:
#                 is_ok = check_list_elements(data[element['name']], element['structure'])
#                 if not is_ok:
#                     return False, request_status.ErrorType.ValueError
#     return True, None
#
# def fill_default(data, pattern):
#     for value in pattern:
#         if value['name'] not in data:
#             data[value['name']] = api_info.type_defaults[value['type']]
#     return data
#
#
# @app.route('/article', methods=['POST'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_article_post():
#     is_right_structure, error = check_structure(request.json, api_info.article_post)
#     if not is_right_structure:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=error,
#                                           msg='Wrong request parameters structure.'))})
#     if request.json['username'] == 'unlogged_user':
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=request_status.ErrorType.ValueError,
#                                           msg='Unlogged user cannot use this method'))})
#     parameters = fill_default(request.json, api_info.article_post)
#     global db_url
#     engine = create_engine(db_url)
#     with Session(engine) as session:
#         status, article_id = backend.post_article(session, parameters['username'], parameters['title'], parameters['body'], parameters['preview'], parameters['tags'])
#         if status.is_error:
#             session.rollback()
#             return json.dumps({'status': dict(status)})
#
#         session.commit()
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK)), 'article_id': article_id})
#
# @app.route('/article', methods=['GET'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_article_get():
#     is_right_structure, error = check_structure(request.json, api_info.article_get)
#     if not is_right_structure:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=error,
#                                           msg='Wrong request parameters structure.'))})
#     parameters = fill_default(request.json, api_info.article_get)
#     global db_url
#     engine = create_engine(db_url)
#     with Session(engine) as session:
#         status, article = backend.get_article(session, parameters['article_id'], parameters['username'])
#         if status.is_error:
#             session.rollback()
#             return json.dumps({'status': dict(status)})
#
#         session.commit()
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK)), 'article': article})
#
# @app.route('/article/data', methods=['POST'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_article_data_post():
#     status, headers = api_types.parse_structure(request.headers, [api_types.Parameter('username', 'str', True),
#                                                                   api_types.Parameter('article-id', 'int', True)])
#     if status.is_error:
#         return json.dumps({'status': dict(status)})
#
#     if headers['username'] == 'unlogged_user':
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=request_status.ErrorType.ValueError,
#                                           msg='Unlogged user cannot use this method'))})
#
#     status, command = api_types.parse_structure(request.json, [api_types.Parameter('like-article', 'json', False),
#                                                                api_types.Parameter('dislike-article', 'json', False),
#                                                                api_types.Parameter('like-comment', 'json', False),
#                                                                api_types.Parameter('dislike-comment', 'json', False),
#                                                                api_types.Parameter('add-comment', 'json', False)])
#     if status.is_error:
#         return json.dumps({'status': dict(status)})
#
#     if 'like-comment' in command:
#         status, _ = api_types.parse_structure(command['like-comment'], [api_types.Parameter('comment_id', 'int', True)])
#         if status.is_error:
#             return json.dumps({'status': dict(status)})
#
#     if 'dislike-comment' in command:
#         status, _ = api_types.parse_structure(command['dislike-comment'],
#                                               [api_types.Parameter('comment_id', 'int', True)])
#         if status.is_error:
#             return json.dumps({'status': dict(status)})
#
#     if 'add-comment' in command:
#         status, _ = api_types.parse_structure(command['add-comment'], [api_types.Parameter('root', 'int', True),
#                                                                        api_types.Parameter('text', 'str', True)])
#         if status.is_error:
#             return json.dumps({'status': dict(status)})
#
#     if 'like-article' in command:
#         status = backend.like_article(headers['article-id'], headers['username'])
#         return json.dumps({'status': dict(status)})
#
#     if 'dislike-article' in command:
#         status = backend.dislike_article(headers['article-id'], headers['username'])
#         return json.dumps({'status': dict(status)})
#
#     if 'like-comment' in command:
#         status = backend.like_comment(command['like-comment']['comment_id'], headers['username'])
#         return json.dumps({'status': dict(status)})
#
#     if 'dislike-comment' in command:
#         status = backend.dislike_comment(command['dislike-comment']['comment_id'], headers['username'])
#         return json.dumps({'status': dict(status)})
#
#     if 'add-comment' in command:
#         status, comment_id = backend.add_comment(headers['article-id'],
#                                                  command['add-comment']['root'],
#                                                  command['add-comment']['text'],
#                                                  headers['username'])
#         return json.dumps({'status': dict(status), 'comment_id': comment_id})
#
# @app.route('/article/data', methods=['GET'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_article_data_get():
#     is_right_structure, error = check_structure(request.json, api_info.article_data_get)
#     if not is_right_structure:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=error,
#                                           msg='Wrong request parameters structure.'))})
#     parameters = fill_default(request.json, api_info.article_data_get)
#     global db_url
#     engine = create_engine(db_url)
#     with Session(engine) as session:
#         status, data = backend.get_article_data(session, parameters['article_id'], parameters['username'], parameters['requested_data'])
#         if status.is_error:
#             session.rollback()
#             return json.dumps({'status': dict(status)})
#
#         session.commit()
#         answer = {'status': dict(status)}
#         answer.update(data)
#         return json.dumps(answer)
#
# @app.route('/pages', methods=['GET'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_pages_get():
#     status, headers = api_types.parse_structure(request.headers,
#                                                 [api_types.Parameter('username', 'str', True),
#                                                  api_types.Parameter('indexes', 'list_of_int', True),
#                                                  api_types.Parameter('include-nonsub', 'bool', True),
#                                                  api_types.Parameter('sort-column', 'str', True),
#                                                  api_types.Parameter('sort-direction', 'str', True)])
#     if status.is_error:
#         return json.dumps({'status': dict(status)})
#
#     status, include = api_types.parse_structure(request.headers,
#                                                [api_types.Parameter('include-tags', 'list', False),
#                                                 api_types.Parameter('include-authors', 'list', False),
#                                                 api_types.Parameter('include-communities', 'list', False)])
#     if status.is_error and status._error_type == request_status.ErrorType.ValueError:
#         return json.dumps({'status': dict(status)})
#
#     status, exclude = api_types.parse_structure(request.headers,
#                                                [api_types.Parameter('exclude-tags', 'list', False),
#                                                 api_types.Parameter('exclude-authors', 'list', False),
#                                                 api_types.Parameter('exclude-communities', 'list', False)])
#     if status.is_error and status._error_type == request_status.ErrorType.ValueError:
#         return json.dumps({'status': dict(status)})
#
#     status, bound = api_types.parse_structure(request.headers,
#                                                [api_types.Parameter('upper-date', 'int', False),
#                                                 api_types.Parameter('lower-date', 'int', False),
#                                                 api_types.Parameter('upper-rating', 'int', False),
#                                                 api_types.Parameter('lower-rating', 'int', False)])
#     if status.is_error and status._error_type == request_status.ErrorType.ValueError:
#         return json.dumps({'status': dict(status)})
#
#     if headers['sort-column'] not in ['creation_date', 'rating']:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=request_status.ErrorType.ValueError,
#                                           msg='Header "type" must have value "creation_date" or "rating"'))})
#
#     if headers['sort-direction'] not in ['descending', 'ascending']:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=request_status.ErrorType.ValueError,
#                                           msg='Header "sort" must have value "descending" or "ascending"'))})
#
#     if include:
#         if 'include-tags' in include.keys():
#             include['tags'] = include.pop('include-tags')
#         if 'include-authors' in include.keys():
#             include['authors'] = include.pop('include-authors')
#         if 'include-community' in include.keys():
#             include['community'] = include.pop('include-community')
#
#     if exclude:
#         if 'exclude-tags' in exclude.keys():
#             exclude['tags'] = exclude.pop('exclude-tags')
#         if 'exclude-authors' in exclude.keys():
#             exclude['authors'] = exclude.pop('exclude-authors')
#         if 'exclude-community' in exclude.keys():
#             exclude['community'] = exclude.pop('exclude-community')
#
#     status, pages = backend.get_pages(headers['indexes'],
#                                       headers['username'],
#                                       headers['include-nonsub'],
#                                       headers['sort-column'],
#                                       headers['sort-direction'],
#                                       include,
#                                       exclude,
#                                       bound)
#     return json.dumps({'status': dict(status), 'pages': pages})
#
# @app.route('/users', methods=['POST'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_users_post():
#     is_right_structure, error = check_structure(request.json, api_info.users_post)
#     if not is_right_structure:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=error,
#                                           msg='Wrong request parameters structure.'))})
#
#     parameters = fill_default(request.json, api_info.users_post)
#     global db_url
#     engine = create_engine(db_url)
#     with Session(engine) as session:
#         status = backend.add_user(session, parameters)
#         if status.is_error:
#             session.rollback()
#             return json.dumps({'status': dict(status)})
#
#         session.commit()
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.OK))})
#
# @app.route('/users/data', methods=['GET'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_users_data_get():
#     is_right_structure, error = check_structure(request.json, api_info.users_data_get)
#     if not is_right_structure:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=error,
#                                           msg='Wrong request parameters structure.'))})
#     if request.json['username'] == 'unlogged_user':
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=request_status.ErrorType.ValueError,
#                                           msg='Unlogged user cannot use this method'))})
#     parameters = fill_default(request.json, api_info.users_data_get)
#     global db_url
#     engine = create_engine(db_url)
#     with Session(engine) as session:
#         status, data = backend.get_user_data(session, parameters['username'], parameters['requested-data'])
#         if status.is_error:
#             session.rollback()
#             return json.dumps({'status': dict(status)})
#
#         session.commit()
#         answer = {'status': dict(status)}
#         answer.update(data)
#         return json.dumps(answer)
#
# @app.route('/users/data', methods=['POST'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_users_data_post():
#     is_right_structure, error = check_structure(request.json, api_info.users_data_post)
#     if not is_right_structure:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=error,
#                                           msg='Wrong request parameters structure.'))})
#     if request.json['username'] == 'unlogged_user':
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=request_status.ErrorType.ValueError,
#                                           msg='Unlogged user cannot use this method'))})
#     #parameters = fill_default(request.json, api_info.users_data_post)
#     global db_url
#     engine = create_engine(db_url)
#     with Session(engine) as session:
#         username = request.json.pop('username')
#         status = backend.update_user_info(session, username, request.json)
#         if status.is_error:
#             session.rollback()
#             return json.dumps({'status': dict(status)})
#
#         session.commit()
#         return json.dumps({'status': dict(status)})
#
# @app.route('/users/password', methods=['POST'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_users_password_post():
#     is_right_structure, error = check_structure(request.json, api_info.user_password_post)
#     if not is_right_structure:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=error,
#                                           msg='Wrong request parameters structure.'))})
#     if request.json['username'] == 'unlogged_user':
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=request_status.ErrorType.ValueError,
#                                           msg='Unlogged user cannot use this method'))})
#     global db_url
#     engine = create_engine(db_url)
#     with Session(engine) as session:
#         username = request.json.pop('username')
#         previous_password = request.json.pop('previous_password')
#         new_password = request.json.pop('new_password')
#         status = backend.change_password(session, previous_password, new_password, username)
#         if status.is_error:
#             session.rollback()
#             return json.dumps({'status': dict(status)})
#
#         session.commit()
#         return json.dumps({'status': dict(status)})
#
# @app.route('/login', methods=['GET'])
# @log.safe_api
# @log.log_request
# @log.timer(config.log_server_api)
# def api_login_get():
#     is_right_structure, error = check_structure(request.json, api_info.login_get)
#     if not is_right_structure:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=error,
#                                           msg='Wrong request parameters structure.'))})
#
#     parameters = fill_default(request.json, api_info.login_get)
#     if request.json['username'] and request.json['email']:
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=request_status.ErrorType.ValueError,
#                                           msg='User cant login via username and email.'))})
#     if request.json['username'] == 'unlogged_user':
#         return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
#                                           error_type=request_status.ErrorType.ValueError,
#                                           msg='Unlogged user cannot use this method'))})
#     global db_url
#     engine = create_engine(db_url)
#     with Session(engine) as session:
#         status, is_password_correct = backend.login(session, parameters)
#         if status.is_error:
#             session.rollback()
#             return json.dumps({'status': dict(status)})
#
#         session.commit()
#         return json.dumps({'status': dict(status), 'is-correct': is_password_correct})

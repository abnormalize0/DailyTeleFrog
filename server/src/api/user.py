from flask import Blueprint, request, Response
from src.services.user_service import UserService
from src import config
from src import log


user = Blueprint('user', __name__, url_prefix='/user')


@user.route('/login', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def login():
    login_data = request.json
    username = login_data.get('username', None)
    password = login_data.get('password', None)
    logged_in_user, _ = UserService.login(username, password)
    return Response(response=logged_in_user, status=200, mimetype="application/json")


@user.route('/register', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def register():
    register_data = request.json
    username = register_data.get('username', None)
    password = register_data.get('password', None)
    email = register_data.get('email', None)
    registered_user, _ = UserService.register(username, password, email)
    return Response(response=registered_user, status=200, mimetype="application/json")

from flask import Blueprint, request
from src.services.user_service import login, register
from src import config
from src import log

user = Blueprint('user', __name__)


@user.route('/login', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def login():
    login_data = request.json
    username = login_data.get('username', None)
    password = login_data.get('password', None)
    return login(username, password)


@user.route('/register', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(config.log_server_api)
def register():
    register_data = request.json
    username = register_data.get('username', None)
    password = register_data.get('password', None)
    email = register_data.get('email', None)
    return register(username, password, email)

import os

from flask import Blueprint, request, Response
from src.services.user_service import UserService
from src import log
from src.config import mail, log_server_api
from flask_mail import Message


user = Blueprint('user', __name__, url_prefix='/user')


@user.route('/login', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(log_server_api)
def login():
    login_data = request.json
    username = login_data.get('username', None)
    password = login_data.get('password', None)
    logged_in_user, _ = UserService.login(username, password)
    return Response(response=logged_in_user, status=200, mimetype="application/json")


@user.route('/register', methods=['POST'])
@log.safe_api
@log.log_request
@log.timer(log_server_api)
def register():
    register_data = request.json
    username = register_data.get('username', None)
    password = register_data.get('password', None)
    email = register_data.get('email', None)
    registered_user, status = UserService.register(username, password, email)
    return Response(response=registered_user, status=status.convert_to_http_error(), mimetype="application/json")


@user.route('/forgot/password', methods=['POST'])
# @log.safe_api
# @log.log_request
# @log.timer(log_server_api)
def forgot_password():
    forgot_password_data = request.json
    email = forgot_password_data.get('email', None)
    mail_message = Message(
        'Hi ! Don’t forget to follow me for more article!',
        sender=os.getenv('MAIL_USERNAME'),
        recipients=[email]
    )
    mail_message.body = 'Hello Flask message sent from Flask-Mail'
    mail.send(mail_message)
    return Response(status=200)

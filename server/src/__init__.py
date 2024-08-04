from src.config import mail
from flask import Flask
import os
from os.path import join, dirname


def create_app(server_mode='production'):
    app = Flask(__name__)

    from dotenv import load_dotenv
    # used in test_api to startup check
    dotenv_path = join(dirname(__file__), '../.env_prod') if server_mode == 'production' else (
        join(dirname(__file__), '../.env_test'))
    load_dotenv(dotenv_path)

    # mail configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True

    mail.init_app(app)

    # apply the blueprints to the app
    from .api.user import user
    app.register_blueprint(user)

    return app

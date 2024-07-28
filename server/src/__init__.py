from flask import Flask
from os.path import join, dirname


def create_app(server_mode='production'):
    app = Flask(__name__)

    from dotenv import load_dotenv
    # used in test_api to startup check
    dotenv_path = join(dirname(__file__), '../.env_prod') if server_mode == 'production' else (
        join(dirname(__file__), '../.env_test'))
    load_dotenv(dotenv_path)

    # apply the blueprints to the app
    from .api.user import user
    app.register_blueprint(user)

    return app

import os
from flask import Flask


def create_app(server_mode='production'):
    app = Flask(__name__)

    from dotenv import load_dotenv
    # used in test_api to startup check
    dotenv_path = '../../.env_prod' if server_mode == 'production' else '../../.env_test'
    load_dotenv(dotenv_path=dotenv_path)

    db_url = os.getenv('MVP_DB_URL')

    return app

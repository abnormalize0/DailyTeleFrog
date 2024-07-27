import os
from flask import Flask


def create_app(server_mode='production'):
    app = Flask(__name__)

    from dotenv import load_dotenv
    # used in test_api to startup check
    load_dotenv(dotenv_path='../../.env')

    if server_mode == 'test':
        db_url = os.getenv('MVP_DB_URL_TEST')
    else:
        db_url = os.getenv('MVP_DB_URL_PRODUCTION')

    return app

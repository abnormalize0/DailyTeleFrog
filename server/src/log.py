'''
Этот файл служит для хранения декораторов, которые используются для системы логгирования на сервере.
'''

import logging
import traceback
import json
from flask import request
from datetime import datetime

from . import config
from . import request_status

def timer(log_file:config.DynamicPath):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(log_file.path)
            start = datetime.now()

            result = func(*args, **kwargs)

            end = datetime.now()
            exec_time = end-start
            exec_time_str = str(exec_time)
            logger.info(f'Processed request in {exec_time_str}: {func.__name__}')
            return result

        # timer used in server/api.py
        # @app.route registers url path using wrapper name, so i change name to avoid name collision
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator

def log_request(func):
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(config.log_server_api.path)
        logger.info(f'Got request {func.__name__}')
        if request.is_json:
            logger.info(f'Body: {request.json}')
        else:
            logger.info(f'Body: Empty')
        logger.info(f'Headers: {request.headers}')
        result = func(*args, **kwargs)
        logger.info(f'Result: {result}\n\n\n\n')
        return result

    # @app.route registers url path using wrapper name, so i change name to avoid name collision
    wrapper.__name__ = func.__name__
    return wrapper

def log_args_kwargs(log_file:config.DynamicPath):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(log_file.path)
            logger.info(f'Got request {func.__name__}\nArgs: {args}\nKwargs: {kwargs}')
            result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

def safe_api(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            logger = logging.getLogger(config.log_server_api.path)
            logger.error(traceback.format_exc())
            return json.dumps({'status': dict(request_status.Status(request_status.StatusType.ERROR,
                                              request_status.ErrorType.UnexpectedError,
                                              msg='Unexpected error'))})
    wrapper.__name__ = func.__name__
    return wrapper
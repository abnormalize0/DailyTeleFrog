import logging
from flask import request
from datetime import datetime

from . import config

def timer(log_file:config.DynamicPath):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(log_file.path)
            start = datetime.now()

            result = func(*args, **kwargs)

            end = datetime.now()
            exec_time = end-start
            exec_time_str = str(exec_time)
            logger.info(f'Processed request in {exec_time_str}: {func.__name__}\n')
            return result

        # timer used in server/api.py
        # @app.route registers url path using wrapper name, so i change name to avoid name collision
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator

def log_headers(func):
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(config.log_server_api.path)
        logger.info(f'Got request {func.__name__}\nWith headers: {request.headers}')
        result = func(*args, **kwargs)
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
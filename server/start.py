"""
Этот файл служит для хранения логики запуска сервера и подготовки пространства для его
корректной работы: создания директории логов и настройки логгера API.
"""

import argparse
import logging
import os
import sys

from src import config
from src.api import api


def standard_configuration(log_name: str) -> None:
    """Настраивает файловый логгер с форматом времени, уровня и сообщения.

    Args:
        log_name: имя логгера и путь к файлу лога.

    Returns:
        None
    """
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_name)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def set_up_loggers() -> None:
    """Создаёт директорию логов при необходимости и настраивает логгер API.

    Args:
        None

    Returns:
        None
    """
    if not os.path.exists(config.log_directory.path):
        os.mkdir(config.log_directory.path)
    standard_configuration(config.log_server_api.path)


# RawTextHelpFormatter support multistring comments
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-t", "--test", action="store_true", help="Run server in test mode")
parser.add_argument("--working-directory", help="Set work directory for server")

flags = vars(parser.parse_args(sys.argv[1:]))

path = flags["working_directory"]
if path:
    if not os.path.exists(os.path.join(os.getcwd(), path)):
        os.mkdir(path)
    os.chdir(path)

set_up_loggers()
if flags["test"]:
    api.run_server(server_mode="test")
else:
    api.run_server()

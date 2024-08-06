'''
Этот файл служит для хранения логики запуска сервера и подготовки пространства для его корректной работы.
Например, в этом файле реализована логика создания необходимых директорий для корректной работы сервера.
'''

import sys
import argparse
import sqlite3
import shutil
import os
import logging
from datetime import datetime

from src import config
from src import create_app


def backup():
    if not os.path.exists(config.backup_directory.path):
        os.mkdir(config.backup_directory.path)

    tmp_dir = os.path.join(config.backup_directory.path, datetime.now().strftime('%Y-%m-%d %H.%M.%S'))
    if os.path.exists(config.db_user_directory.path):
        shutil.copytree(config.db_user_directory.path, tmp_dir, dirs_exist_ok=True)
    if os.path.exists(config.db_article_directory.path):
        shutil.copytree(config.db_article_directory.path, tmp_dir, dirs_exist_ok=True)
    if os.path.exists(config.db_comment_directory.path):
        shutil.copytree(config.db_comment_directory.path, tmp_dir, dirs_exist_ok=True)
    if os.path.exists(config.log_directory.path):
        shutil.copytree(config.log_directory.path, tmp_dir, dirs_exist_ok=True)

    if os.path.exists(tmp_dir):
        shutil.make_archive(tmp_dir, 'zip', root_dir=tmp_dir,)
        shutil.rmtree(tmp_dir)

def standart_configuration(log_name):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_name)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def set_up_loggers():
    if not os.path.exists(config.log_directory.path):
        os.mkdir(config.log_directory.path)
    standart_configuration(config.log_server_api.path)
    standart_configuration(config.log_db_api.path)

def init_users():
    shutil.rmtree(config.db_user_directory.path, ignore_errors=True)
    os.makedirs(config.db_user_directory.path)
    connection = sqlite3.connect(config.db_user.path)
    cursor = connection.cursor()
    cursor.execute(f'''CREATE TABLE {config.user_table_name} (
                    {config.user_id_name} TEXT PRIMARY KEY,
                    nickname TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    name_history TEXT,
                    avatar TEXT,
                    sub_tags TEXT,
                    blocked_tags TEXT,
                    sub_users TEXT,
                    blocked_users TEXT,
                    sub_communities TEXT,
                    blocked_communities TEXT,
                    description TEXT,
                    creation_date INTEGER NOT NULL,
                    rating INTEGER)''')
    connection.commit()
    connection.close()

def init_articles():
    shutil.rmtree(config.db_article_directory.path, ignore_errors=True)
    os.makedirs(config.db_article_directory.path)
    connection = sqlite3.connect(config.db_article.path)
    cursor = connection.cursor()
    cursor.execute(f'''CREATE TABLE {config.article_table_name} (
                    {config.article_id_name} INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    creation_date INTEGER NOT NULL,
                    community TEXT,
                    rating INTEGER,
                    likes_count INTEGER,
                    likes_id TEXT,
                    dislikes_count INTEGER,
                    dislikes_id TEXT,
                    comments_count INTEGER,
                    preview_content JSON NOT NULL,
                    author_preview JSON NOT NULL,
                    author_id INTEGER NOT NULL,
                    tags TEXT)''')
    connection.commit()
    connection.close()

def init_comments():
    shutil.rmtree(config.db_comment_directory.path, ignore_errors=True)
    os.makedirs(config.db_comment_directory.path)
    connection = sqlite3.connect(config.db_comment.path)
    cursor = connection.cursor()
    cursor.execute(f'''CREATE TABLE {config.comment_table_name} (
                    {config.comment_id_name} INTEGER PRIMARY KEY,
                    creation_date INTEGER NOT NULL,
                    rating INTEGER,
                    likes_count INTEGER,
                    likes_id TEXT,
                    dislikes_count INTEGER,
                    dislikes_id TEXT,
                    article_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL)''')
    connection.commit()
    connection.close()

# RawTextHelpFormatter support multistring comments
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-p', '--production', action='store_true',
                    help='Run server in production mode')
parser.add_argument('--working-directory',
                    help='Set work directory for server')

flags = vars(parser.parse_args(sys.argv[1:]))

path = flags['working_directory']
if path:
    if not os.path.exists(os.path.join(os.getcwd(), path)):
        os.mkdir(path)
    os.chdir(path)

set_up_loggers()

app = create_app() if flags['production'] else create_app(server_mode='test')

if __name__ == '__main__':
    app.run()

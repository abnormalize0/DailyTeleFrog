import sys
import argparse
import sqlite3
import shutil
import os
import logging
from datetime import datetime

from src import api
from src import config

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
                    {config.user_id_name} INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    page TEXT,
                    avatar TEXT,
                    blocked_tags TEXT)''')
    connection.close()

def init_articles():
    shutil.rmtree(config.db_article_directory.path, ignore_errors=True)
    os.makedirs(config.db_article_directory.path)
    connection = sqlite3.connect(config.db_article.path)
    cursor = connection.cursor()
    cursor.execute(f'''CREATE TABLE {config.article_table_name} (
                    {config.article_id_name} INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    created TEXT NOT NULL,
                    likes_count INTEGER,
                    likes_id TEXT,
                    dislikes_count INTEGER,
                    dislikes_id TEXT,
                    comments_count INTEGER,
                    preview_content JSON NOT NULL,
                    author_preview JSON NOT NULL,
                    author_id INTEGER NOT NULL,
                    tags TEXT)''')
    connection.close()

def init_comments():
    shutil.rmtree(config.db_comment_directory.path, ignore_errors=True)
    os.makedirs(config.db_comment_directory.path)
    connection = sqlite3.connect(config.db_comment.path)
    cursor = connection.cursor()
    cursor.execute(f'''CREATE TABLE {config.comment_table_name} (
                    {config.comment_id_name} INTEGER PRIMARY KEY,
                    likes_count INTEGER,
                    likes_id TEXT,
                    dislikes_count INTEGER,
                    dislikes_id TEXT,
                    article_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL)''')
    connection.close()

#RawTextHelpFormatter support multistring comments
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-i', '--init', action='store_true',
                    help='Create all server databases. Existing databases will be deleted')
parser.add_argument('--init-users', action='store_true',
                    help='Create all users databases. Existing database will be deleted')
parser.add_argument('--init-articles', action='store_true',
                    help='Create all articles databases. Existing database will be deleted')
parser.add_argument('--init-comments', action='store_true',
                    help='Create all comments databases. Existing database will be deleted')
parser.add_argument('--dont-start-server', action='store_true', default=False,
                    help="Don't start the server")
parser.add_argument('--working-directory',
                    help='Set work directory for server')

flags = vars(parser.parse_args(sys.argv[1:]))

path = flags['working_directory']
if path:
    if not os.path.exists(os.path.join(os.getcwd(), path)):
        os.mkdir(path)
    os.chdir(path)

if flags['init']:
    backup()
    init_users()
    init_articles()
    init_comments()
else:
    if flags['init_users']:
        backup()
        init_users()

    if flags['init_articles']:
        backup()
        init_articles()

    if flags['init_comments']:
        backup()
        init_comments()

if not flags['dont_start_server']:
    set_up_loggers()
    api.run_server()
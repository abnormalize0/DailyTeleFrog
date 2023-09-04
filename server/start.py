import sys
import argparse
import sqlite3
import shutil
import os
from datetime import datetime

from src import api
from src import config

def copy_users(work_dir=None):
    if not os.path.exists(config.BACKUPDIRECTORY):
        os.mkdir(config.BACKUPDIRECTORY)
    if not work_dir:
        work_dir = os.path.join(config.BACKUPDIRECTORY, datetime.now().strftime('%Y-%m-%d %H.%M.%S'))
        os.mkdir(work_dir)
    shutil.copytree(config.USERSDIRECTORY, os.path.join(work_dir, 'users'), dirs_exist_ok=True)
    return work_dir

def copy_articles(work_dir=None):
    if not os.path.exists(config.BACKUPDIRECTORY):
        os.mkdir(config.BACKUPDIRECTORY)
    if not work_dir:
        work_dir = os.path.join(config.BACKUPDIRECTORY, datetime.now().strftime('%Y-%m-%d %H.%M.%S'))
        os.mkdir(work_dir)
    shutil.copytree(config.ARTICLEDIRECTORY, os.path.join(work_dir, 'articles'), dirs_exist_ok=True)
    return work_dir

def backup(work_dir):
    shutil.make_archive(work_dir, 'zip', root_dir=work_dir,)
    shutil.rmtree(work_dir)
    return

def init_users(path):
    shutil.rmtree(config.USERSDIRECTORY, ignore_errors=True)
    if not path:
        config.USERSDIRECTORY = config.DEFAULTUSERSDIRECTORY
    else:
        config.USERSDIRECTORY = path
        config.USERSDB= os.path.join(config.USERSDIRECTORY, 'user.db')
    os.makedirs(config.USERSDIRECTORY)
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE {0} (
                            {1} INTEGER PRIMARY KEY,
                            name TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            page TEXT,
                            avatar TEXT,
                            blocked_tags TEXT)
    '''.format(config.USERSTABLENAME, config.USERSIDNAME))
    connection.close()
    return

def init_articles(path):
    shutil.rmtree(config.ARTICLEDIRECTORY, ignore_errors=True)
    if not path:
        config.ARTICLEDIRECTORY = config.DEFAULTARTICLEDIRECTORY
    else:
        config.ARTICLEDIRECTORY = path
        config.ARTICLESDB = os.path.join(config.ARTICLEDIRECTORY, 'articles.db')
    os.makedirs(config.ARTICLEDIRECTORY)
    connection = sqlite3.connect(config.ARTICLESDB)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE {0} (
                            {1} INTEGER PRIMARY KEY,
                            name TEXT NOT NULL,
                            created TEXT NOT NULL,
                            likes_count INTEGER,
                            likes_id TEXT,
                            comments_count INTEGER,
                            preview_content JSON NOT NULL,
                            author_preview JSON NOT NULL,
                            tags TEXT)
    '''.format(config.ARTICLESTABLENAME, config.ARTICLESIDNAME))
    connection.close()
    return

def init_comments(path):
    shutil.rmtree(config.COMMENTSDIRECTORY, ignore_errors=True)
    if not path:
        config.COMMENTSDIRECTORY = config.DEFAULTCOMMENTSDIRECTORY
    else:
        config.COMMENTSDIRECTORY = path
        config.COMMENTSDB = os.path.join(config.COMMENTSDIRECTORY, 'comments.db')
    os.makedirs(config.COMMENTSDIRECTORY)
    connection = sqlite3.connect(config.COMMENTSDB)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE {0} (
                            {1} INTEGER PRIMARY KEY,
                            likes_count INTEGER,
                            likes_id TEXT,
                            article_id INTEGER NOT NULL,
                            author_id INTEGER NOT NULL)
    '''.format(config.COMMENTSTABLENAME, config.COMMENTSIDNAME))
    return

#RawTextHelpFormatter support multistring comments
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-b', '--backup', action='store_true',
                    help='Create a backup copy of the all server databases at {0} location'\
                    .format(config.BACKUPDIRECTORY))
parser.add_argument('--backup-users', action='store_true',
                    help='Create a backup copy of the users databases at {0} location'\
                    .format(config.BACKUPDIRECTORY))
parser.add_argument('--backup-articles', action='store_true',
                    help='Create a backup copy of the articles databases at {0} location'\
                    .format(config.BACKUPDIRECTORY))
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
parser.add_argument('--user-db-filepath',
                    help='Set filepath for user databases')
parser.add_argument('--articles-db-filepath',
                    help='Set filepath for articles databases')
parser.add_argument('--comments-db-filepath',
                    help='Set filepath for articles databases')

flags = vars(parser.parse_args(sys.argv[1:]))

if flags['backup']:
    work_dir = copy_users()
    copy_articles(work_dir)
    backup(work_dir)
else:
    if flags['backup_users']:
        work_dir = copy_users()
        backup(work_dir)

    if flags['backup_articles']:
        work_dir = copy_articles()
        backup(work_dir)

if flags['init']:
    init_users(flags['user_db_filepath'])
    init_articles(flags['articles_db_filepath'])
    init_comments(flags['comments_db_filepath'])
else:
    if flags['init_users']:
        init_users(flags['user_db_filepath'])

    if flags['init_articles']:
        init_articles(flags['articles_db_filepath'])

    if flags['init_comments']:
        init_comments(flags['comments_db_filepath'])

if not flags['dont_start_server']:
    api.run_server()
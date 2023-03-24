import sys
import argparse
import sqlite3
import shutil
import os
from datetime import datetime

import api
import config

def copy_users(work_dir=None):
    if not os.path.exists(config.BACKUPDIRECTORY):
        os.mkdir(config.BACKUPDIRECTORY)
    if not work_dir:
        work_dir = os.path.join(config.BACKUPDIRECTORY, datetime.now().strftime("%Y-%m-%d %H.%M.%S"))
        os.mkdir(work_dir)
    shutil.copytree(config.USERSDIRECTORY, os.path.join(work_dir, "users"), dirs_exist_ok=True)
    return work_dir

def copy_articles(work_dir=None):
    if not os.path.exists(config.BACKUPDIRECTORY):
        os.mkdir(config.BACKUPDIRECTORY)
    if not work_dir:
        work_dir = os.path.join(config.BACKUPDIRECTORY, datetime.now().strftime("%Y-%m-%d %H.%M.%S"))
        os.mkdir(work_dir)
    shutil.copytree(config.ARTICLEDIRECTORY, os.path.join(work_dir, "articles"), dirs_exist_ok=True)
    return work_dir

def backup(work_dir):
    shutil.make_archive(work_dir, 'zip', root_dir=work_dir,)
    shutil.rmtree(work_dir)
    return

def init_users():
    shutil.rmtree(config.USERSDIRECTORY, ignore_errors=True)
    os.mkdir(config.USERSDIRECTORY)
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE users (
                            user_id INTEGER PRIMARY KEY,
                            name TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            page TEXT NOT NULL,
                            avatar TEXT,
                            blocked_tags TEXT)
    """)
    connection.close()
    return

def init_articles():
    shutil.rmtree(config.ARTICLEDIRECTORY, ignore_errors=True)
    os.mkdir(config.ARTICLEDIRECTORY)
    connection = sqlite3.connect(config.ARTICLESDB)
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE articles (
                            article_id INTEGER PRIMARY KEY,
                            likes_count INTEGER,
                            comments_count INTEGER,
                            preview JSON NOT NULL,
                            tags TEXT)
    """)
    connection.close()
    return

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-b', '--backup', action='store_true', help="Create a backup copy of the all server databases at ../backup location")
parser.add_argument('--backup-users', action='store_true', help="Create a backup copy of the users databases at ../backup location")
parser.add_argument('--backup-articles', action='store_true', help="Create a backup copy of the articles databases at ../backup location")
parser.add_argument('-i', '--init', action='store_true', help="Create all server databases. Existing databases will be deleted")
parser.add_argument('--init-users', action='store_true', help="Create all users databases. Existing database will be deleted")
parser.add_argument('--init-articles', action='store_true', help="Create all articles databases. Existing database will be deleted")

flags = vars(parser.parse_args(sys.argv[1:]))

if flags["backup"]:
    work_dir = copy_users()
    copy_articles(work_dir)
    backup(work_dir)
else:
    if flags["backup_users"]:
        work_dir = copy_users()
        backup(work_dir)

    if flags["backup_articles"]:
        work_dir = copy_articles()
        backup(work_dir)

if flags["init"]:
    init_users()
    init_articles()
else:
    if flags["init_users"]:
        init_users()

    if flags["init_articles"]:
        init_articles()

api.run_server()
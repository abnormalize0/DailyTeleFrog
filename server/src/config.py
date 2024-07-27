'''
Этот файл служит для хранения кофигурации сервера. Например, путей к базам данных.
'''

import os

class DynamicPath():
    def __init__(self, *args):
        self.endpont = args

    @property
    def path(self):
        return os.path.join(os.getcwd(), *self.endpont)

current_directory = os.getcwd()
backup_directory = DynamicPath('backup')

db_user_directory = DynamicPath('db', 'users')
db_user = DynamicPath('db', 'users', 'users.db')
db_article_directory = DynamicPath('db', 'articles')
db_article = DynamicPath('db', 'articles', 'articles.db')
db_comment_directory = DynamicPath('db', 'comments')
db_comment = DynamicPath('db', 'comments', 'comments.db')

log_directory = DynamicPath('log')
log_server_api = DynamicPath('log', 'server_api.log')
log_db_api = DynamicPath('log', 'db_api.log')

delimiter = '~'
articles_per_page = 5

user_id_name = 'username'
user_table_name = 'users'

article_id_name = 'article_id'
article_table_name = 'articles'

comment_id_name = 'comment_id'
comment_table_name = 'comments'

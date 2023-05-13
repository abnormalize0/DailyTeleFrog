import sqlite3
import json

from . import config


def unblocked_article_request(blocked_tags=None):
    request = 'SELECT article_id FROM articles'
    if not blocked_tags:
        return request
    request += " WHERE tags NOT LIKE '%{0}{1}{0}%'".format(config.DELIMITER, blocked_tags[0]) 
    for tag in blocked_tags[1:]:
        request += " AND tags NOT LIKE '%{0}{1}{0}%'".format(config.DELIMITER, tag)
    return request

def get_unblocked_artiles(blocked_tags=None):
    unblocked_artiles = []
    connection = sqlite3.connect(config.ARTICLESDB)
    cursor = connection.cursor()
    select = unblocked_article_request(blocked_tags)
    select = cursor.execute(select)
    unblocked_artiles = select.fetchall()
    connection.close()
    return [_[0] for _ in unblocked_artiles]

def get_user_blocked_tags(user_id):
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()
    select = 'SELECT blocked_tags FROM users WHERE user_id = {0}'.format(user_id)
    select = cursor.execute(select)
    bloked_tags = select.fetchall()
    connection.close()
    print(bloked_tags)
    if bloked_tags[0][0]:
        bloked_tags = bloked_tags[0][0].split(config.DELIMITER)[1:-1]
    return bloked_tags

def tags_to_str(tags):
    tags_str = config.DELIMITER
    for tag in tags:
        tags_str += str(tag) + config.DELIMITER
    return tags_str

def create_db_entry(preview):
    tags = preview.pop('tags')
    tags = tags_to_str(tags)
    connection = sqlite3.connect(config.ARTICLESDB)
    cursor = connection.cursor()
    select = "INSERT INTO articles (preview, tags) VALUES ('{0}', '{1}')".format(json.dumps(preview), tags)
    cursor.execute(select)
    connection.commit()
    article_id = cursor.lastrowid
    connection.close()
    return article_id

def get_author_preview(user_id):
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()
    select = 'SELECT name, page, avatar FROM users WHERE user_id = {0}'.format(user_id)
    select = cursor.execute(select)
    db_info = select.fetchall()
    connection.close()
    author_preview = {}
    author_preview['user_id'] = user_id
    author_preview['name'] = db_info[0][0]
    author_preview['page'] = db_info[0][1]
    author_preview['avatar'] = db_info[0][2]
    return author_preview

def get_likes_comments_count(article_id):
    connection = sqlite3.connect(config.ARTICLESDB)
    cursor = connection.cursor()
    select = 'SELECT likes_count, comments_count FROM articles WHERE article_id = {0}'.format(article_id)
    select = cursor.execute(select)
    select = select.fetchall()
    return select[0][0], select[0][1]

def update_field(user_id, field_name, field_value):
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()
    update = "UPDATE users SET {0} = '{1}' WHERE user_id = {2}".format(field_name, 
                                                                      field_value, 
                                                                      user_id)
    cursor.execute(update)
    connection.commit()
    connection.close()

def add_user(user_info):
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()

    '''
    select return info about all column in %TABLE_NAME%:
    'id' (number of column in result)
    'name' (its name); 
    'type' (data type if given, else ''); 
    'notnull' (whether or not the column can be NULL); 
    'dflt_value' (the default value for the column);
    'pk' (either zero for columns that are not part of the primary key, 
          or the 1-based index of the column within the primary key)
    '''
    columns = cursor.execute("SELECT * FROM pragma_table_info('users')")
    columns = columns.fetchall()
    
    required_columns = [column_info[1] for column_info in columns if column_info[3]]
    required_column_names = ''
    for column_name in required_columns:
        required_column_names += column_name + ', '
    required_column_names = required_column_names[:-2]

    required_columns_values = ''
    for column_name in required_columns:
        required_columns_values += '"' + str(user_info[column_name]) + '", '
    required_columns_values = required_columns_values[:-2]
    select = 'INSERT INTO users ({0}) VALUES ({1})'.format(required_column_names,
                                                        required_columns_values)
    cursor.execute(select)
    
    connection.commit()
    user_id = cursor.lastrowid

    nonrequired_columns = [column_info[1] for column_info in columns if not column_info[3]]
    for column_name in nonrequired_columns:
        if column_name in user_info.keys():
            update_field(user_id, column_name, user_info[column_name])

    connection.close()
    return user_id

def check_password(password, user_id):
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()
    select = 'SELECT password FROM users WHERE user_id = {0}'.format(user_id)
    stored_password = cursor.execute(select)
    return password == stored_password

def change_password(password, user_id):
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()
    update = 'UPDATE users SET password = {0} WHERE user_id = {1}'.format(password, user_id)
    cursor.execute(update)
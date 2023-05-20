import sqlite3
import json
import os

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
    select = """INSERT INTO articles (preview, tags, likes_count, likes_id) 
                VALUES ('{0}', '{1}', '{2}', '{3}')""".format(json.dumps(preview), tags, '0', '')
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

def get_article_likes_comments(article_id):
    connection = sqlite3.connect(config.ARTICLESDB)
    cursor = connection.cursor()
    select = 'SELECT likes_count, comments_count FROM articles WHERE article_id = {0}'.format(article_id)
    select = cursor.execute(select)
    select = select.fetchall()
    return select[0][0], select[0][1]

def update_field(db, table_name, id_name, id_value, field_name, field_value):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    update = "UPDATE {0} SET {1} = '{2}' WHERE {3} = {4}".format(table_name,
                                                                 field_name,
                                                                 field_value,
                                                                 id_name,
                                                                 id_value)
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
            update_field(config.USERSDB,
                         config.USERSTABLENAME,
                         config.USERSIDNAME,
                         user_id,
                         column_name, 
                         user_info[column_name])
    connection.close()
    return user_id

def check_password(password, user_id):
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()
    select = 'SELECT password FROM users WHERE user_id = {0}'.format(user_id)
    stored_password = cursor.execute(select)
    connection.close()
    return password == stored_password

def change_password(password, user_id):
    connection = sqlite3.connect(config.USERSDB)
    cursor = connection.cursor()
    update = 'UPDATE users SET password = {0} WHERE user_id = {1}'.format(password, user_id)
    cursor.execute(update)
    connection.close()

def set_likes_on_article(id, likes_count):
    article = None
    with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(id)), encoding="utf-8") as file:
        article = json.load(file)
    article['likes_count'] = likes_count
    with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(id)), 'w', encoding="utf-8") as file:
        json.dump(article, file, ensure_ascii=False, indent=4)

def find_comment(root_comment, likes_count, id):
    if root_comment['id'] == int(id):
        root_comment['likes_count'] = likes_count
        return True, root_comment
    for index, child_comment in enumerate(root_comment['answers']):
        is_changed, changed_comments = find_comment(child_comment, likes_count, id)
        if is_changed:
            root_comment['answers'][index] = changed_comments
            return True, root_comment
    return False, None

def set_likes_on_comment(file_name, id, likes_count):
    article = None
    with open(file_name, encoding="utf-8") as file:
        article = json.load(file)
    for index, root_comment in enumerate(article['comments']):
        is_changed, changed_comments = find_comment(root_comment, likes_count, id)
        if is_changed:
            article['comments'][index] = changed_comments
            break
    with open(file_name, 'w', encoding="utf-8") as file:
        json.dump(article, file, ensure_ascii=False, indent=4)
    return

def like(db, table_name, id_name, id, user_id):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    select = 'SELECT likes_id FROM {0} WHERE {1} = {2}'.format(table_name, id_name, id)
    select = cursor.execute(select)
    select = select.fetchall()[0][0]
    if not select:
        select = ''
    change = 1

    if user_id not in select.split(config.DELIMITER):
        update_field(db,
                     table_name,
                     id_name,
                     id,
                     'likes_id',
                     select + '{0}{1}{0}'.format(config.DELIMITER, user_id))
    else:
        update_field(db,
                     table_name,
                     id_name,
                     id,
                     'likes_id',
                     select.replace('{0}{1}{0}'.format(config.DELIMITER, user_id), ''))
        change = -1

    select = 'SELECT likes_count FROM {0} WHERE {1} = {2}'.format(table_name, id_name, id)
    select = cursor.execute(select)
    select = select.fetchall()[0][0]
    likes_count = select + change
    update_field(db,
                 table_name,
                 id_name,
                 id,
                 'likes_count',
                 likes_count)
    connection.close()

    if db == config.ARTICLESDB:
        set_likes_on_article(id, likes_count)
    if db == config.COMMENTSDB:
        connection = sqlite3.connect(db)
        cursor = connection.cursor()
        select = 'SELECT article_id FROM {0} WHERE {1} = {2}'.format(table_name, id_name, id)
        select = cursor.execute(select)
        select = select.fetchall()[0][0]
        file_name = os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(select))
        set_likes_on_comment(file_name, id, likes_count)

def get_comment_likes(comment_id):
    connection = sqlite3.connect(config.COMMENTSDB)
    cursor = connection.cursor()
    select = 'SELECT likes_count FROM {0} WHERE {1} = {2}'.format(config.COMMENTSTABLENAME,
                                                                  config.COMMENTSIDNAME,
                                                                  comment_id)
    select = cursor.execute(select)
    select = select.fetchall()
    connection.close()
    return select[0][0]

def create_comment(article_id, user_id):
    connection = sqlite3.connect(config.COMMENTSDB)
    cursor = connection.cursor()
    select = '''INSERT INTO {0} (likes_count, 
    likes_id, 
    article_id, 
    author_id) VALUES ("{1}", "{2}", "{3}", "{4}")'''.format(config.COMMENTSTABLENAME, 
                                                     '1',
                                                     config.DELIMITER + str(user_id) + config.DELIMITER,
                                                     str(article_id),
                                                     str(user_id))
    cursor.execute(select)
    connection.commit()
    comment_id = cursor.lastrowid
    connection.close()
    return comment_id

def add_answer(root, comment, root_id):
    if root['id'] == int(root_id):
        root['answers'].append(comment)
        return True, root
    for index, child_root in enumerate(root['answers']):
        is_changed, changed_comments = add_answer(child_root, comment, root_id)
        if is_changed:
            root['answers'][index] = changed_comments
            return True, root
    return False, None

def add_comment(article_id, root_id, comment_text, user_id):

    comment_id = create_comment(article_id, user_id)
    comment = {'comment_text': comment_text,
               'author_id': user_id,
               'likes_count': 1,
               'id': comment_id,
               'answers': []}

    file_name = os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(article_id))
    article = None
    with open(file_name) as file:
        article = json.load(file)
    if int(root_id) == -1:
        article['comments'].append(comment)
    else:
        for index, root in enumerate(article['comments']):
            is_added, changed_answers = add_answer(root, comment, root_id)
            if is_added:
                article['comments'][index] = changed_answers
                break

    with open(file_name, 'w') as file:
        json.dump(article, file, ensure_ascii=False, indent=4)

    return comment_id
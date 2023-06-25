
import json
import os

from . import worker
from .. import config

def check_password(password, user_id):
    data = worker.get_entry_data(config.USERSDB, 
                                 config.USERSTABLENAME,
                                 ['password'],
                                 id_name=config.USERSIDNAME,
                                 id_value=user_id)
    stored_password = data['password']
    return password == stored_password

def change_password(password, user_id):
    worker.update_entry(config.USERSDB,
                        config.USERSTABLENAME,
                        config.USERSIDNAME,
                        user_id,
                        'password',
                        password)

def get_author_preview(user_id):
    author_preview = worker.get_entry_data(config.USERSDB,
                          config.USERSTABLENAME,
                          ['name', 'page', 'avatar', config.USERSIDNAME],
                          id_name=config.USERSIDNAME,
                          id_value=user_id)
    return author_preview

def get_user_blocked_tags(user_id):
    data = worker.get_entry_data(config.USERSDB,
                                 config.USERSTABLENAME,
                                 ['blocked_tags'],
                                 id_name=config.USERSIDNAME,
                                 id_value=user_id)

    bloked_tags = None
    if 'blocked_tags'  in data.keys() and data['blocked_tags']:
        bloked_tags = data['blocked_tags'].split(config.DELIMITER)[1:-1]
    return bloked_tags

def get_unblocked_artiles(blocked_tags=None):
    exclude_data = None
    if blocked_tags:
        exclude_data = {'tags': blocked_tags}
    articles_id = worker.get_entry_data(config.ARTICLESDB,
                                        config.ARTICLESTABLENAME,
                                        [config.ARTICLESIDNAME],
                                        exclude=exclude_data)
    return articles_id[config.ARTICLESIDNAME]

def get_likes_comments_from_article(article_id):
    likes_and_comments_count = worker.get_entry_data(config.USERSDB,
                                                     config.USERSTABLENAME,
                                                     ['likes_count', 'comments_count'],
                                                     id_name=config.USERSIDNAME,
                                                     id_value=article_id)
    return likes_and_comments_count['likes_count'], likes_and_comments_count['comments_count']

def get_likes_from_comment(comment_id):
    likes_count = worker.get_entry_data(config.COMMENTSDB,
                                        config.COMMENTSTABLENAME,
                                        ['likes_count'],
                                        id_name=config.COMMENTSIDNAME,
                                        id_value=comment_id)
    return likes_count['likes_count']

def create_comment(article_id, user_id):
    comment = {'author_id': user_id,
               'likes_count': 1,
               'likes_id': config.DELIMITER + str(user_id) + config.DELIMITER,
               'article_id': article_id}
    data = worker.add_entry(config.COMMENTSDB,
                            config.COMMENTSTABLENAME,
                            config.COMMENTSIDNAME,
                            comment)
    return data['id']

def append_answer_to_comment(root, comment, root_id):
    for index, child_root in enumerate(root['answers']):
        if child_root['id'] == root_id:
            child_root['answers'].append(comment)
            return True, child_root
        is_changed, changed_coments = append_answer_to_comment(child_root, comment, root_id)
        if is_changed:
            return True, changed_coments
    return False, None

def add_comment(article_id, root_id, comment_text, user_id):

    comment_id = create_comment(article_id, user_id)
    comment = {'comment_text': comment_text,
               'author_id': user_id,
               'likes_count': 1,
               'likes_id': config.DELIMITER + str(user_id) + config.DELIMITER,
               'id': comment_id,
               'answers': []}

    file_name = os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(article_id))
    article = None
    with open(file_name) as file:
        article = json.load(file)
    if int(root_id) == -1:
        article['answers'].append(comment)
    else:
        append_answer_to_comment(article, comment, root_id)

    with open(file_name, 'w') as file:
        json.dump(article, file, ensure_ascii=False, indent=4)

    return comment_id

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

def set_likes_on_article(id, likes_count):
    article = None
    with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(id)), encoding="utf-8") as file:
        article = json.load(file)
    article['likes_count'] = likes_count
    with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(id)), 'w', encoding="utf-8") as file:
        json.dump(article, file, ensure_ascii=False, indent=4)

def like(db, table_name, id_name, id, user_id):
    data = worker.get_entry_data(db,
                                 table_name,
                                 ['likes_id', 'likes_count'],
                                 id_name=id_name,
                                 id_value=id)

    select = data['likes_id']
    current_likes_count = data['likes_count']
    if not select:
        select = ''
    change = 1

    if user_id not in select.split(config.DELIMITER):
        worker.update_entry(db,
                     table_name,
                     id_name,
                     id,
                     'likes_id',
                     select + '{0}{1}{0}'.format(config.DELIMITER, user_id))
    else:
        worker.update_entry(db,
                     table_name,
                     id_name,
                     id,
                     'likes_id',
                     select.replace('{0}{1}{0}'.format(config.DELIMITER, user_id), ''))
        change = -1
    
    likes_count = current_likes_count + change
    worker.update_entry(db,
                 table_name,
                 id_name,
                 id,
                 'likes_count',
                 likes_count)

    if db == config.ARTICLESDB:
        set_likes_on_article(id, likes_count)
    if db == config.COMMENTSDB:
        article_id = worker.get_entry_data(db,
                                           table_name,
                                           ['article_id'],
                                           id_name=id_name,
                                           id_value=id)

        file_name = os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(article_id['article_id']))
        set_likes_on_comment(file_name, id, likes_count)

def post_article_to_db(preview):
    article_id = worker.add_entry(config.ARTICLESDB,
                                  config.ARTICLESTABLENAME,
                                  config.ARTICLESIDNAME,
                                  preview)
    return article_id['id']

def add_user(info):
    user_id = worker.add_entry(config.USERSDB,
                               config.USERSTABLENAME,
                               config.USERSIDNAME,
                               info)
    return user_id

def update_user_info(field_name, field_value, user_id):
    worker.update_entry(config.USERSDB,
                        config.USERSTABLENAME,
                        config.USERSIDNAME,
                        user_id,
                        field_name,
                        field_value)
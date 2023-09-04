import json
import os

from . import worker
from .. import config

def check_password(password, user_id):
    status, data = worker.get_entry_data(config.USERSDB,
                                         config.USERSTABLENAME,
                                         ['password'],
                                         id_name=config.USERSIDNAME,
                                         id_value=user_id)
    if status.is_error:
        return status, None
    stored_password = data['password']
    return status, password == stored_password

def change_password(password, user_id):
    status = worker.update_entry(config.USERSDB,
                                 config.USERSTABLENAME,
                                 config.USERSIDNAME,
                                 user_id,
                                 'password',
                                 password)
    return status

def get_author_preview(user_id):
    status, author_preview = worker.get_entry_data(config.USERSDB,
                                                   config.USERSTABLENAME,
                                                   ['name', 'page', 'avatar', config.USERSIDNAME],
                                                   id_name=config.USERSIDNAME,
                                                   id_value=user_id)
    return status, author_preview

def get_user_blocked_tags(user_id):
    status, data = worker.get_entry_data(config.USERSDB,
                                         config.USERSTABLENAME,
                                         ['blocked_tags'],
                                         id_name=config.USERSIDNAME,
                                         id_value=user_id)
    if status.is_error:
        return status, None

    bloked_tags = None

    if data['blocked_tags']:
        bloked_tags = data['blocked_tags'].split(config.DELIMITER)[1:-1]
    return status, bloked_tags

def get_unblocked_articles(blocked_tags=None):
    exclude_data = None
    if blocked_tags:
        exclude_data = {'tags': blocked_tags}
    status, articles_id = worker.get_entry_data(config.ARTICLESDB,
                                                config.ARTICLESTABLENAME,
                                                [config.ARTICLESIDNAME],
                                                exclude=exclude_data)
    return status, articles_id[config.ARTICLESIDNAME]

def get_likes_comments_from_article(article_id):
    status, data = worker.get_entry_data(config.ARTICLESDB,
                                         config.ARTICLESTABLENAME,
                                         ['likes_count', 'comments_count'],
                                         id_name=config.ARTICLESIDNAME,
                                         id_value=article_id)
    return status, data['likes_count'], data['comments_count']

def get_likes_from_comment(comment_id):
    status, likes_count = worker.get_entry_data(config.COMMENTSDB,
                                                config.COMMENTSTABLENAME,
                                                ['likes_count'],
                                                id_name=config.COMMENTSIDNAME,
                                                id_value=comment_id)
    return status, likes_count['likes_count']

def create_comment(article_id, user_id):
    comment = {'author_id': user_id,
               'likes_count': 1,
               'likes_id': config.DELIMITER + str(user_id) + config.DELIMITER,
               'article_id': article_id}
    status, comment_id = worker.add_entry(config.COMMENTSDB,
                                    config.COMMENTSTABLENAME,
                                    comment)
    if status.is_error:
        return status, None
    return status, comment_id

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
    status, comment_id = create_comment(article_id, user_id)
    if status.is_error:
        return status, None
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
        _, answers = append_answer_to_comment(article, comment, root_id)
        article['answers'] = answers

    with open(file_name, 'w') as file:
        json.dump(article, file, ensure_ascii=False, indent=4)

    return status, comment_id

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
    status, data = worker.get_entry_data(db,
                                         table_name,
                                         ['likes_id', 'likes_count'],
                                         id_name=id_name,
                                         id_value=id)
    if status.is_error:
        return status

    select = data['likes_id']
    current_likes_count = data['likes_count']
    if not select:
        select = ''
    change = 1

    if str(user_id) not in select.split(config.DELIMITER):
        status = worker.update_entry(db,
                                     table_name,
                                     id_name,
                                     id,
                                     'likes_id',
                                     select + '{0}{1}{0}'.format(config.DELIMITER, user_id))
        if status.is_error:
            return status
    else:
        status = worker.update_entry(db,
                                     table_name,
                                     id_name,
                                     id,
                                     'likes_id',
                                     select.replace('{0}{1}{0}'.format(config.DELIMITER, user_id), ''))
        if status.is_error:
            return status
        change = -1

    likes_count = current_likes_count + change
    status = worker.update_entry(db,
                                 table_name,
                                 id_name,
                                 id,
                                 'likes_count',
                                 likes_count)
    if status.is_error:
        return status

    if db == config.ARTICLESDB:
        set_likes_on_article(id, likes_count)
    if db == config.COMMENTSDB:
        status, article_id = worker.get_entry_data(db,
                                           table_name,
                                           ['article_id'],
                                           id_name=id_name,
                                           id_value=id)
        if status.is_error:
            return status
        file_name = os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(article_id['article_id']))
        set_likes_on_comment(file_name, id, likes_count)

    return status

def post_article_to_db(article):
    status, article_id = worker.add_entry(config.ARTICLESDB,
                                          config.ARTICLESTABLENAME,
                                          article)
    return status, article_id

def add_user(info):
    status, user_id = worker.add_entry(config.USERSDB,
                                       config.USERSTABLENAME,
                                       info)
    return status, user_id

def update_user_info(field_name, field_value, user_id):
    status = worker.update_entry(config.USERSDB,
                                 config.USERSTABLENAME,
                                 config.USERSIDNAME,
                                 user_id,
                                 field_name,
                                 field_value)
    return status
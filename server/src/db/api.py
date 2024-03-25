"""
Этот файл служит для хранения логики выполнения запросов, не связанной с изменениями в базах данных.
Также в этом файле производится постобработка выполненных запросов к базам данных.
Постобработка включает в себя приведение типов данных к нужным.
"""

import json
import os
import time

from . import worker
from .. import config
from .. import request_status


def check_password(password, user_id=None, email=None):
    status = None
    data = None
    if user_id:
        status, data = worker.get_entry_data(config.db_user.path,
                                             config.user_table_name,
                                             ['password'],
                                             id_name=config.user_id_name,
                                             id_value=user_id)
    else:
        status, data = worker.get_entry_data(config.db_user.path,
                                             config.user_table_name,
                                             ['password'],
                                             id_name='email',
                                             id_value=email)
    if status.is_error:
        return status, False
    stored_password = data['password']
    return status, password == stored_password


def change_password(password, user_id):
    status = worker.update_entry(config.db_user.path,
                                 config.user_table_name,
                                 config.user_id_name,
                                 user_id,
                                 'password',
                                 password)
    return status


def get_unblocked_articles(user_id, include_nonsub, sort_column, sort_direction, include, exclude, bounds):
    status = None
    data = {}
    if user_id == 0:
        status = request_status.Status(request_status.StatusType.OK)
    else:
        status, data = worker.get_entry_data(config.db_user.path,
                                             config.user_table_name,
                                             ['blocked_tags', 'blocked_users', 'blocked_communities'],
                                             id_name=config.user_id_name,
                                             id_value=user_id)
    if status.is_error:
        return status, None

    blocked_tags = []
    blocked_users = []
    blocked_communities = []

    if data.get('blocked_tags'):
        blocked_tags = data['blocked_tags'].split(config.delimiter)[1:-1]
    if exclude and 'tags' in exclude.keys():
        blocked_tags.extend(exclude['tags'])
    if data.get('blocked_users'):
        blocked_users = data['blocked_users'].split(config.delimiter)[1:-1]
    if exclude and 'users' in exclude.keys():
        blocked_users.extend(exclude['users'])
    if data.get('blocked_communities'):
        blocked_communities = data['blocked_communities'].split(config.delimiter)[1:-1]
    if exclude and 'communities' in exclude.keys():
        blocked_communities.extend(exclude['communities'])

    if status.is_error:
        return status, None

    exclude_data = {}
    if blocked_tags:
        exclude_data['tags'] = blocked_tags
    if blocked_users:
        exclude_data['users'] = blocked_users
    if blocked_communities:
        exclude_data['communities'] = blocked_communities

    status, articles_id = worker.get_entry_data(config.db_article.path,
                                                config.article_table_name,
                                                [config.article_id_name],
                                                include_nonsub=include_nonsub,
                                                include=include,
                                                exclude=exclude_data,
                                                bounds=bounds,
                                                sort_column=sort_column,
                                                sort_direction=sort_direction,
                                                user_id=user_id)

    if status.is_error:
        return status, None

    if type(articles_id[config.article_id_name]) is not list:
        articles_id[config.article_id_name] = [articles_id[config.article_id_name]]
    return status, articles_id[config.article_id_name]


def create_comment(article_id, user_id):
    comment = {'author_id': user_id,
               'creation_date': round(time.time() * 1000),
               'rating': 0,
               'likes_count': 0,
               'likes_id': '',
               'dislikes_count': 0,
               'dislikes_id': '',
               'article_id': article_id}
    status, comment_id = worker.add_entry(config.db_comment.path,
                                          config.comment_table_name,
                                          comment)
    if status.is_error:
        return status, None, None
    return status, comment_id, comment['creation_date']


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
    status, comment_id, creation_date = create_comment(article_id, user_id)
    if status.is_error:
        return status, None
    comment = {'comment_text': comment_text,
               'creation_date': creation_date,
               'author_id': user_id,
               'rating': 0,
               'likes_count': 0,
               'dislikes_count': 0,
               'id': comment_id,
               'answers': []}

    file_name = os.path.join(config.db_article_directory.path, f'{article_id}.json')
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


def find_comment(root_comment, vote_count, vote_type, id):
    if root_comment['id'] == int(id):
        root_comment[vote_type] = vote_count
        return True, root_comment
    for index, child_comment in enumerate(root_comment['answers']):
        is_changed, changed_comments = find_comment(child_comment, vote_count, id)
        if is_changed:
            root_comment['answers'][index] = changed_comments
            return True, root_comment
    return False, None


def set_vote_on_comment(file_name, id, vote_count, vote_type):
    article = None
    with open(file_name, encoding="utf-8") as file:
        article = json.load(file)
    for index, root_comment in enumerate(article['answers']):
        is_changed, changed_comments = find_comment(root_comment, vote_count, vote_type, id)
        if is_changed:
            article['answers'][index] = changed_comments
            break
    with open(file_name, 'w', encoding="utf-8") as file:
        json.dump(article, file, ensure_ascii=False, indent=4)


def set_vote_on_article(id, vote_count, vote_type):
    article = None
    with open(os.path.join(config.db_article_directory.path, f'{id}.json'), encoding="utf-8") as file:
        article = json.load(file)
    article[vote_type] = vote_count
    with open(os.path.join(config.db_article_directory.path, f'{id}.json'), 'w', encoding="utf-8") as file:
        json.dump(article, file, ensure_ascii=False, indent=4)


def vote(db, table_name, id_name, id, user_id, vote_type):
    status, data = worker.get_entry_data(db,
                                         table_name,
                                         ['likes_id', 'likes_count', 'author_id', 'dislikes_count', 'dislikes_id'],
                                         id_name=id_name,
                                         id_value=id)
    if status.is_error:
        return status

    author_id = data['author_id']

    if user_id == author_id:
        return request_status.Status(request_status.StatusType.ERROR, request_status.ErrorType.ValueError,
                                     msg='User tries to like or dislike their own comment or article')

    reverse_vote = 'dislikes'
    if vote_type == 'dislikes':
        reverse_vote = 'likes'

    vote_id = data[vote_type + '_id']
    vote_count = data[vote_type + '_count']
    reverse_vote_id = data[reverse_vote + '_id']
    reverse_vote_count = data[reverse_vote + '_count']
    is_have_reverse_vote = False

    # user set like on disliked post/comment or dislike on liked post/comment
    if reverse_vote_id and str(user_id) in reverse_vote_id.split(config.delimiter):
        status = worker.update_entry(db,
                                     table_name,
                                     id_name,
                                     id,
                                     reverse_vote + '_id',
                                     reverse_vote_id.replace(f'{config.delimiter}{user_id}{config.delimiter}', ''))
        if status.is_error:
            return status

        status = worker.update_entry(db,
                                     table_name,
                                     id_name,
                                     id,
                                     reverse_vote + '_count',
                                     reverse_vote_count - 1)
        if status.is_error:
            return status
        is_have_reverse_vote = True

    if not vote_id:
        vote_id = ''
    change = 1

    if str(user_id) not in vote_id.split(config.delimiter):
        status = worker.update_entry(db,
                                     table_name,
                                     id_name,
                                     id,
                                     vote_type + '_id',
                                     vote_id + f'{config.delimiter}{user_id}{config.delimiter}')
        if status.is_error:
            return status
    else:
        status = worker.update_entry(db,
                                     table_name,
                                     id_name,
                                     id,
                                     vote_type + '_id',
                                     vote_id.replace(f'{config.delimiter}{user_id}{config.delimiter}', ''))
        if status.is_error:
            return status
        change = -1

    # update posts/comments author rating
    status, old_rating = worker.get_entry_data(config.db_user.path,
                                               config.user_table_name,
                                               ['rating'],
                                               config.user_id_name,
                                               author_id)
    old_rating = old_rating['rating']
    if vote_type == 'likes':
        new_rating = old_rating + change * (1 + int(is_have_reverse_vote))
    else:
        new_rating = old_rating - change * (1 + int(is_have_reverse_vote))

    status = worker.update_entry(config.db_user.path,
                                 config.user_table_name,
                                 config.user_id_name,
                                 author_id,
                                 'rating',
                                 new_rating)
    if status.is_error:
        return status

    # update likes/dislikes count
    new_vote_count = vote_count + change
    status = worker.update_entry(db,
                                 table_name,
                                 id_name,
                                 id,
                                 vote_type + '_count',
                                 new_vote_count)
    if status.is_error:
        return status

    status, likes_dislikes = worker.get_entry_data(db, table_name, ['likes_count', 'dislikes_count'], id_name, id)
    if status.is_error:
        return status

    status = worker.update_entry(db,
                                 table_name,
                                 id_name,
                                 id,
                                 'rating',
                                 likes_dislikes['likes_count'] - likes_dislikes['dislikes_count'])
    if status.is_error:
        return status

    if db == config.db_article.path:
        set_vote_on_article(id, new_vote_count, vote_type + '_count')
        if is_have_reverse_vote:
            set_vote_on_article(id, reverse_vote_count - 1, reverse_vote + '_count')
    if db == config.db_comment.path:
        status, article_id = worker.get_entry_data(db,
                                                   table_name,
                                                   ['article_id'],
                                                   id_name=id_name,
                                                   id_value=id)
        if status.is_error:
            return status
        file_name = os.path.join(config.db_article_directory.path, f'{article_id["article_id"]}.json')
        set_vote_on_comment(file_name, id, new_vote_count, vote_type + '_count')
        if is_have_reverse_vote:
            set_vote_on_comment(file_name, id, reverse_vote_count - 1, reverse_vote + '_count')

    return status


def post_article_to_db(article):
    status, article_id = worker.add_entry(config.db_article.path,
                                          config.article_table_name,
                                          article)
    return status, article_id


def add_user(info):
    status, user_id = worker.add_entry(config.db_user.path,
                                       config.user_table_name,
                                       info)
    return status, user_id


def user_update_info(field_name, field_value, user_id):
    status = worker.update_entry(config.db_user.path,
                                 config.user_table_name,
                                 config.user_id_name,
                                 user_id,
                                 field_name,
                                 field_value)
    return status


def article_get_data(article_id, requested_data):
    status, data = worker.get_entry_data(config.db_article.path,
                                         config.article_table_name,
                                         requested_data,
                                         config.article_id_name,
                                         article_id)
    return status, data


def user_get_data(user_id, requested_data):
    status, data = worker.get_entry_data(config.db_user.path,
                                         config.user_table_name,
                                         requested_data,
                                         config.user_id_name,
                                         user_id)
    return status, data

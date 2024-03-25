'''
Этот файл служит для хранения логики выполнения запросов, не связанной с изменениями в базах данных.
'''

import json
import os
import time

from .db import api
from . import config
from . import request_status


def get_page_articles(index, user_id, include_nonsub, sort_column, sort_direction, include, exclude, bounds):
    status, articles = api.get_unblocked_articles(user_id, include_nonsub, sort_column, sort_direction,
                                                  include, exclude, bounds)
    if status.is_error:
        return status, None
    page_articles = []
    if len(articles) < (index + 1) * config.articles_per_page:
        page_articles = articles[index * config.articles_per_page:]
    else:
        page_articles = articles[index * config.articles_per_page: (index + 1) * config.articles_per_page]
    return status, page_articles


def select_preview(article):
    preview = {}
    preview['name'] = article['name']
    preview['preview_content'] = article['preview_content']
    preview['tags'] = article['tags']
    preview['creation_date'] = article['creation_date']
    preview['author_preview'] = article['author_preview']
    preview['likes_count'] = article['likes_count']
    preview['likes_id'] = article['likes_id']
    preview['dislikes_count'] = article['dislikes_count']
    preview['dislikes_id'] = article['dislikes_id']
    preview['comments_count'] = article['comments_count']
    return preview


def get_page(index, user_id, include_nonsub, sort_column, sort_direction, include, exclude, bounds):
    status, page_articles = get_page_articles(index, user_id, include_nonsub, sort_column, sort_direction,
                                              include, exclude, bounds)
    if status.is_error:
        return status, None
    previews = []
    for article_id in page_articles:
        with open(os.path.join(config.db_article_directory.path,
                               f'{article_id}.json'),
                  encoding="utf-8") as file:
            article = json.load(file)
            preview = select_preview(article)
            preview['id'] = article_id
            previews.append(preview)
    return status, previews


def get_pages(indexes, user_id, include_nonsub, sort_column, sort_direction, include, exclude, bounds):
    pages = {}
    for index in indexes:
        status, page = get_page(index, user_id, include_nonsub, sort_column, sort_direction, include, exclude, bounds)
        if status.is_error:
            return status, None
        pages[index] = page
    return request_status.Status(request_status.StatusType.OK), pages


def get_article(id):
    article = None
    try:
        with open(os.path.join(config.db_article_directory.path,
                               f'{id}.json'), encoding="utf-8") as file:
            article = json.load(file)
    except FileNotFoundError:
        return None
    return article


def create_article_file(article_id, article):
    with open(os.path.join(config.db_article_directory.path,
                           f'{article_id}.json'), 'w+', encoding='utf-8') as file:
        json.dump(article, file, ensure_ascii=False, indent=4)


def post_article(article, user_id):
    status, author_preview = api.user_get_data(user_id, ['name', 'avatar'])
    if status.is_error:
        return status, None
    article['author_preview'] = author_preview
    article['author_id'] = user_id
    article['creation_date'] = round(time.time() * 1000)
    article['answers'] = []
    article['rating'] = 0
    article['likes_count'] = 0
    article['likes_id'] = ''
    article['dislikes_count'] = 0
    article['dislikes_id'] = ''
    article['comments_count'] = 0
    data = select_preview(article)
    data['author_id'] = article['author_id']
    data['creation_date'] = article['creation_date']
    data['rating'] = article['rating']
    data['likes_id'] = article['likes_id']
    data['dislikes_id'] = article['dislikes_id']
    status, article_id = api.post_article_to_db(data)
    if status.is_error:
        return status, None
    create_article_file(article_id, article)
    return status, article_id


def add_user(user_info):
    user_info['name_history'] = config.delimiter + user_info['name'] + config.delimiter
    user_info['creation_date'] = round(time.time() * 1000)
    user_info['rating'] = 0
    return api.add_user(user_info)


def update_user_info(user_info, user_id):
    exluded_fields = ['user-id', 'password']
    for field in user_info.keys():
        if field not in exluded_fields:
            status = api.user_update_info(field, user_info[field], user_id)
        else:
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.OptionError,
                                         msg=f'Wrong user parameter {field}.\
                                         You can not update this parameter by this method')
        if field == 'name' and not status.is_error:
            status, data = api.user_get_data(user_id, ['name_history'])
            name_history = data['name_history']
            name_history += user_info[field] + config.delimiter
            _ = api.user_update_info('name_history', name_history, user_id)

    return status


def login(password, email=None, user_id=None):
    return api.check_password(password, user_id=user_id, email=email)


def change_password(previous_password, new_password, user_id):
    status, is_same = api.check_password(previous_password, user_id)
    if status.is_error:
        return status
    if not is_same:
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg='Incorrect password. Password check failed!')
    status = api.change_password(new_password, user_id)

    return status


def dislike_article(article_id, user_id):
    status = api.vote(config.db_article.path,
                      config.article_table_name,
                      config.article_id_name,
                      article_id,
                      user_id,
                      'dislikes')

    return status


def like_article(article_id, user_id):
    status = api.vote(config.db_article.path,
                      config.article_table_name,
                      config.article_id_name,
                      article_id,
                      user_id,
                      'likes')

    return status


def dislike_comment(comment_id, user_id):
    status = api.vote(config.db_comment.path,
                      config.comment_table_name,
                      config.comment_id_name,
                      comment_id,
                      user_id,
                      'dislikes')

    return status


def like_comment(comment_id, user_id):
    status = api.vote(config.db_comment.path,
                      config.comment_table_name,
                      config.comment_id_name,
                      comment_id,
                      user_id,
                      'likes')

    return status


def add_comment(article_id, root, cooment_text, user_id):
    status, id = api.add_comment(article_id, root, cooment_text, user_id)

    return status, id


def get_article_data(article_id, requested_data):

    return api.article_get_data(article_id, requested_data)


def get_user_data(user_id, requested_data):

    return api.user_get_data(user_id, requested_data)

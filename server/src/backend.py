'''
Этот файл служит для хранения логики выполнения запросов, не связанной с изменениями в базах данных.
'''

import json
import os
import time

from .db import api, user
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
        page_articles = articles[index * config.articles_per_page : (index + 1) * config.articles_per_page]
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
    user.add_user(
        username=user_info["username"],
        nickname=user_info["nickname"],
        password=user_info["password"],
        creation_date=round(time.time() * 1000),
        email=user_info["email"],
        avatar=user_info["avatar"],
        description=user_info["description"]
    )

def update_user_info(user_info, username):
    for key in user_info:
        match key:
            case "avatar":
                user.update_avatar(username, user_info[key])
            case "sub-tags":
                user.sub_tag(username, user_info[key])
            case "blocked-tags":
                user.block_tag(username, user_info[key])
            case "sub-users":
                user.sub_user(username, user_info[key])
            case "blocked-users":
                user.block_user(username, user_info[key])
            case "nickname":
                user.update_nickname(username, user_info[key])
            case "email":
                user.update_email(username, user_info[key])
            case "description":
                user.update_description(username, user_info[key])

def login(password, email=None, user_id=None):
    return user.check_password(password=password, username=user_id, email=email)

def change_password(previous_password, new_password, login):
    is_same = user.check_password(previous_password, username=login)
    if not is_same:
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg='Incorrect password. Password check failed!')
    user.change_password(new_password, login)
    return request_status.Status(request_status.StatusType.OK)

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

def add_comment(article_id, root, comment_text, user_id):
    status, id = api.add_comment(article_id, root, comment_text, user_id)
    return status, id

def get_article_data(article_id, requested_data):
    return api.article_get_data(article_id, requested_data)

def get_user_data(username, requested_data):
    data: dict = {}
    for key in requested_data:
        match key:
            case "avatar":
                data[key] = user.get_avatar(username)
            case "name_history":
                data[key] = user.get_name_history(username)
            case "sub_tags":
                data[key] = user.get_sub_tag(username)
            case "blocked_tags":
                data[key] = user.get_blacklist_tag(username)
            case "sub_users":
                data[key] = user.get_sub_user(username)
            case "blocked_users":
                data[key] = user.get_blacklist_user(username)
            case "nickname":
                data[key] = user.get_nickname(username)
            case "email":
                data[key] = user.get_email(username)
            case "description":
                data[key] = user.get_description(username)
            case "creation_date":
                data[key] = user.get_creation_date(username)
            case "rating":
                data[key] = user.get_rating(username)
    return data
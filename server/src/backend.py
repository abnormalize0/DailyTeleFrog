'''
Этот файл служит для хранения логики выполнения запросов, не связанной с изменениями в базах данных.
'''

import json
import os
import time

from .db import api, user, article
from . import config
from . import request_status

def get_page_articles(index, username, include_nonsub, sort_column, sort_direction, include, exclude, bounds):
    status, articles = api.get_unblocked_articles(username, include_nonsub, sort_column, sort_direction,
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
    preview['views_count'] = article['views_count']
    preview['views_id'] = article['views_id']
    preview['opens_count'] = article['opens_count']
    preview['opens_id'] = article['opens_id']
    return preview

def get_page(index, username, include_nonsub, sort_column, sort_direction, include, exclude, bounds):
    status, page_articles = get_page_articles(index, username, include_nonsub, sort_column, sort_direction,
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

def get_pages(indexes, username, include_nonsub, sort_column, sort_direction, include, exclude, bounds):
    pages = {}
    for index in indexes:
        status, page = get_page(index, username, include_nonsub, sort_column, sort_direction, include, exclude, bounds)
        if status.is_error:
            return status, None
        pages[index] = page
    return request_status.Status(request_status.StatusType.OK), pages

def get_article(session, article_id, username):
    status, article_info = article.get_article(session, article_id)
    if status.is_error:
        return status, None
    status, preview = article.get_preview(session, article_id)
    if status.is_error:
        return status, None
    status, likes = article.get_likes(session, article_id)
    if status.is_error:
        return status, None
    status, dislikes = article.get_dislikes(session, article_id)
    if status.is_error:
        return status, None
    status, rating = article.get_rating(session, article_id)
    if status.is_error:
        return status, None
    status, comments_count = article.get_comments_count(session, article_id)
    if status.is_error:
        return status, None
    #status, comments = comment.get_comments(session, article_id)
    status, is_liked = article.is_liked(session, article_id, username)
    if status.is_error:
        return status, None
    status, is_disliked = article.is_disliked(session, article_id, username)
    if status.is_error:
        return status, None
    status, tags = article.get_tags(session, article_id)
    if status.is_error:
        return status, None
    status, views = article.get_views(session, article_id)
    if status.is_error:
        return status, None
    status, opens = article.get_opens(session, article_id)
    if status.is_error:
        return status, None
    status, is_views = article.is_views(session, article_id, username)
    if status.is_error:
        return status, None
    status, is_opens = article.is_open(session, article_id, username)
    if status.is_error:
        return status, None

    return request_status.Status(request_status.StatusType.OK), {
        "creation_date": article_info.creation_date,
        "author_preview": "author_preview",
        "title": article_info.title,
        "body": article_info.body,
        "preview": preview,
        "likes": likes,
        "dislikes": dislikes,
        "rating": rating,
        "comments_count": comments_count,
        "is_liked": is_liked,
        "is_disliked": is_disliked,
        "tags": tags,
        "views": views,
        "opens": opens,
        "is_views": is_views,
        "is_opens": is_opens,
    }


def post_article(session, author, title, body, preview, tags):
    article_id = article.add_article(
        session=session,
        title=title,
        body=body,
        author=author,
        preview=preview)
    article.add_tags(session=session, tags=tags, article_id=article_id)
    return request_status.Status(request_status.StatusType.OK), article_id

def add_user(session, user_info):
    user.add_user(
        session=session,
        username=user_info["username"],
        nickname=user_info["nickname"],
        password=user_info["password"],
        creation_date=round(time.time() * 1000),
        email=user_info["email"],
        avatar=user_info["avatar"],
        description=user_info["description"]
    )
    status = request_status.Status(request_status.StatusType.OK)
    return status

def update_user_info(session, username, data):
    for key in data:
        match key:
            case "avatar":
                status = user.update_avatar(session, username, data[key])
                if status.is_error:
                    return status
            case "sub-tags":
                status = user.sub_tag(session, username, data[key])
                if status.is_error:
                    return status
            case "blocked-tags":
                status = user.block_tag(session, username, data[key])
                if status.is_error:
                    return status
            case "sub-users":
                status = user.sub_user(session, username, data[key])
                if status.is_error:
                    return status
            case "blocked-users":
                status = user.block_user(session, username, data[key])
                if status.is_error:
                    return status
            case "nickname":
                status = user.update_nickname(session, username, data[key])
                if status.is_error:
                    return status
            case "email":
                status = user.update_email(session, username, data[key])
                if status.is_error:
                    return status
            case "description":
                status = user.update_description(session, username, data[key])
                if status.is_error:
                    return status
    return request_status.Status(request_status.StatusType.OK)

def login(session, parameters):
    password = parameters['password']
    username = parameters['username']
    email = parameters['email']
    status, is_password_correct = user.check_password(session=session, password=password, username=username, email=email)
    return status, is_password_correct

def change_password(session, previous_password, new_password, username):
    is_same = user.check_password(session, previous_password, username=username)
    if not is_same:
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg='Incorrect password!')
    user.change_password(session, new_password, username)
    return request_status.Status(request_status.StatusType.OK)

def dislike_article(article_id, username):
    status = api.vote(config.db_article.path,
                      config.article_table_name,
                      config.article_id_name,
                      article_id,
                      username,
                      'dislikes')
    return status

def like_article(article_id, username):
    status = api.vote(config.db_article.path,
                      config.article_table_name,
                      config.article_id_name,
                      article_id,
                      username,
                      'likes')
    return status

def dislike_comment(comment_id, username):
    status = api.vote(config.db_comment.path,
                      config.comment_table_name,
                      config.comment_id_name,
                      comment_id,
                      username,
                      'dislikes')
    return status

def like_comment(comment_id, username):
    status = api.vote(config.db_comment.path,
                      config.comment_table_name,
                      config.comment_id_name,
                      comment_id,
                      username,
                      'likes')
    return status

def open_article(article_id, username):
    status = api.vote(config.db_article.path,
                      config.article_table_name,
                      config.article_id_name,
                      article_id,
                      username,
                      'opens')
    return status

def view_article(article_id, username):
    status = api.vote(config.db_article.path,
                      config.article_table_name,
                      config.article_id_name,
                      article_id,
                      username,
                      'views')
    return status

def add_comment(article_id, root, comment_text, username):
    status, id = api.add_comment(article_id, root, comment_text, username)
    return status, id

def get_article_data(session, article_id, username, requested_data):
    data: dict = {}
    for key in requested_data:
        match key:
            case "likes":
                status, data[key] = article.get_likes(session, article_id)
                if status.is_error:
                    return status, None
            case "dislikes":
                status, data[key] = article.get_dislikes(session, article_id)
                if status.is_error:
                    return status, None
            case "rating":
                status, data[key] = article.get_rating(session, article_id)
                if status.is_error:
                    return status, None
            case "comments_count":
                status, data[key] = article.get_comments_count(session, article_id)
                if status.is_error:
                    return status, None
            case "creation_date":
                status, article_info = article.get_article(session, article_id)
                if status.is_error:
                    return status, None
                data[key] = article_info.creation_date
            case "tags":
                status, data[key] = article.get_tags(session, article_id)
                if status.is_error:
                    return status, None
            case "is_liked":
                status, data[key] = article.is_liked(session, article_id, username)
                if status.is_error:
                    return status, None
            case "is_disliked":
                status, data[key] = article.is_disliked(session, article_id, username)
                if status.is_error:
                    return status, None
            case "views":
                status, data[key] = article.get_views(session, article_id)
                if status.is_error:
                    return status, None
            case "opens":
                status, data[key] = article.get_opens(session, article_id)
                if status.is_error:
                    return status, None
    return request_status.Status(request_status.StatusType.OK), data

def get_user_data(session, username, requested_data):
    data: dict = {}
    for key in requested_data:
        match key:
            case "avatar":
                status, data[key] = user.get_avatar(session, username)
                if status.is_error:
                    return status, None
            case "name_history":
                status, data[key] = user.get_name_history(session, username)
                if status.is_error:
                    return status, None
            case "sub_tags":
                status, data[key] = user.get_sub_tag(session, username)
                if status.is_error:
                    return status, None
            case "blocked_tags":
                status, data[key] = user.get_blacklist_tag(session, username)
                if status.is_error:
                    return status, None
            case "sub_users":
                status, data[key] = user.get_sub_user(session, username)
                if status.is_error:
                    return status, None
            case "blocked_users":
                status, data[key] = user.get_blacklist_user(session, username)
                if status.is_error:
                    return status, None
            case "nickname":
                status, data[key] = user.get_nickname(session, username)
                if status.is_error:
                    return status, None
            case "email":
                status, data[key] = user.get_email(session, username)
                if status.is_error:
                    return status, None
            case "description":
                status, data[key] = user.get_description(session, username)
                if status.is_error:
                    return status, None
            case "creation_date":
                status, data[key] = user.get_creation_date(session, username)
                if status.is_error:
                    return status, None
            case "rating":
                status, data[key] = user.get_rating(session, username)
                if status.is_error:
                    return status, None
            case _:
                pass
    return request_status.Status(request_status.StatusType.OK), data
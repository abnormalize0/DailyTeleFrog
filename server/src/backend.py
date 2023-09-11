import json
import os

from .db import api
from . import config
from . import request_status

def get_page_articles(index, blocked_tags):
    status, articles = api.get_unblocked_articles(blocked_tags)
    if status.is_error:
        return status, None
    page_articles = []
    if len(articles) < (index + 1) * config.ARTICLES_PER_PAGE:
        page_articles = articles[index * config.ARTICLES_PER_PAGE:]
    else:
        page_articles = articles[index * config.ARTICLES_PER_PAGE : (index + 1) * config.ARTICLES_PER_PAGE]
    return status, page_articles

def select_preview(article):
    preview = {}
    preview['name'] = article['name']
    preview['preview_content'] = article['preview_content']
    preview['tags'] = article['tags']
    preview['created'] = article['created']
    preview['author_preview'] = article['author_preview']
    preview['likes_count'] = article['likes_count']
    preview['comments_count'] = article['comments_count']
    return preview

def get_page(index, blocked_tags = None):
    status, page_articles = get_page_articles(index, blocked_tags)
    if status.is_error:
        return status, None
    previews = []
    for article_id in page_articles:
        with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(article_id)), encoding="utf-8") as file:
            article = json.load(file)
            preview = select_preview(article)
            preview['id'] = article_id
            previews.append(preview)
    return status, previews

def get_pages(indexes, user_id):
    pages = {}
    status, blocked_tags = api.get_user_blocked_tags(user_id)
    if status.is_error:
        return status, None
    for index in indexes:
        status, page = get_page(index, blocked_tags)
        if status.is_error:
            return status, None
        pages[index] = page
    return request_status.Status(request_status.StatusType.OK), pages

def get_article(id):
    article = None
    with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(id)), encoding="utf-8") as file:
        article = json.load(file)
    return article

def create_article_file(article_id, article):
    with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(article_id)), 'w+', encoding='utf-8') as file:
        json.dump(article, file, ensure_ascii=False, indent=4)

def post_article(article, user_id):
    status, author_preview = api.get_author_preview(user_id)
    if status.is_error:
        return status, None
    article['author_preview'] = author_preview
    article['answers'] = []
    article['likes_count'] = 1
    article['likes_id'] = config.DELIMITER + str(user_id) + config.DELIMITER
    article['comments_count'] = 0
    article_preview = select_preview(article)
    status, article_id = api.post_article_to_db(article_preview)
    if status.is_error:
        return status, None
    create_article_file(article_id, article)
    return status, article_id

def add_user(user_info):
    return api.add_user(user_info)

def update_user_info(user_info, user_id):
    exluded_fields = ['user-id', 'name', 'password']
    for field in user_info.keys():
        if field not in exluded_fields:
            status = api.update_user_info(field, user_info[field], user_id)
        else:
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.OptionError,
                                         msg='Wrong user parameter {0}.\
                                         You can not update this parameter by this method'.format(field))
    return status

def get_article_likes_comments(article_id):
    status, likes_count, comments_count = api.get_likes_comments_from_article(article_id)
    return status, {'likes_count': likes_count, 'comments_count': comments_count}

def check_password(password, user_id):
    return api.check_password(password, user_id)

def change_password(previous_password, new_password, user_id):
    status, is_same = check_password(previous_password, user_id)
    if status.is_error:
        return status
    if not is_same:
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg='Incorrect password. Password check failed!')
    status = api.change_password(new_password, user_id)
    return status

def like_article(article_id, user_id):
    status = api.like(config.ARTICLESDB,
             config.ARTICLESTABLENAME,
             config.ARTICLESIDNAME,
             article_id,
             user_id)
    return status

def get_comment_likes(comment_id):
    status, likes_count = api.get_likes_from_comment(comment_id)
    return status, likes_count

def like_comment(comment_id, user_id):
    status = api.like(config.COMMENTSDB,
                      config.COMMENTSTABLENAME,
                      config.COMMENTSIDNAME,
                      comment_id,
                      user_id)
    return status

def article_add_comment(article_id, root, cooment_text, user_id):
    id = api.add_comment(article_id, root, cooment_text, user_id)
    return id
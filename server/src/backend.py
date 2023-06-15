import json
import os

from . import db
from . import config

def get_page_articles(index, blocked_tags):
    articles = db.get_unblocked_artiles(blocked_tags)
    page_articles = []
    if len(articles) < (index + 1) * config.ARTICLES_PER_PAGE:
        page_articles = articles[index * config.ARTICLES_PER_PAGE:]
    else:
        page_articles = articles[index * config.ARTICLES_PER_PAGE : (index + 1) * config.ARTICLES_PER_PAGE]
    return page_articles

def select_preview(article):
    preview = {}
    preview['name'] = article['name']
    preview['preview_content'] = article['preview_content']
    preview['tags'] = article['tags']
    preview['date'] = article['date']
    preview['author'] = article['author']
    return preview

def get_page(index, blocked_tags = None):
    page_articles = get_page_articles(index, blocked_tags)
    previews = []
    for article_id in page_articles:
        with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(article_id)), encoding="utf-8") as file:
            article = json.load(file)
            preview = select_preview(article)
            preview['id'] = article_id
            previews.append(preview)
    return previews

def get_pages(indexes, user_id):
    pages = {}
    blocked_tags = db.get_user_blocked_tags(user_id)
    for index in indexes:
        page = get_page(index, blocked_tags)
        pages[index] = page
    return pages

def get_article(id):
    article = None
    with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(id)), encoding="utf-8") as file:
        article = json.load(file)
    return article

def create_article_file(article_id, article):
    with open(os.path.join(config.ARTICLEDIRECTORY, '{0}.json'.format(article_id)), 'w+', encoding='utf-8') as file:
        json.dump(article, file, ensure_ascii=False, indent=4)

def post_article(article, user_id):
    author_preview = db.get_author_preview(user_id)
    article['author'] = author_preview
    article['comments'] = []
    article['likes_count'] = 0
    article_preview = select_preview(article)
    article_id = db.create_db_entry(article_preview)
    create_article_file(article_id, article)
    return article_id

def add_user(user_info):
    return db.add_user(user_info)

def update_user_info(user_info):
    exluded_fields = ['user_id', 'name', 'password']
    for field in user_info.keys():
        if field not in exluded_fields:
            db.update_field(field, user_info[field])

def get_article_likes_comments(article_id):
    likes_count, comments_count = db.get_article_likes_comments(article_id)
    return {'likes_count': likes_count, 'comments_count': comments_count}

def check_password(password, user_id):
    return db.check_password(password, user_id)

def change_password(previous_password, new_password, user_id):
    if check_password(previous_password, user_id):
        db.change_password(new_password, user_id)

def like_article(article_id, user_id):
    db.like(config.ARTICLESDB,
            config.ARTICLESTABLENAME,
            config.ARTICLESIDNAME,
            article_id,
            user_id)

def get_comment_likes(comment_id):
    likes_count = db.get_comment_likes(comment_id)
    return likes_count

def like_comment(comment_id, user_id):
    db.like(config.COMMENTSDB,
            config.COMMENTSTABLENAME,
            config.COMMENTSIDNAME,
            comment_id,
            user_id)

def article_add_comment(article_id, root, cooment_text, user_id):
    id = db.add_comment(article_id, root, cooment_text, user_id)
    return id
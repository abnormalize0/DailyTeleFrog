from . import scheme
from .. import config
from .. import request_status
import time
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import select, update, delete


def is_article_not_exist(session:Session, article_id):
    article = session.query(scheme.Article).where(scheme.Article.id == article_id).scalar()
    return article is None

def post(session, title, body, author, preview):
    article = scheme.Article(
        title=title,
        body=body,
        author_username=author,
        creation_date=round(time.time() * 1000),
    )
    session.add(article)
    session.flush()
    article_preview = scheme.ArticlePreview(
        article_id=article.id,
        preview_content=preview,
    )
    session.add(article_preview)
    session.flush()
    return article.id


def add_tags(session, tags, article_id):
    for tag in tags:
        article_tag = scheme.ArticleTag(tag_name=tag, article_id=article_id)
        session.add(article_tag)
    session.flush()


def is_liked(session:Session, article_id, username):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.OK), False
    return request_status.Status(request_status.StatusType.OK), not session.query(scheme.ArticleLike).where(scheme.ArticleLike.article_id == article_id and scheme.ArticleLike.author_username == username).scalar() is None


def is_disliked(session:Session, article_id, username):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.OK), False
    return request_status.Status(request_status.StatusType.OK), not session.query(scheme.ArticleDislike).where(scheme.ArticleDislike.article_id == article_id and scheme.ArticleDislike.author_username == username).scalar() is None



def likes_count(session:Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    likes = (
        session.query(scheme.ArticleLike)
        .where(scheme.ArticleLike.article_id == article_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), likes

def dislikes_count(session:Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    dislikes = (
        session.query(scheme.ArticleDislike)
        .where(scheme.ArticleDislike.article_id == article_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), dislikes

def rating(session:Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    likes = (
        session.query(scheme.ArticleLike)
        .where(scheme.ArticleLike.article_id == article_id)
        .count()
    )
    dislikes = (
        session.query(scheme.ArticleDislike)
        .where(scheme.ArticleDislike.article_id == article_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), likes - dislikes


def comments_count(session:Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    comments_count = (
        session.query(scheme.Comment)
        .where(scheme.Comment.article_id == article_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), comments_count


def get(session:Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    article = session.query(scheme.Article).where(scheme.Article.id == article_id).scalar()
    return request_status.Status(request_status.StatusType.OK), article


def preview(session:Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    preview = session.query(scheme.ArticlePreview.preview_content).where(scheme.ArticlePreview.article_id == article_id).scalar()
    return request_status.Status(request_status.StatusType.OK), preview


def tags(session:Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    tags = session.query(scheme.ArticleTag.tag_name).where(scheme.ArticleTag.article_id == article_id).all()
    return request_status.Status(request_status.StatusType.OK), [tag[0] for tag in tags]


def like(session:Session, article_id, username):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    existing_like = (
        session.query(scheme.ArticleLike)
        .where(
            scheme.ArticleLike.article_id == article_id
            and scheme.ArticleLike.author_username == username
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.ArticleDislike)
        .where(
            scheme.ArticleDislike.article_id == article_id
            and scheme.ArticleDislike.author_username == username
        )
        .scalar()
    )
    if existing_like:
        session.delete(existing_like)
    else:
        like = scheme.ArticleLike(article_id=article_id, author_username=username)
        session.add(like)
    if existing_dislike:
        session.delete(existing_dislike)
    session.flush()
    return request_status.Status(request_status.StatusType.OK)


def dislike(session:Session, article_id, username):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    existing_like = (
        session.query(scheme.ArticleLike)
        .where(
            scheme.ArticleLike.article_id == article_id
            and scheme.ArticleLike.author_username == username
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.ArticleDislike)
        .where(
            scheme.ArticleDislike.article_id == article_id
            and scheme.ArticleDislike.author_username == username
        )
        .scalar()
    )
    if existing_dislike:
        session.delete(existing_dislike)
    else:
        dislike = scheme.ArticleDislike(article_id=article_id, author_username=username)
        session.add(dislike)
    if existing_like:
        session.delete(existing_like)
    session.commit()
    return request_status.Status(request_status.StatusType.OK)
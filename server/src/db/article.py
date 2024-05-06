from . import scheme
from .. import config
from .. import request_status
import time
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import select, update, delete

from sqlalchemy import create_engine


def is_article_not_exist(session: Session, article_id):
    article = session.query(scheme.Article).where(scheme.Article.id == article_id).scalar()
    return article is None


def add_article(session, title, body, author, preview):
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
    session.commit()
    return article.id


def add_tags(session, tags, article_id):
    for tag in tags:
        article_tag = scheme.ArticleTag(tag_name=tag, article_id=article_id)
        session.add(article_tag)
    session.commit()


def is_liked(session: Session, article_id, username):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.OK), False
    return request_status.Status(request_status.StatusType.OK), not session.query(scheme.ArticleLike).where(
        scheme.ArticleLike.article_id == article_id and scheme.ArticleLike.author_username == username).scalar() is None


def is_disliked(session: Session, article_id, username):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.OK), False
    return request_status.Status(request_status.StatusType.OK), not session.query(scheme.ArticleDislike).where(
        scheme.ArticleDislike.article_id == article_id and scheme.ArticleDislike.author_username == username).scalar() is None


def get_likes(session: Session, article_id):
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


def get_dislikes(session: Session, article_id):
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


def get_rating(session: Session, article_id):
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


def get_comments_count(session: Session, article_id):
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


def get_article(session: Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    article = session.query(scheme.Article).where(scheme.Article.id == article_id).scalar()
    return request_status.Status(request_status.StatusType.OK), article


def get_preview(session: Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    preview = session.query(scheme.ArticlePreview.preview_content).where(
        scheme.ArticlePreview.article_id == article_id).scalar()
    return request_status.Status(request_status.StatusType.OK), preview


def get_tags(session: Session, article_id):
    if is_article_not_exist(session, article_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {article_id}'), None
    tags = session.query(scheme.ArticleTag.tag_name).where(scheme.ArticleTag.article_id == article_id).all()
    return request_status.Status(request_status.StatusType.OK), [tag[0] for tag in tags]


def like_article(article_id, username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
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
        session.delete(existing_dislike)
        session.commit()


def dislike_article(article_id, username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
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
        session.delete(existing_like)
        session.commit()


def check_open(article_id, username):
    """Функция проверяет, открывал ли пользователь статью.

    :param article_id: Id статьи
    :param username: Имя пользователя
    """
    engine = create_engine(config.db_url)

    with Session(engine) as session:
        existing_record = session.query(scheme.ArticleOpenCounter).filter_by(article_id=article_id,
                                                                             author_username=username).first()
        if not existing_record:
            new_record = scheme.ArticleOpenCounter(article_id=article_id, author_username=username)
            session.add(new_record)
            session.commit()


def check_views(articles: List[Tuple[int, str]]):
    """Функция проверяет, просматривал ли пользователь статью.

    :param articles: Список статей
    """
    engine = create_engine(config.db_url)

    with Session(engine) as session:
        for article_id, username in articles:
            existing_record = session.query(scheme.ArticleViewCounter).filter_by(article_id=article_id,
                                                                                 author_username=username).first()
            if not existing_record:
                new_record = scheme.ArticleViewCounter(article_id=article_id, author_username=username)
                session.add(new_record)
        session.commit()

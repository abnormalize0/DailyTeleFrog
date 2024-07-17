from . import scheme
#import scheme
import time
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import select, update, delete

from sqlalchemy import create_engine

db = create_engine("sqlite://")
scheme.Base.metadata.create_all(db)
session = Session(db)


def add_comment(article_id, root_id, comment_text, login):
    comment = scheme.Comment(
        article_id=article_id,
        author_username=login,
        text=comment_text,
        root_id=root_id,
        creation_date=round(time.time() * 1000),
    )
    session.add(comment)
    session.commit()

def like_comment(comment_id, username):
    existing_like = (
        session.query(scheme.CommentLike)
        .where(
            scheme.CommentLike.comment_id == comment_id
            and scheme.CommentLike.author_username == username
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.CommentDislike)
        .where(
            scheme.CommentDislike.comment_id == comment_id
            and scheme.CommentDislike.author_username == username
        )
        .scalar()
    )
    if existing_like:
        session.delete(existing_like)
    else:
        like = scheme.CommentLike(comment_id=comment_id, author_username=username)
        session.add(like)
    session.delete(existing_dislike)
    session.commit()

def dislike_comment(comment_id, username):
    existing_like = (
        session.query(scheme.CommentLike)
        .where(
            scheme.CommentLike.comment_id == comment_id
            and scheme.CommentLike.author_username == username
        )
        .scalar()
    )
    existing_dislike = (
        session.query(scheme.CommentDislike)
        .where(
            scheme.CommentDislike.comment_id == comment_id
            and scheme.CommentDislike.author_username == username
        )
        .scalar()
    )
    if existing_dislike:
        session.delete(existing_dislike)
    else:
        dislike = scheme.CommentDislike(comment_id=comment_id, author_username=username)
        session.add(dislike)
    session.delete(existing_like)
    session.commit()

def comment_rating(comment_id):
    likes = session.query(
        scheme.CommentLike
    ).where(
        scheme.CommentLike.comment_id == comment_id
    )
    dislikes = session.query(
        scheme.CommentDislike
    ).where(
        scheme.CommentDislike.comment_id == comment_id
    )
    return likes - dislikes
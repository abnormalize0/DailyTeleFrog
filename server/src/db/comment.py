from . import scheme
import time
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import select, update, delete

from sqlalchemy import create_engine

from .. import request_status

def is_comment_not_exist(session:Session, comment_id):
    comment = session.query(scheme.Comment).where(scheme.Comment.id == comment_id).scalar()
    return comment is None

def add(session:Session, article_id, root_id, comment_text, username):
    comment = scheme.Comment(
        article_id=article_id,
        author_username=username,
        text=comment_text,
        root_id=root_id,
        creation_date=round(time.time() * 1000),
    )
    session.add(comment)
    session.flush()
    return request_status.Status(request_status.StatusType.OK), comment.id

def like(session:Session, comment_id, username):
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
    if existing_dislike:
       session.delete(existing_dislike)
    session.commit()
    return request_status.Status(request_status.StatusType.OK)

def dislike(session:Session, comment_id, username):
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
    if existing_like:
        session.delete(existing_like)
    session.commit()
    return request_status.Status(request_status.StatusType.OK)

def rating(session:Session, comment_id):
    likes = session.query(
        scheme.CommentLike
    ).where(
        scheme.CommentLike.comment_id == comment_id
    ).scalar()
    dislikes = session.query(
        scheme.CommentDislike
    ).where(
        scheme.CommentDislike.comment_id == comment_id
    ).scalar()
    return request_status.Status(request_status.StatusType.OK), likes - dislikes

def answers(id, comments):
    comment_answers = []
    for i, comment in enumerate(comments):
        if comment[2] == id:
            comment_answers.append(
                {
                    "author_username": comment[0],
                    "id": comment[1],
                    "root_id": comment[2],
                    "text": comment[3],
                    "answers": answers(comment[1], comments)
                }
            )
    return request_status.Status(request_status.StatusType.OK), comment_answers

def from_article(session:Session, article_id):
    comments = session.query(
        scheme.Comment.author_username,
        scheme.Comment.id,
        scheme.Comment.root_id,
        scheme.Comment.text
    ).where(
        scheme.Comment.article_id == article_id
    ).all()
    sorted_comments = []
    for comment in comments:
        if comment[2] == -1:
            sorted_comments.append(
                {
                    "author_username": comment[0],
                    "id": comment[1],
                    "root_id": comment[2],
                    "text": comment[3],
                    "answers": answers(comment[1], comments)
                }
            )

    return request_status.Status(request_status.StatusType.OK), sorted_comments

def likes_count(session:Session, comment_id):
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {comment_id}'), None
    likes = (
        session.query(scheme.CommentLike)
        .where(scheme.CommentLike.comment_id == comment_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), likes

def dislikes_count(session:Session, comment_id):
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {comment_id}'), None
    dislikes = (
        session.query(scheme.CommentDislike)
        .where(scheme.CommentDislike.comment_id == comment_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), dislikes

def rating(session:Session, comment_id):
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {comment_id}'), None
    likes = (
        session.query(scheme.CommentLike)
        .where(scheme.CommentLike.comment_id == comment_id)
        .count()
    )
    dislikes = (
        session.query(scheme.CommentDislike)
        .where(scheme.CommentDislike.comment_id == comment_id)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), likes - dislikes

def creation_date(session:Session, comment_id):
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find article with id: {comment_id}'), None
    date = (
        session.query(scheme.Comment.creation_date)
        .where(scheme.Comment.id == comment_id)
        .count()
    ).scalar()

    return request_status.Status(request_status.StatusType.OK), date

def is_liked(session:Session, comment_id, username):
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(request_status.StatusType.OK), False
    return request_status.Status(request_status.StatusType.OK), not session.query(scheme.CommentLike).where(scheme.CommentLike.comment_id == comment_id and scheme.CommentLike.author_username == username).scalar() is None


def is_disliked(session:Session, comment_id, username):
    if is_comment_not_exist(session, comment_id):
        return request_status.Status(request_status.StatusType.OK), False
    return request_status.Status(request_status.StatusType.OK), not session.query(scheme.CommentDislike).where(scheme.CommentDislike.comment_id == comment_id and scheme.CommentDislike.author_username == username).scalar() is None

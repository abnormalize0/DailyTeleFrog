from . import scheme
import time
from sqlalchemy import select, update, delete
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy.orm import Session

from .. import config
from .. import request_status


def is_user_not_exist(session:Session, username, email=None):
    user:scheme.User
    if username:
        user = (
            session.query(scheme.User)
            .where(scheme.User.username == username)
            .scalar()
            )
    if email:
        user = (
            session.query(scheme.User)
            .where(scheme.User.email == email)
            .scalar()
            )
    return user is None

def add_user(session:Session, username, nickname, password, creation_date, email, avatar=None, description=None):
    user = scheme.User(
        username=username,
        nickname=nickname,
        password=password,
        creation_date=creation_date,
        email=email,
        avatar=avatar,
        description=description,
    )
    old_name = scheme.UserNameHistory(
        username=username,
        old_name=nickname,
    )
    session.add_all((user, old_name))
    session.flush()


def check_password(session:Session, password, username=None, email=None):
    if is_user_not_exist(session=session, username=username, email=email):
        return request_status.Status(request_status.StatusType.OK), False
    user_password: str
    if username:
        user_password = (
            session.query(scheme.User.password)
            .where(scheme.User.username == username)
            .scalar()
        )
    if email:
        user_password = (
            session.query(scheme.User.password)
            .where(scheme.User.email == email)
            .scalar()
        )
    return request_status.Status(request_status.StatusType.OK), password == user_password


def change_password(session:Session, password, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}')
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.password = password
    session.commit()
    return request_status.Status(request_status.StatusType.OK)


def update_email(session:Session, username, email):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}')
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.email = email
    session.commit()
    return request_status.Status(request_status.StatusType.OK)


def update_nickname(session:Session, username, nickname):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}')
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.nickname = nickname
    name_history = scheme.UserNameHistory(
        username=username,
        old_name=nickname,
    )
    session.add(name_history)
    session.commit()
    return request_status.Status(request_status.StatusType.OK)


def update_description(session:Session, username, description):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}')
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.description = description
    session.commit()
    return request_status.Status(request_status.StatusType.OK)


def update_avatar(session:Session, username, avatar):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}')
    user: scheme.User = (
        session.query(scheme.User).where(scheme.User.username == username).scalar()
    )
    user.avatar = avatar
    session.commit()
    return request_status.Status(request_status.StatusType.OK)


def sub_user(session:Session, username, sub):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}')
    block_user = session.query(scheme.UserBlacklist).where(
        scheme.UserBlacklist.username == username
        and scheme.UserBlacklist.blocked_user == sub
    ).scalar()
    if block_user:
        session.delete(block_user)
    subscription = scheme.UserSubscription(
        username=username,
        subscribed_user=sub,
    )
    session.add(subscription)
    session.commit()
    return request_status.Status(request_status.StatusType.OK)


def block_user(session:Session, username, blocked_user):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}')
    sub_user = session.query(scheme.UserSubscription).where(
        scheme.UserSubscription.username == username
        and scheme.UserSubscription.subscribed_user == blocked_user
    ).scalar()
    if sub_user:
        session.delete(sub_user)
    blacklist = scheme.UserBlacklist(
        username=username,
        blocked_user=blocked_user,
    )
    session.add(blacklist)
    session.commit()
    return request_status.Status(request_status.StatusType.OK)


def sub_tag(session:Session, username, tag_name):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}')
    block_tag = session.query(scheme.TagBlacklist).where(
        scheme.TagBlacklist.username == username
        and scheme.TagBlacklist.tag_name == tag_name
    ).scalar()
    if block_tag:
        session.delete(block_tag)
    subscription = scheme.TagSubscription(
        username=username,
        tag_name=tag_name,
    )
    session.add(subscription)
    session.commit()
    return request_status.Status(request_status.StatusType.OK)


def block_tag(session:Session, username, tag_name):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}')
    sub_tag = session.query(scheme.TagSubscription).where(
        scheme.TagSubscription.username == username
        and scheme.TagSubscription.tag_name == tag_name
    ).scalar()
    if sub_tag:
        session.delete(sub_tag)
    user_blacklist = scheme.TagBlacklist(
        username=username,
        tag_name=tag_name,
    )
    session.add(user_blacklist)
    session.commit()
    return request_status.Status(request_status.StatusType.OK)


def get_rating(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    user_articles = session.query(scheme.Article.id).where(
        scheme.Article.author_username == username
    )
    article_likes = (
        session.query(scheme.ArticleLike)
        .where(scheme.ArticleLike.article_id in user_articles)
        .count()
    )
    article_dislikes = (
        session.query(scheme.ArticleDislike)
        .where(scheme.ArticleDislike.article_id in user_articles)
        .count()
    )
    user_comments = session.query(scheme.Comment.id).where(
        scheme.Comment.author_username == username
    )
    comment_likes = (
        session.query(scheme.CommentLike)
        .where(scheme.CommentLike.comment_id in user_comments)
        .count()
    )
    comment_dislikes = (
        session.query(scheme.CommentDislike)
        .where(scheme.CommentDislike.comment_id in user_comments)
        .count()
    )
    return request_status.Status(request_status.StatusType.OK), article_likes - article_dislikes + comment_likes + comment_dislikes


def get_email(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    email = (
        session.query(scheme.User.email)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), email


def get_name_history(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    name_history = (
        session.query(scheme.UserNameHistory.old_name)
        .where(scheme.UserNameHistory.username == username)
        .all()
    )
    name_history = [row[0] for row in name_history]
    return request_status.Status(request_status.StatusType.OK), name_history


def get_nickname(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    nickname = (
        session.query(scheme.User.nickname)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), nickname


def get_description(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    description = (
        session.query(scheme.User.description)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), description


def get_avatar(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    avatar = (
        session.query(scheme.User.avatar)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), avatar


def get_sub_user(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    subscriptions = (
        session.query(scheme.UserSubscription.subscribed_user)
        .where(scheme.UserSubscription.username == username)
        .all()
    )
    subscriptions = [row[0] for row in subscriptions]
    return request_status.Status(request_status.StatusType.OK), subscriptions


def get_blacklist_user(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    blacklist = (
        session.query(scheme.UserBlacklist.blocked_user)
        .where(scheme.UserBlacklist.username == username)
        .all()
    )
    blacklist = [row[0] for row in blacklist]
    return request_status.Status(request_status.StatusType.OK), blacklist


def get_sub_tag(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    subscriptions = (
        session.query(scheme.TagSubscription)
        .where(scheme.TagSubscription.username == username)
        .all()
    )
    subscriptions = [row[0] for row in subscriptions]
    return request_status.Status(request_status.StatusType.OK), subscriptions


def get_blacklist_tag(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    blacklist = (
        session.query(scheme.TagBlacklist)
        .where(scheme.TagBlacklist.username == username)
        .all()
    )
    blacklist = [row[0] for row in blacklist]
    return request_status.Status(request_status.StatusType.OK), blacklist


def get_creation_date(session:Session, username):
    if is_user_not_exist(session=session, username=username):
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'Cannot find user with username: {username}'), None
    creation_date = (
        session.query(scheme.User.creation_date)
        .where(scheme.User.username == username)
        .scalar()
    )
    return request_status.Status(request_status.StatusType.OK), creation_date

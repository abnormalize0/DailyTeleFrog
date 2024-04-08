from . import scheme
import time
from sqlalchemy import select, update, delete
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy.orm import Session

from .. import config


def add_user(username, nickname, password, creation_date, email, avatar=None, description=None):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
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
        session.commit()


def check_password(password, username=None, email=None):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
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
        return password == user_password


def change_password(password, username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        user: scheme.User = (
            session.query(scheme.User).where(scheme.User.username == username).scalar()
        )
        user.password = password
        session.commit()


def update_email(username, email):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        user: scheme.User = (
            session.query(scheme.User).where(scheme.User.username == username).scalar()
        )
        user.email = email
        session.commit()


def update_nickname(username, nickname):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
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


def update_description(username, description):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        user: scheme.User = (
            session.query(scheme.User).where(scheme.User.username == username).scalar()
        )
        user.description = description
        session.commit()


def update_avatar(username, avatar):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        user: scheme.User = (
            session.query(scheme.User).where(scheme.User.username == username).scalar()
        )
        user.avatar = avatar
        session.commit()


def sub_user(username, sub):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        request = select(scheme.UserBlacklist).where(
            scheme.UserBlacklist.username == username
            and scheme.UserBlacklist.blocked_user == sub
        )
        session.delete(request)
        subscription = scheme.UserSubscription(
            username=username,
            subscribed_user=sub,
        )
        session.add(subscription)
        session.commit()


def block_user(username, blocked_user):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        request = select(scheme.UserSubscription).where(
            scheme.UserSubscription.username == username
            and scheme.UserSubscription.subscribed_user == blocked_user
        )
        session.delete(request)
        blacklist = scheme.UserBlacklist(
            username=username,
            blocked_user=blocked_user,
        )
        session.add(blacklist)
        session.commit()


def sub_tag(username, tag_name):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        request = select(scheme.TagBlacklist).where(
            scheme.TagBlacklist.username == username
            and scheme.TagBlacklist.tag_name == tag_name
        )
        session.delete(request)
        subscription = scheme.TagSubscription(
            username=username,
            subscribed_user=tag_name,
        )
        session.add(subscription)
        session.commit()


def block_tag(username, tag_name):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        request = select(scheme.TagSubscription).where(
            scheme.TagSubscription.username == username
            and scheme.TagSubscription.tag_name == tag_name
        )
        session.delete(request)
        user_blacklist = scheme.TagBlacklist(
            username=username,
            blocked_user=tag_name,
        )
        session.add(user_blacklist)
        session.commit()


def get_rating(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
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
        return article_likes - article_dislikes + comment_likes + comment_dislikes


def get_email(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        email = (
            session.query(scheme.User.email)
            .where(scheme.User.username == username)
            .scalar()
        )
        return email


def get_name_history(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        name_history = (
            session.query(scheme.UserNameHistory.old_name)
            .where(scheme.UserNameHistory.username == username)
            .all()
        )
        name_history = [row[0] for row in name_history]
        return name_history


def get_nickname(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        nickname = (
            session.query(scheme.User.nickname)
            .where(scheme.User.username == username)
            .scalar()
        )
        return nickname


def get_description(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        description = (
            session.query(scheme.User.description)
            .where(scheme.User.username == username)
            .scalar()
        )
        return description


def get_avatar(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        avatar = (
            session.query(scheme.User.avatar)
            .where(scheme.User.username == username)
            .scalar()
        )
        return avatar


def get_sub_user(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        subscriptions = (
            session.query(scheme.UserSubscription.subscribed_user)
            .where(scheme.UserSubscription.username == username)
            .all()
        )
        subscriptions = [row[0] for row in subscriptions]
        return subscriptions


def get_blacklist_user(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        blacklist = (
            session.query(scheme.UserBlacklist.blocked_user)
            .where(scheme.UserBlacklist.username == username)
            .all()
        )
        blacklist = [row[0] for row in blacklist]
        return blacklist


def get_sub_tag(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        subscriptions = (
            session.query(scheme.TagSubscription)
            .where(scheme.TagSubscription.username == username)
            .all()
        )
        subscriptions = [row[0] for row in subscriptions]
        return subscriptions


def get_blacklist_tag(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        blacklist = (
            session.query(scheme.TagBlacklist)
            .where(scheme.TagBlacklist.username == username)
            .all()
        )
        blacklist = [row[0] for row in blacklist]
        return blacklist


def get_creation_date(username):
    engine = create_engine(config.db_url)
    with Session(engine) as session:
        creation_date = (
            session.query(scheme.User.creation_date)
            .where(scheme.User.username == username)
            .scalar()
        )
        return creation_date

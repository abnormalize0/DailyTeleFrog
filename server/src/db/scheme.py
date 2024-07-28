import datetime
import os

import jwt

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Text, BigInteger, DateTime
from sqlalchemy.sql import func
from typing import Optional


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32))
    email: Mapped[str] = mapped_column(String(32), unique=True)
    nickname: Mapped[str] = mapped_column(String(32))
    password: Mapped[str] = mapped_column(String(60), deferred=True)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    avatar: Mapped[Optional[str]] = mapped_column(String(32))
    description: Mapped[Optional[str]] = mapped_column(Text)

    def __init__(self, username, email, nickname, password, avatar, description, **kw):
        super().__init__(**kw)
        self.username = username
        self.email = email
        self.nickname = nickname
        self.password = password

        self.creation_date = func.now()
        self.avatar = avatar
        self.description = description

    def encode_auth_token(self):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
                'iat': datetime.datetime.utcnow(),
                'sub': self.id
            }
            return jwt.encode(
                payload,
                os.getenv('SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Decodes the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_token, os.getenv('SECRET_KEY'), algorithms='HS256')
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'password': self.password,
            'creation_date': str(self.creation_date),
            'avatar': self.avatar,
            'description': self.description
        }


class UserNameHistory(Base):
    __tablename__ = "user_name_history"
    username: Mapped[str] = mapped_column(ForeignKey("users.username"), primary_key=True)
    old_name: Mapped[str] = mapped_column(String(512), primary_key=True)


class TagSubscription(Base):
    __tablename__ = "tag_subscriptions"
    tag_name: Mapped[str] = mapped_column(String(512), primary_key=True)
    username: Mapped[str] = mapped_column(ForeignKey("users.username"), primary_key=True)

class TagBlacklist(Base):
    __tablename__ = "tag_blacklist"
    tag_name: Mapped[str] = mapped_column(String(512), primary_key=True)
    username: Mapped[str] = mapped_column(ForeignKey("users.username"), primary_key=True)

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    username: Mapped[str] = mapped_column(ForeignKey("users.username"), primary_key=True)
    subscribed_user: Mapped[str] = mapped_column(ForeignKey("users.username"), primary_key=True)

class UserBlacklist(Base):
    __tablename__ = "user_blacklist"
    username: Mapped[str] = mapped_column(ForeignKey("users.username"), primary_key=True)
    blocked_user: Mapped[str] = mapped_column(ForeignKey("users.username"), primary_key=True)

class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    creation_date: Mapped[int] = mapped_column(BigInteger)
    body: Mapped[str] = mapped_column(String(512))
    author_username: Mapped[int] = mapped_column(ForeignKey("users.username"))

class ArticleTag(Base):
    __tablename__ = "article_tags"
    tag_name: Mapped[str] = mapped_column(String(512), primary_key=True)
    article_id = mapped_column(ForeignKey("articles.id"), primary_key=True)

class ArticlePreview(Base):
    __tablename__ = "article_preview"
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), primary_key=True)
    preview_content: Mapped[str] = mapped_column(String(512))

class ArticleLike(Base):
    __tablename__ = "article_likes"
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), primary_key=True)
    author_username: Mapped[int] = mapped_column(ForeignKey("users.username"), primary_key=True)

class ArticleDislike(Base):
    __tablename__ = "article_dislikes"
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), primary_key=True)
    author_username: Mapped[int] = mapped_column(ForeignKey("users.username"), primary_key=True)

class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), )
    author_username: Mapped[int] = mapped_column(ForeignKey("users.username"), )
    text: Mapped[str] = mapped_column(String(512))
    creation_date: Mapped[int]
    root_id: Mapped[int]

class CommentLike(Base):
    __tablename__ = "comment_likes"
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), primary_key=True)
    author_username: Mapped[int] = mapped_column(ForeignKey("users.username"), primary_key=True)

class CommentDislike(Base):
    __tablename__ = "comment_dislikes"
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), primary_key=True)
    author_username: Mapped[int] = mapped_column(ForeignKey("users.username"), primary_key=True)

#class Community(Base):
#    __tablename__ = "communities"
#    name: Mapped[str] = mapped_column(primary_key=True)
#    avatar: Mapped[str]
#    description: Mapped[str]
#    creation_date: Mapped[int]
#    creator: Mapped[int] = mapped_column(ForeignKey("users.username"))
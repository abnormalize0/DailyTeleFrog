import datetime
import os

import jwt

from sqlalchemy import Text, DateTime
from src.db import *
from src.request_status import Status, StatusType
from sqlalchemy.sql import func
from typing import Optional


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
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, minutes=90),
                'iat': datetime.datetime.utcnow(),
                'user_id': self.id
            }
            return jwt.encode(
                payload,
                os.getenv('SECRET_KEY'),
                algorithm='HS256'
            ), Status(StatusType.OK)
        except jwt.exceptions.InvalidTokenError:
            return None, Status(StatusType.ERROR, msg='Error occurred, try later')

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

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.db.scheme import User
from src.request_status import Status, StatusType
import bcrypt
import os

db_url = os.getenv('MVP_DB_URL')


class UserRepository:

    @staticmethod
    def get_user(username, password):
        engine = create_engine(db_url)
        with Session(engine) as session:
            user = session.query(User).where(User.username == username).first()
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')) and isinstance(user,
                                                                                                               User):
                auth_token = user.encode_auth_token()
                if auth_token:
                    return json.dumps({
                        "user": user.to_json(),
                        "auth_token": auth_token
                    }), Status(StatusType.OK)
                return {"user": None, "auth_token": None}, Status(StatusType.ERROR)
            return None, Status(StatusType.ERROR)

    @staticmethod
    def save_user(username, password, email):
        engine = create_engine(db_url)
        with Session(engine) as session:
            u = session.query(User).where(User.email == email).first()
            if u:
                return "User already exists", Status(StatusType.ERROR)

            user = User(
                username=username,
                nickname=username,
                password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(int(os.getenv('BCRYPT_LOG_ROUNDS'))))
                .decode('utf-8'),
                email=email,
                avatar=None,
                description=None
            )
            session.add(user)
            session.commit()
            session.flush()
            auth_token = user.encode_auth_token()

            return json.dumps({'user': user.to_json(), 'auth_token': auth_token}), Status(StatusType.OK)

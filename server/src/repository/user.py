from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.config import db_url
from src.db.scheme import User
from src.request_status import Status, StatusType
from src.api.api import bcrypt


def get_user(email, password):
    engine = create_engine(db_url)
    with Session(engine) as session:
        user = session.query(User).where(User.email == email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            auth_token = user.encode_auth_token(user.id)
            if auth_token:
                return {
                    "user": user,
                    "auth_token": auth_token.decode()
                }, Status(StatusType.OK)
            return {"user": None, "auth_token": None}, Status(StatusType.ERROR)
        return None, Status(StatusType.ERROR)


def save_user(username, password, email):
    engine = create_engine(db_url)
    with Session(engine) as session:
        u = session.query(User).where(User.email == email).first()
        if u:
            return "User already exists", Status(StatusType.ERROR)

        user = User(
            username=username,
            nickname=username,
            password=password,
            email=email,
            avatar=None,
            description=None
        )
        session.add(user)
        session.flush()
        auth_token = user.encode_auth_token()

        return {"user": user, "auth_token": auth_token}, Status(StatusType.OK)

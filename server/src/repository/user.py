from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.config import db_url
from src.db.scheme import User
from src.request_status import Status, StatusType


def get_user(username, password):
    engine = create_engine(db_url)
    with Session(engine) as session:
        user = session.query(User).where(User.username == username and User.password == password)
        return user, Status(StatusType.OK)


def save_user(username, password, email, creation_time):
    engine = create_engine(db_url)
    with Session(engine) as session:
        user = User(
            username=username,
            nickname=username,
            password=password,
            email=email,
            creation_date=creation_time
        )
        session.add(user)
        session.flush()


"""
Этот файл служит для хранения общего declarative base, от которого наследуются
все модели схемы БД — без него SQLAlchemy не сможет собрать их в одну общую
Base.metadata (используется в тестах для create_all/drop_all).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

from sqlalchemy.orm import Session
from src.db.scheme import Article


def is_article_not_exist(session: Session, article_id):
    article = session.query(Article).where(Article.id == article_id).scalar()
    return article is None

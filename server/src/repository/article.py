from sqlalchemy.orm import Session
from src.db.scheme import Article


def article_exists(session: Session, article_id):
    article = session.query(Article).where(Article.id == article_id).scalar()
    return article is None

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.config import db_url
from src.db.scheme import ArticlePreview, Article
from src.request_status import Status, StatusType, ErrorType
from src.services.utils.article import is_article_not_exist


def get_preview(session: Session, article_id):
    if is_article_not_exist(session, article_id):
        return (None, Status(StatusType.ERROR, error_type=ErrorType.ValueError,
                             msg=f'Cannot find article with id: {article_id}'))
    preview = session.query(ArticlePreview.preview_content).where(ArticlePreview.article_id == article_id).scalar()
    return preview, Status(StatusType.OK)


def get_previews(start_ts, end_ts):
    engine = create_engine(db_url)
    with Session(engine) as session:
        article_limit = 30
        article_ids = (session.query(Article.id).where(start_ts <= Article.creation_date <= end_ts).limit(article_limit)
                       .all())
        previews = session.query(ArticlePreview).where(ArticlePreview.article_id.in_(article_ids)).all()
        return previews, Status(StatusType.OK)

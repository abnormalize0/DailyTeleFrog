from flask import Blueprint, request
from src.request_status import Status, StatusType, ErrorType
from src.services.preview_article import get_previews

preview_article = Blueprint('preview_article', __name__)


@preview_article.route('/preview_articles', methods=['GET'])
def preview_articles():
    start_ts = request.args.get('start_ts')
    end_ts = request.args.get('end_ts')

    if start_ts is None or end_ts is None:
        return None, Status(StatusType.ERROR, error_type=ErrorType.ValueError)

    return get_previews(start_ts, end_ts)

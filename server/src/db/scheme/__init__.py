"""
Этот файл служит для хранения схемы БД: раньше все модели лежали в одном
scheme.py, теперь каждая таблица — в своём файле (см. decisions/0001, план по
структуре кода). Здесь модели собираются заново под одним именем `scheme`, как
раньше, чтобы во всех местах, где уже написано `from . import scheme` и
`scheme.User`/`scheme.Article`/…, ничего менять не пришлось. Импорт каждой
модели обязателен и здесь, а не только в её собственном файле — иначе класс не
попадёт в Base.metadata и create_all/drop_all (см. tests/conftest.py) его не
увидят.
"""

from .base import Base
from .user import User
from .user_name_history import UserNameHistory
from .tag_subscription import TagSubscription
from .tag_blacklist import TagBlacklist
from .user_subscription import UserSubscription
from .user_blacklist import UserBlacklist
from .article import Article
from .article_tag import ArticleTag
from .article_preview import ArticlePreview
from .article_like import ArticleLike
from .article_dislike import ArticleDislike
from .comment import Comment
from .comment_like import CommentLike
from .comment_dislike import CommentDislike
from .access_token import AccessToken
from .refresh_token import RefreshToken

# Задел на будущее, ещё не решено — сообщества/каналы авторов. Ничего не
# реализует, оставлено как памятка, перенесено сюда при разбиении scheme.py на
# файлы без изменений.
# class Community(Base):
#    __tablename__ = "communities"
#    name: Mapped[str] = mapped_column(primary_key=True)
#    avatar: Mapped[str]
#    description: Mapped[str]
#    creation_date: Mapped[int]
#    creator: Mapped[int] = mapped_column(ForeignKey("users.username"))

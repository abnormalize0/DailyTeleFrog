"""
Этот файл служит для регистрации всех API-методов на общем `shared.app`.
Импорт каждого подмодуля — единственный способ выполнить его `@app.route(...)`
(побочный эффект импорта), сами имена дальше не используются.
"""

from . import articles
from . import articles_item
from . import articles_data
from . import articles_like
from . import articles_dislike
from . import articles_comments
from . import comments_item
from . import comments_like
from . import comments_dislike
from . import users
from . import users_me
from . import users_me_password
from . import auth_login
from . import auth_refresh
from . import auth_logout
from . import auth_logout_all

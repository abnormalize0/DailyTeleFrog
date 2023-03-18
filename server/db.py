import sqlite3
import json

DELIMITER = '~'
ARTICLESDB = "articles/articles.db"
USERSDB = "users/users.db"

def unblocked_article_request(blocked_tags=None):
    request = "SELECT article_id FROM articles"
    if not blocked_tags:
        return request
    request += " WHERE tags NOT LIKE '%{0}{1}{0}%'".format(DELIMITER, blocked_tags[0]) 
    for tag in blocked_tags[1:]:
        request += " AND tags NOT LIKE '%{0}{1}{0}%'".format(DELIMITER, tag)
    return request

def get_unblocked_artiles(blocked_tags=None):
    unblocked_artiles = []
    connection = sqlite3.connect(ARTICLESDB)
    cursor = connection.cursor()
    request = unblocked_article_request(blocked_tags)
    select = cursor.execute(request)
    unblocked_artiles = select.fetchall()
    connection.close()
    return [_[0] for _ in unblocked_artiles]

def get_user_blocked_tags(user_id):
    connection = sqlite3.connect(USERSDB)
    cursor = connection.cursor()
    select = cursor.execute("SELECT blocked_tags FROM users WHERE user_id = ?", [user_id])
    bloked_tags = select.fetchall()
    connection.close()
    bloked_tags = bloked_tags[0][0].split(DELIMITER)[1:-1]
    return bloked_tags

def tags_to_str(tags):
    tags_str = DELIMITER
    for tag in tags:
        tags_str += str(tag) + DELIMITER
    return tags_str

def create_db_entry(preview):
    tags = preview.pop('tags')
    tags = tags_to_str(tags)
    connection = sqlite3.connect(ARTICLESDB)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO articles (preview, tags) VALUES (?, ?)", [json.dumps(preview), tags])
    connection.commit()
    article_id = cursor.lastrowid
    connection.close()
    return article_id

def get_author_preview(user_id):
    connection = sqlite3.connect(USERSDB)
    cursor = connection.cursor()
    select = cursor.execute("SELECT name, page, avatar FROM users WHERE user_id = ?", [user_id])
    db_info = select.fetchall()
    connection.close()
    author_preview = {}
    author_preview["user_id"] = user_id
    author_preview["name"] = db_info[0][0]
    author_preview["page"] = db_info[0][1]
    author_preview["avatar"] = db_info[0][2]
    return author_preview

def get_likes_comments_count(article_id):
    connection = sqlite3.connect(ARTICLESDB)
    cursor = connection.cursor()
    select = cursor.execute("SELECT likes_count, comments_count FROM articles WHERE article_id = ?", [article_id])
    return select[0][0], select[1][0]

def add_user(user_info):
    connection = sqlite3.connect(USERSDB)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO users (name, password, page, avatar, blocked_tags) VALUES (?, ?, ?, ?, ?)", [
        user_info["name"],
        user_info["password"],
        user_info["page"],
        user_info["avatar"],
        user_info["blocked_tags"],
    ])
    connection.commit()
    user_id = cursor.lastrowid
    connection.close()
    return user_id
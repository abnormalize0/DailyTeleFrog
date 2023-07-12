from flask import Flask, request, jsonify
from flask_cors import CORS
import json

from . import backend

app = Flask(__name__)
cors = CORS(app)


@app.route('/article', methods=['GET'])
def api_get_article():
    article_id = request.headers.get('article-id')
    article = backend.get_article(article_id)
    return json.dumps(article)

@app.route('/article/likes_comments', methods=['GET'])
def api_get_article_likes_comments():
    article_id = request.headers.get('article-id')
    likes_comments = backend.get_article_likes_comments(article_id)
    return json.dumps(likes_comments)

@app.route('/article', methods=['POST'])
def api_post_article():
    article = json.loads(request.headers.get('article'))
    login = request.headers.get('login')
    article_id = backend.post_article(article, login)
    return json.dumps({'article-id': article_id})

@app.route('/article/like', methods=['POST'])
def api_like_article():
    login = request.headers.get('login')
    article_id = request.headers.get('article-id')
    backend.like_article(article_id, login)
    return json.dumps({})

@app.route('/article/comments/add', methods=['POST'])
def api_add_comment():
    login = request.headers.get('login')
    article_id = request.headers.get('article-id')
    root = request.headers.get('root')
    cooment_text = request.headers.get('text')
    id = backend.article_add_comment(article_id, root, cooment_text, login)
    return json.dumps({'comment-id': id})

@app.route('/article/comments/like', methods=['POST'])
def api_like_comment():
    login = request.headers.get('login')
    comment_id = request.headers.get('comment-id')
    backend.like_comment(comment_id, login)
    return json.dumps({})

@app.route('/article/comments/like', methods=['GET'])
def api_get_comments_likes():
    comment_id = request.headers.get('comment-id')
    likes_count = backend.get_comment_likes(comment_id)
    return json.dumps({'likes-count': likes_count})

@app.route('/pages', methods=['GET'])
def api_get_pages():
    login = request.headers.get('login')
    indexes = request.headers.get('indexes')
    indexes = indexes.split(',')
    indexes = [int(index) for index in indexes]
    pages = backend.get_pages(indexes, login)
    return json.dumps(pages)

@app.route('/users/new', methods=['POST'])
def api_add_user():
    user_info = json.loads(request.headers.get('user-info'))
    login = backend.add_user(user_info)
    return json.dumps({'login': login})

@app.route('/users/update', methods=['POST'])
def api_update_user_info():
    login = int(request.headers.get('login'))
    user_info = json.loads(request.headers.get('user-info'))
    backend.update_user_info(user_info, login)
    return json.dumps({})

@app.route('/users/change_password', methods=['POST'])
def api_change_user_password():
    login = request.headers.get('login')
    previous_password = request.headers.get('previous-password')
    new_password = request.headers.get('new-password')
    backend.change_password(previous_password, new_password, login)
    return json.dumps({})

@app.route('/users/check_password', methods=['GET'])
def api_check_user_password():
    login = request.headers.get('login')
    password = request.headers.get('password')
    is_password_correct = backend.check_password(password, login)
    return json.dumps({'status': is_password_correct})

def run_server():
    print('Running...')
    app.run(host='0.0.0.0', port=5000)
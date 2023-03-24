from flask import Flask, request, jsonify
from flask_cors import CORS
import json

import backend

app = Flask(__name__)
cors = CORS(app)


@app.route("/article", methods=["GET"])
def get_article():
    article_id = request.headers.get('article_id')
    article = backend.get_article(article_id)
    return json.dumps(article)

@app.route("/article/likes_comments", methods=["GET"])
def get_likes_comments_count():
    article_id = request.headers.get('article_id')
    likes_comments = backend.get_likes_comments_count(article_id)
    return json.dumps(likes_comments)

@app.route("/article", methods=["POST"])
def post_article():
    article = request.get_json()
    user_id = request.headers.get('user_id')
    backend.post_article(article, user_id)

@app.route("/pages", methods=["GET"])
def get_pages():
    user_id = request.headers.get('user_id')
    indexes = request.headers.get('indexes')
    pages = backend.get_pages(indexes, user_id)
    return json.dumps(pages)

@app.route("/users/new", methods=["POST"])
def add_user():
    user_info = request.headers.get('user_info')
    user_id = backend.add_user(user_info)
    return json.dumps(user_id)

@app.route("/users/update", methods=["POST"])
def update_user_info():
    user_info = request.headers.get('user_info')
    backend.update_user_inf(user_info)

@app.route("/users/change_password", methods=["POST"])
def change_user_password():
    user_id = request.headers.get("user_id")
    previous_password = request.headers.get("previous_password")
    new_password = request.headers.get("new_password")
    backend.change_password(previous_password, new_password, user_id)

@app.route("/users/check_password", methods=["GET"])
def check_user_password():
    user_id = request.headers.get("user_id")
    password = request.headers.get("password")
    return json.dumps(backend.check_password(password, user_id))

def run_server():
    app.run(host='0.0.0.0', port=5000)
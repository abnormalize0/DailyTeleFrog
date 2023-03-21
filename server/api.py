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

@app.route("/users", methods=["POST"])
def add_user():
    user_info = request.headers.get('user_info')
    user_id = backend.add_user(user_info)
    return json.dumps(user_id)

if __name__ == "__main__": 
    app.run(host='0.0.0.0', port=5000)
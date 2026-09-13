"""
Этот файл служит для хранения данных и методов, которые могут использованы во многих тестах.
"""

import unittest
import requests
import os


class BaseTest(unittest.TestCase):
    workdir = os.getenv("MVP_PATH") + "/test_tmp"
    localhost = "http://127.0.0.1:5000"
    user_count = 0

    default_values = {
        "int": 1,
        "str": "qwerty",
        "dict": {"key": "value"},
        "list": ["tag1", "tag2"],
        "bool": True,
        "date": "1-1-2024",
    }

    wrong_values = {
        "int": "f",
        "str": 1,
        "dict": [],
        "list": {},
        "bool": "hehe",
        "date": {},
    }

    def setUp(self):
        """Хук unittest, вызываемый перед каждым тестом; переопределен в наследниках.

        Args:
            None

        Returns:
            None
        """
        return

    def tearDown(self):
        """Хук unittest, вызываемый после каждого теста; переопределен в наследниках.

        Args:
            None

        Returns:
            None
        """
        return

    def add_user(self, **kwargs):
        """Регистрирует нового тестового пользователя через POST /users.

        Args:
            **kwargs: не используется.

        Returns:
            Кортеж (username, password, nickname, email).
        """
        username = f"tester_username_{self.user_count}"
        nickname = f"tester_nickname_{self.user_count}"
        password = "qwerty"
        email = f"test_{self.user_count}@test.test"
        answer = requests.post(
            self.localhost + "/users",
            json={
                "username": username,
                "nickname": nickname,
                "password": password,
                "email": email,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.user_count += 1
        return (username, password, nickname, email)

    def add_article(self, username, tags=None, preview=None):
        """Публикует тестовую статью через POST /article.

        Args:
            username: автор статьи.
            tags: список тегов, по умолчанию ["tag1", "tag2"].
            preview: контент предпоказа, по умолчанию {"type": "image", "data": "ref"}.

        Returns:
            article_id созданной статьи.
        """
        if not preview:
            preview = {"type": "image", "data": "ref"}
        if not tags:
            tags = ["tag1", "tag2"]
        response = requests.post(
            self.localhost + "/article",
            json={
                "username": username,
                "title": "test_name",
                "preview": preview,
                "tags": tags,
                "body": {"block1": "text"},
            },
        )
        self.assertEqual(
            response.json()["status"]["type"], "OK", msg=response.json()["status"]
        )
        return response.json()["article_id"]

    def add_comment(self, username, article_id):
        """Добавляет тестовый комментарий верхнего уровня через POST /article/comment.

        Args:
            username: автор комментария.
            article_id: id статьи.

        Returns:
            id созданного комментария.
        """
        response = requests.post(
            self.localhost + "/article/comment",
            json={
                "username": username,
                "article_id": article_id,
                "text": "text",
                "root": -1,
            },
        )
        self.assertEqual(
            response.json()["status"]["type"], "OK", msg=response.json()["status"]
        )
        return response.json()["id"]

    def like_article(self, article_id, username):
        """Ставит лайк статье через POST /article/like.

        Args:
            article_id: id статьи.
            username: кто ставит лайк.

        Returns:
            None
        """
        response = requests.post(
            self.localhost + "/article/like",
            json={
                "username": username,
                "article_id": article_id,
            },
        )
        self.assertEqual(
            response.json()["status"]["type"], "OK", msg=response.json()["status"]
        )

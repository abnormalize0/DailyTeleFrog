"""
Этот файл служит для хранения тестов на публичные API методы сервера.
Названия для тестов  формируются следующим образом: test_%METHOD_NAME%_%REQUEST_TYPE%.
Префикс test_ обязателен, так как его наличие используется для подсчета тестов.
%METHOD_NAME% и %REQUEST_TYPE% такие же как и в /server/src/api.py
"""

import os
import requests
import subprocess
import signal
import json
import re
import time
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import create_engine

from tests import base_test
from src import config
from src.db import scheme


class TestAPI(base_test.BaseTest):

    server = None

    def setUp(self):
        # if server didnt close correctly in previuos attempt then kill it
        if os.path.exists(self.workdir):
            pid_file = open(os.path.join(self.workdir, "lastpid.txt"), "r")
            pid = pid_file.readline()
            try:
                os.kill(int(pid), signal.SIGKILL)
            except Exception:
                pass
            # shutil.rmtree(self.workdir, ignore_errors=True)

        load_dotenv(dotenv_path="../.env")
        self.db = create_engine(os.getenv("MVP_DB_URL_TEST"))

        scheme.Base.metadata.drop_all(self.db)
        scheme.Base.metadata.create_all(self.db)

        self.server = subprocess.Popen(
            ["python3", "/app/start.py", "-t", "--working-directory", self.workdir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # wait until server startup
        while True:
            nextline = self.server.stdout.readline()
            time.sleep(1)
            if nextline:
                break

        pid_file = open(os.path.join(self.workdir, "lastpid.txt"), "w+")
        pid_file.write(str(self.server.pid))

    def tearDown(self):
        self.server.terminate()
        # print all server output
        for line in self.server.stderr:
            print(line.decode("utf8"))
        # shutil.rmtree(self.workdir, ignore_errors=True)

    def set_values(self, structure: list):
        headers = {}
        for parameter in structure:
            if parameter["type"] == "json" and parameter["structure"]:
                headers[parameter["name"]] = self.set_values(parameter["structure"])
            else:
                headers[parameter["name"]] = self.default_values[parameter["type"]]
        return headers

    def check_excepted_error(
        self, endpoint, method, headers: dict, body: dict, checked_key, excepted_error
    ):
        request_headers = {}
        for k, v in headers.items():
            # dont dumps str because json.loads(json.dumps({[}])) dont raise value error
            if type(v) is not str:
                request_headers[k] = json.dumps(v)
            else:
                request_headers[k] = v

        if method == "post":
            answer = requests.post(
                self.localhost + endpoint, headers=request_headers, json=body
            )
        else:
            answer = requests.get(
                self.localhost + endpoint, headers=request_headers, json=body
            )

        status_type = answer.json()["status"]["type"]
        error_type = answer.json()["status"]["error_type"]
        message = answer.json()["status"]["message"]
        self.assertEqual(
            status_type, "ERROR", msg=f"Error not raised for {checked_key} key"
        )
        self.assertEqual(
            error_type,
            excepted_error,
            msg=f"Error type: {error_type}\nMessage: {message}",
        )

    def insert_nested_values(self, structure: dict, position: list, values):
        if not position:
            structure.update(values)
        else:
            next_step = position.pop(0)
            structure[next_step] = self.insert_nested_values(
                structure[next_step], position, values
            )
        return structure

    def delete_nested_values(self, structure: dict, position: list):
        if len(position) == 1:
            structure.pop(position[0])
        else:
            next_step = position.pop(0)
            structure[next_step] = self.delete_nested_values(
                structure[next_step], position
            )
        return structure

    def update_structure(self, body, headers, position, values, container):
        if container == "body":
            body = self.insert_nested_values(body, position, values)
        elif container == "header":
            headers = self.insert_nested_values(headers, position, values)
        return body, headers

    def restore_structure(self, body, headers, position, container):
        if container == "body":
            body = self.delete_nested_values(body, position)
        elif container == "header":
            headers = self.delete_nested_values(headers, position)
        return body, headers

    def check_structure(
        self,
        endpoint: str,
        method: str,
        structure: list,
    ):
        info_body = []
        bodies = {}
        info_headers = []
        headers = {}
        for object in structure:
            match object["container"]:
                case "body":
                    info_body.append(object)
                case "header":
                    info_headers.append(object)

        if info_body:
            bodies = self.set_values(info_body)
        if info_headers:
            headers = self.set_values(info_headers)

        for i, _ in enumerate(info_body):
            body = info_body.pop(i)
            body_value = bodies.pop(body["name"])
            self.structure_check_step(
                endpoint, method, body, bodies, headers, [], container="body"
            )
            info_body.insert(i, body)
            bodies[body["name"]] = body_value

        for i, _ in enumerate(info_headers):
            header = info_headers.pop(i)
            header_value = headers.pop(header["name"])
            self.structure_check_step(
                endpoint, method, header, bodies, headers, [], container="header"
            )
            info_headers.insert(i, header)
            headers[header["name"]] = header_value

    def structure_check_step(
        self, endpoint, method, structure: list, body, headers, position, container
    ):
        # set wrong value to header
        values = {structure["name"]: self.wrong_values[structure["type"]]}
        body, headers = self.update_structure(
            body, headers, position[:], values, container
        )

        self.check_excepted_error(
            endpoint=endpoint,
            method=method,
            headers=headers,
            body=body,
            checked_key=structure["name"],
            excepted_error="ValueError",
        )

        # restore correct headers
        position.append(structure["name"])
        body, headers = self.restore_structure(body, headers, position[:], container)
        position.pop(-1)

        # missed required header
        if structure["is_required"]:
            self.check_excepted_error(
                endpoint=endpoint,
                method=method,
                headers=headers,
                body=body,
                checked_key=structure["name"],
                excepted_error="OptionError",
            )

        # check nested structure
        if structure["type"] == "json" and structure["structure"]:
            for i, _ in enumerate(structure["structure"]):
                nested_structure = structure["structure"].pop(i)
                values = {structure["name"]: self.set_values(structure["structure"])}
                body, headers = self.update_structure(
                    body, headers, position[:], values, container
                )

                position.append(structure["name"])
                self.structure_check_step(
                    endpoint=endpoint,
                    method=method,
                    structure=nested_structure,
                    body=body,
                    headers=headers,
                    position=position,
                    container=container,
                )

                body, headers = self.restore_structure(
                    body, headers, position[:], container
                )
                structure["structure"].insert(i, nested_structure)
                position.pop(-1)

    def test_article_post(self):
        endpoint = "/article"
        method = "post"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        usename = user_info[0]
        article = {
            "title": "test_name",
            "preview-content": {"type": "image", "data": "ref"},
            "tags": ["tag1", "tag2", "tag3"],
            "body": {"block1": "text"},
        }

        # happy path
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": usename,
                "title": "test_name",
                "preview": {"type": "image", "data": "ref"},
                "tags": ["tag1", "tag2", "tag3"],
                "body": {"block1": "text"},
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        # test unlogged users
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": "unlogged_user",
                "title": "test_name",
                "preview": {"type": "image", "data": "ref"},
                "tags": ["tag1", "tag2", "tag3"],
                "body": {"block1": "text"},
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

    def test_article_get(self):
        endpoint = "/article"
        method = "get"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        author_info = self.add_user()
        author = author_info[0]
        article_id = self.add_article(username=author)

        # happy path
        answer = requests.get(
            self.localhost + endpoint,
            json={"article_id": article_id, "username": username},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertIn("body", answer.json()["article"].keys())
        self.assertIn("preview", answer.json()["article"].keys())
        self.assertIn("author_preview", answer.json()["article"].keys())
        self.assertEqual(answer.json()["article"]["author_preview"]["username"], author)
        # self.assertIn('answers', answer.json()['article'].keys())
        self.assertIn("likes", answer.json()["article"].keys())
        self.assertIn("dislikes", answer.json()["article"].keys())
        self.assertIn("is_liked", answer.json()["article"].keys())
        self.assertIn("is_disliked", answer.json()["article"].keys())
        self.assertIn("comments_count", answer.json()["article"].keys())
        self.assertIn("tags", answer.json()["article"].keys())
        self.assertIn("creation_date", answer.json()["article"].keys())

        # trying to read a non-existent article
        answer = requests.get(
            self.localhost + endpoint,
            json={"article_id": article_id + 1, "username": username},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

    def test_article_like_post(self):
        endpoint = "/article/like"
        method = "post"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        user_info = self.add_user()
        username_2 = user_info[0]
        article_id = self.add_article(username=username)

        # Проверка, что нельзя лайкнуть свою статью.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username, "article_id": article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

        # Проверка, что лайк применился к статье.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "article_id": article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["likes"]
        answer = requests.get(
            self.localhost + "/article/data",
            json={
                "username": username_2,
                "article_id": article_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["likes"], 1)

        # Проверка, что лайк изменяет рейтинг пользователя.
        request_data = ["rating"]
        answer = requests.get(
            self.localhost + "/users/data",
            json={"username": username, "requested_data": request_data},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["rating"], 1)

        # Проверка, что лайк отменяется, если уже был поставлен.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "article_id": article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["likes"]
        answer = requests.get(
            self.localhost + "/article/data",
            json={
                "username": username_2,
                "article_id": article_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["likes"], 0)

        # Проверка, что убирание лайка изменяет рейтинг.
        request_data = ["rating"]
        answer = requests.get(
            self.localhost + "/users/data",
            json={"username": username, "requested_data": request_data},
        )
        self.assertEqual(answer.json()["rating"], 0)

        # Проверка, что лайк перезаписывает дизлайк.
        answer = requests.post(
            self.localhost + "/article/dislike",
            json={"username": username_2, "article_id": article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "article_id": article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["likes", "dislikes"]
        answer = requests.get(
            self.localhost + "/article/data",
            json={
                "username": username_2,
                "article_id": article_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["likes"], 1)
        self.assertEqual(answer.json()["dislikes"], 0)

        # Проверка, что лайк на одной статье не задевает лайк на другой статье того же пользователя.
        other_article_id = self.add_article(username=username)
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "article_id": other_article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        answer = requests.get(
            self.localhost + "/article/data",
            json={
                "username": username_2,
                "article_id": article_id,
                "requested_data": ["likes"],
            },
        )
        self.assertEqual(answer.json()["likes"], 1)
        answer = requests.get(
            self.localhost + "/article/data",
            json={
                "username": username_2,
                "article_id": other_article_id,
                "requested_data": ["likes"],
            },
        )
        self.assertEqual(answer.json()["likes"], 1)

    def test_article_dislike_post(self):
        endpoint = "/article/dislike"
        method = "post"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        user_info = self.add_user()
        username_2 = user_info[0]
        article_id = self.add_article(username=username)

        # Проверка, что дизлайк применился к статье.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "article_id": article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["dislikes"]
        answer = requests.get(
            self.localhost + "/article/data",
            json={
                "username": username_2,
                "article_id": article_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["dislikes"], 1)

        # Проверка, что дизлайк изменяет рейтинг пользователя.
        request_data = ["rating"]
        answer = requests.get(
            self.localhost + "/users/data",
            json={"username": username, "requested_data": request_data},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["rating"], -1)

        # Проверка, что дизлайк отменяется, если уже был поставлен.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "article_id": article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["dislikes"]
        answer = requests.get(
            self.localhost + "/article/data",
            json={
                "username": username_2,
                "article_id": article_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["dislikes"], 0)

        # Проверка, что убирание дизлайк изменяет рейтинг.
        request_data = ["rating"]
        answer = requests.get(
            self.localhost + "/users/data",
            json={"username": username, "requested_data": request_data},
        )
        self.assertEqual(answer.json()["rating"], 0)

        # Проверка, что дизлайк перезаписывает лайк.
        answer = requests.post(
            self.localhost + "/article/like",
            json={"username": username_2, "article_id": article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "article_id": article_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["likes", "dislikes"]
        answer = requests.get(
            self.localhost + "/article/data",
            json={
                "username": username_2,
                "article_id": article_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["dislikes"], 1)
        self.assertEqual(answer.json()["likes"], 0)

    def test_article_comment_post(self):
        endpoint = "/article/comment"
        method = "post"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        article_id = self.add_article(username=username)
        # Публикуем комментарий к статье.
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": username,
                "article_id": article_id,
                "text": "text",
                "root": -1,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertIn("id", answer.json(), msg=answer.json())

        # Публикуем ответ на комментарий.
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": username,
                "article_id": article_id,
                "text": "text",
                "root": answer.json()["id"],
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertIn("id", answer.json(), msg=answer.json())

        # Попытка ответить на несуществующий комментарий.
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": username,
                "article_id": article_id,
                "text": "text",
                "root": answer.json()["id"] + 1000,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

    def test_article_comment_like_post(self):
        endpoint = "/article/comment/like"
        method = "post"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        user_info = self.add_user()
        username_2 = user_info[0]
        article_id = self.add_article(username=username)

        comment_id = self.add_comment(username, article_id)

        # Проверка, что нельзя лайкнуть свой комментарий.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username, "comment_id": comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

        # Проверка, что лайк применился к комментарию.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "comment_id": comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["likes"]
        answer = requests.get(
            self.localhost + "/article/comment/data",
            json={
                "username": username_2,
                "comment_id": comment_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["likes"], 1)

        # Проверка, что лайк на комментарии изменяет рейтинг пользователя.
        request_data = ["rating"]
        answer = requests.get(
            self.localhost + "/users/data",
            json={"username": username, "requested_data": request_data},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["rating"], 1)

        # Проверка, что лайк на комментарии отменяется, если уже был поставлен.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "comment_id": comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["likes"]
        answer = requests.get(
            self.localhost + "/article/comment/data",
            json={
                "username": username_2,
                "comment_id": comment_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["likes"], 0)

        # Проверка, что убирание лайка на комментарии изменяет рейтинг.
        request_data = ["rating"]
        answer = requests.get(
            self.localhost + "/users/data",
            json={"username": username, "requested_data": request_data},
        )
        self.assertEqual(answer.json()["rating"], 0)

        # Проверка, что лайк на комментарии перезаписывает дизлайк.
        answer = requests.post(
            self.localhost + "/article/comment/dislike",
            json={"username": username_2, "comment_id": comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "comment_id": comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["likes", "dislikes"]
        answer = requests.get(
            self.localhost + "/article/comment/data",
            json={
                "username": username_2,
                "comment_id": comment_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["likes"], 1)
        self.assertEqual(answer.json()["dislikes"], 0)

        # Проверка, что лайк на одном комментарии не задевает лайк на другом комментарии того же пользователя.
        other_comment_id = self.add_comment(username, article_id)
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "comment_id": other_comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        answer = requests.get(
            self.localhost + "/article/comment/data",
            json={
                "username": username_2,
                "comment_id": comment_id,
                "requested_data": ["likes"],
            },
        )
        self.assertEqual(answer.json()["likes"], 1)
        answer = requests.get(
            self.localhost + "/article/comment/data",
            json={
                "username": username_2,
                "comment_id": other_comment_id,
                "requested_data": ["likes"],
            },
        )
        self.assertEqual(answer.json()["likes"], 1)

    def test_article_comment_dislike_post(self):
        endpoint = "/article/comment/dislike"
        method = "post"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        user_info = self.add_user()
        username_2 = user_info[0]
        article_id = self.add_article(username=username)

        comment_id = self.add_comment(username, article_id)

        # Проверка, что дизлайк применился к комментарию.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "comment_id": comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["dislikes"]
        answer = requests.get(
            self.localhost + "/article/comment/data",
            json={
                "username": username_2,
                "comment_id": comment_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["dislikes"], 1)

        # Проверка, что дизлайк на комментарии изменяет рейтинг пользователя.
        request_data = ["rating"]
        answer = requests.get(
            self.localhost + "/users/data",
            json={"username": username, "requested_data": request_data},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["rating"], -1)

        # Проверка, что дизлайк на комментарии отменяется, если уже был поставлен.
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "comment_id": comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["dislikes"]
        answer = requests.get(
            self.localhost + "/article/comment/data",
            json={
                "username": username_2,
                "comment_id": comment_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["dislikes"], 0)

        # Проверка, что убирание дизлайка на комментарии изменяет рейтинг.
        request_data = ["rating"]
        answer = requests.get(
            self.localhost + "/users/data",
            json={"username": username, "requested_data": request_data},
        )
        self.assertEqual(answer.json()["rating"], 0)

        # Проверка, что дизлайк на комментарии перезаписывает лайк.
        answer = requests.post(
            self.localhost + "/article/comment/like",
            json={"username": username_2, "comment_id": comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username_2, "comment_id": comment_id},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        request_data = ["likes", "dislikes"]
        answer = requests.get(
            self.localhost + "/article/comment/data",
            json={
                "username": username_2,
                "comment_id": comment_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        self.assertEqual(answer.json()["likes"], 0)
        self.assertEqual(answer.json()["dislikes"], 1)

    def test_article_comment_data_get(self):
        endpoint = "/article/comment/data"
        method = "get"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]

        user_info = self.add_user()
        username = user_info[0]
        article_id = self.add_article(username=username)
        request_data = [
            "likes",
            "dislikes",
            "rating",
            "creation_date",
            "is_liked",
            "is_disliked",
        ]

        comment_id = self.add_comment(username, article_id)

        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "comment_id": comment_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        for field in request_data:
            self.assertIn(field, answer.json())

        # test unlogged users
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": "unlogged_user",
                "comment_id": comment_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        for field in request_data:
            self.assertIn(field, answer.json())

        # trying to read a non-existent article
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "comment_id": -1,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

    def test_article_data_get(self):
        endpoint = "/article/data"
        method = "get"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        article_id = self.add_article(username=username)
        request_data = [
            "likes",
            "dislikes",
            "rating",
            "comments_count",
            "creation_date",
            "is_liked",
            "is_disliked",
        ]
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "article_id": article_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        for field in request_data:
            self.assertIn(field, answer.json())

        # test unlogged users
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": "unlogged_user",
                "article_id": article_id,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=answer.json()["status"]
        )
        for field in request_data:
            self.assertIn(field, answer.json())

        # trying to read a non-existent article
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "article_id": -1,
                "requested_data": request_data,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

    def test_pages(self):
        endpoint = "/pages"
        method = "get"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]

        user_info = self.add_user()
        username2 = user_info[0]

        user_info = self.add_user()
        liker = user_info[0]

        article_1 = self.add_article(
            username, tags=["tag1", "tag2"], preview={"type": "text", "data": "text1"}
        )
        article_2 = self.add_article(
            username, tags=["tag2", "tag3"], preview={"type": "text", "data": "text2"}
        )
        self.like_article(article_2, username2)

        article_3 = self.add_article(
            username, tags=["tag1", "tag4"], preview={"type": "text", "data": "text3"}
        )
        self.like_article(article_3, username2)
        self.like_article(article_3, liker)

        # invalid sort_column / sort_direction values
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "indexes": [0],
                "sort_column": "bogus_column",
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "indexes": [0],
                "sort_direction": "sideways",
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

        # happy path: sort by rating, descending
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "indexes": [0],
                "sort_column": "rating",
                "sort_direction": "descending",
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        page = answer.json()["pages"]["0"]
        self.assertEqual(
            [article["id"] for article in page], [article_3, article_2, article_1]
        )
        for article in page:
            self.assertIn("preview_content", article)
            self.assertIn("tags", article)
            self.assertIn("creation_date", article)
            self.assertIn("author_preview", article)
            self.assertIn("likes", article)
            self.assertIn("dislikes", article)
            self.assertIn("rating", article)
            self.assertIn("comments_count", article)
            self.assertIn("is_liked", article)
            self.assertIn("is_disliked", article)
        self.assertEqual(page[0]["author_preview"]["username"], username)

        # sort by rating, ascending
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "indexes": [0],
                "sort_column": "rating",
                "sort_direction": "ascending",
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        page = answer.json()["pages"]["0"]
        self.assertEqual(
            [article["id"] for article in page], [article_1, article_2, article_3]
        )

        # sort by creation_date, descending (default)
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "indexes": [0]},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        page = answer.json()["pages"]["0"]
        self.assertEqual(
            [article["id"] for article in page], [article_3, article_2, article_1]
        )

        # sort by creation_date, ascending
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "indexes": [0],
                "sort_column": "creation_date",
                "sort_direction": "ascending",
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        page = answer.json()["pages"]["0"]
        self.assertEqual(
            [article["id"] for article in page], [article_1, article_2, article_3]
        )

        # include_tags: only articles having ALL requested tags
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "indexes": [0], "include_tags": ["tag4"]},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        page = answer.json()["pages"]["0"]
        self.assertEqual([article["id"] for article in page], [article_3])

        # exclude_tags
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "indexes": [0],
                "sort_column": "creation_date",
                "sort_direction": "ascending",
                "exclude_tags": ["tag4"],
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        page = answer.json()["pages"]["0"]
        self.assertEqual([article["id"] for article in page], [article_1, article_2])

        # include_authors / exclude_authors
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "indexes": [0], "include_authors": [username2]},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(answer.json()["pages"]["0"], [])

        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "indexes": [0], "exclude_authors": [username]},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(answer.json()["pages"]["0"], [])

        # bounds on rating
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "indexes": [0],
                "sort_column": "rating",
                "sort_direction": "descending",
                "lower_rating": 0,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        page = answer.json()["pages"]["0"]
        self.assertEqual([article["id"] for article in page], [article_3, article_2])

        # blacklist: blocked authors are always excluded
        answer = requests.post(
            self.localhost + "/users/data",
            json={"username": username, "blocked-users": [username2]},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        article_4 = self.add_article(
            username2, tags=["tag5"], preview={"type": "text", "data": "text4"}
        )
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "indexes": [0]},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        page_ids = [article["id"] for article in answer.json()["pages"]["0"]]
        self.assertNotIn(article_4, page_ids)

        # subscriptions: include_nonsub=False restricts to subscribed tags/authors
        answer = requests.post(
            self.localhost + "/users/data",
            json={"username": username, "sub-tags": ["tag4"]},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "indexes": [0], "include_nonsub": False},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            [article["id"] for article in answer.json()["pages"]["0"]], [article_3]
        )

        # unlogged users can browse pages too
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": "unlogged_user", "indexes": [0]},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        page_ids = [article["id"] for article in answer.json()["pages"]["0"]]
        self.assertIn(article_4, page_ids)

        # pagination across multiple indexes
        user_info = self.add_user()
        username3 = user_info[0]
        paginated_ids = []
        for i in range(7):
            paginated_ids.append(
                self.add_article(
                    username3,
                    tags=["pagination_tag"],
                    preview={"type": "text", "data": f"page_text_{i}"},
                )
            )
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": "unlogged_user",
                "indexes": [0, 1],
                "include_tags": ["pagination_tag"],
                "sort_column": "creation_date",
                "sort_direction": "ascending",
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            [article["id"] for article in answer.json()["pages"]["0"]],
            paginated_ids[:5],
        )
        self.assertEqual(
            [article["id"] for article in answer.json()["pages"]["1"]],
            paginated_ids[5:],
        )

    def test_users_post(self):
        endpoint = "/users"
        method = "post"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        username = "test_name_1"
        nickname = "test_name_1"
        email = "test@,test.test"
        password = "password"
        avatar = "avatar"

        # happy path
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": username,
                "nickname": nickname,
                "email": email,
                "password": password,
                "avatar": avatar,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        requested_data = [
            "nickname",
            "email",
            "name_history",
            "avatar",
            "creation_date",
            "rating",
        ]
        answer = requests.get(
            self.localhost + "/users/data",
            json={"username": username, "requested_data": requested_data},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(nickname, answer.json()["nickname"])
        self.assertEqual(email, answer.json()["email"])
        self.assertEqual([nickname], answer.json()["name_history"])
        self.assertEqual(avatar, answer.json()["avatar"])
        self.assertEqual(0, answer.json()["rating"])
        self.assertIn("creation_date", answer.json())

        # username is a primary key: same username with a different email must be rejected
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": username,
                "nickname": "other_nickname",
                "email": "other_email@test.test",
                "password": password,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

        # email is unique: different username with the same email must be rejected
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": "other_username",
                "nickname": "other_nickname",
                "email": email,
                "password": password,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

    def test_users_data_get(self):
        endpoint = "/users/data"
        method = "get"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]

        # happy path
        requested_data = [
            "nickname",
            "email",
            "name_history",
            "avatar",
            "blocked_tags",
            "creation_date",
            "rating",
        ]
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "requested_data": requested_data},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertIn("nickname", answer.json())
        self.assertIn("email", answer.json())
        self.assertIn("name_history", answer.json())
        self.assertIn("avatar", answer.json())
        self.assertIn("creation_date", answer.json())
        self.assertIn("rating", answer.json())

        # test unlogged users
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": "unlogged_user", "requested_data": requested_data},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

    def test_users_data_post(self):
        endpoint = "/users/data"
        method = "post"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        user_name = user_info[2]

        # happy path
        nickname = "new_name"
        email = "new_email@email.email"
        avatar = "avatar_link"
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": username,
                "nickname": nickname,
                "avatar": avatar,
                "email": email,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        requested_data = ["nickname", "email", "name_history", "avatar"]
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "requested_data": requested_data},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(answer.json()["nickname"], nickname)
        self.assertEqual(answer.json()["name_history"], [nickname, user_name])
        self.assertEqual(answer.json()["avatar"], avatar)

        # subscriptions and blacklists (tags and users)
        other_user_info = self.add_user()
        other_username = other_user_info[0]
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": username,
                "sub-tags": ["tag1", "tag2"],
                "blocked-tags": ["tag3"],
                "sub-users": [other_username],
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )

        requested_data = ["sub_tags", "blocked_tags", "sub_users", "blocked_users"]
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "requested_data": requested_data},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(sorted(answer.json()["sub_tags"]), ["tag1", "tag2"])
        self.assertEqual(answer.json()["blocked_tags"], ["tag3"])
        self.assertEqual(answer.json()["sub_users"], [other_username])
        self.assertEqual(answer.json()["blocked_users"], [])

        # blocking a user must remove any existing subscription to them, and vice versa
        answer = requests.post(
            self.localhost + endpoint,
            json={"username": username, "blocked-users": [other_username]},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        answer = requests.get(
            self.localhost + endpoint,
            json={
                "username": username,
                "requested_data": ["sub_users", "blocked_users"],
            },
        )
        self.assertEqual(answer.json()["sub_users"], [])
        self.assertEqual(answer.json()["blocked_users"], [other_username])

        # test unlogged users
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": "unlogged_user",
                "nickname": nickname,
                "avatar": avatar,
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

    def test_user_password_post(self):
        endpoint = "/users/password"
        method = "post"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        password = user_info[1]

        # wrong previous password must be rejected
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": username,
                "previous_password": password + "wrong",
                "new_password": "1234",
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )
        answer = requests.get(
            self.localhost + "/login",
            json={"username": username, "password": password},
        )
        self.assertEqual(
            answer.json()["is-correct"], True, msg=str(answer.json()["status"])
        )

        # happy path
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": username,
                "previous_password": password,
                "new_password": "1234",
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        answer = requests.get(
            self.localhost + "/login",
            json={"username": username, "password": "1234"},
        )
        self.assertEqual(
            answer.json()["is-correct"], True, msg=str(answer.json()["status"])
        )

        # test unlogged users
        answer = requests.post(
            self.localhost + endpoint,
            json={
                "username": "unlogged_user",
                "previous_password": password,
                "new_password": "1234",
            },
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

    def test_login_get(self):
        endpoint = "/login"
        method = "get"
        answer = requests.options(self.localhost + endpoint)
        self.check_structure(
            endpoint=endpoint, method=method, structure=answer.json()[method]
        )

        user_info = self.add_user()
        username = user_info[0]
        password = user_info[1]
        email = user_info[3]

        # happy path
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": str(username), "password": password},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["is-correct"], True, msg=str(answer.json()["status"])
        )

        answer = requests.get(
            self.localhost + endpoint, json={"email": email, "password": password}
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["is-correct"], True, msg=str(answer.json()["status"])
        )

        # special rule: incorrect id return is-correct = False
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": str(username) + "1", "password": password},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "OK", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["is-correct"], False, msg=str(answer.json()["is-correct"])
        )

        # both username and email must be rejected
        answer = requests.get(
            self.localhost + endpoint,
            json={"username": username, "email": email, "password": password},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

        # neither username nor email must be rejected, not crash
        answer = requests.get(
            self.localhost + endpoint,
            json={"password": password},
        )
        self.assertEqual(
            answer.json()["status"]["type"], "ERROR", msg=str(answer.json()["status"])
        )
        self.assertEqual(
            answer.json()["status"]["error_type"],
            "ValueError",
            msg=str(answer.json()["status"]),
        )

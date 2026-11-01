"""
Этот файл служит для хранения fixtures pytest: поднятие настоящего серверного
процесса поверх чистой тестовой БД перед каждым тестом и фабрики тестовых
сущностей (пользователь, статья, комментарий, лайк), используемые тестами в
tests/routes/*.py.
"""

import os
import signal
import subprocess
import time
from collections.abc import Callable, Generator

import pytest
import requests
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

from src.db import scheme
from tests.helpers import LOCALHOST, WORKDIR, assert_ok, auth_headers

SERVER_START_TIMEOUT_S = 30
SERVER_STOP_TIMEOUT_S = 10


def pytest_sessionstart(session: pytest.Session) -> None:
    """Хук pytest: убивает сервер, оставшийся от прошлого некорректно завершенного
    прогона тестов. Достаточно сделать это один раз в начале сессии, а не перед
    каждым тестом, так как это может произойти только между прогонами pytest.

    Args:
        session: сессия pytest (не используется).

    Returns:
        None
    """
    if os.path.exists(WORKDIR):
        with open(os.path.join(WORKDIR, "lastpid.txt"), "r") as pid_file:
            pid = pid_file.readline()
        try:
            os.kill(int(pid), signal.SIGKILL)
        except Exception:
            pass


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    """Читает `.env` и создает SQLAlchemy engine к тестовой БД один раз на сессию.

    Args:
        None

    Returns:
        sqlalchemy.Engine: engine, подключенный к MVP_DB_URL_TEST.
    """
    load_dotenv(dotenv_path="../.env")
    return create_engine(os.getenv("MVP_DB_URL_TEST"))


def _wait_for_server(process: subprocess.Popen) -> None:
    """Ждёт, пока сервер начнёт отвечать по HTTP. Настоящий запрос вместо чтения
    его вывода: так тест не зависает, если сервер упал при запуске, и не ждёт
    лишнего, если сервер поднялся быстро.

    Args:
        process: процесс тестового сервера.

    Returns:
        None; если сервер упал или не поднялся вовремя, тест проваливается.
    """
    deadline = time.monotonic() + SERVER_START_TIMEOUT_S
    while time.monotonic() < deadline:
        if process.poll() is not None:
            _, stderr = process.communicate()
            pytest.fail(f"Server exited on startup:\n{stderr.decode('utf8')}")
        try:
            requests.options(LOCALHOST + "/users", timeout=1)
            return
        except requests.ConnectionError:
            time.sleep(0.05)
    process.kill()
    pytest.fail(f"Server did not start in {SERVER_START_TIMEOUT_S} s")


@pytest.fixture(autouse=True)
def server(db_engine: Engine) -> Generator[subprocess.Popen, None, None]:
    """Пересоздает с нуля тестовую БД и поднимает `start.py -t` перед каждым тестом,
    останавливая его после и печатая его stderr.

    Args:
        db_engine: fixture engine тестовой БД.

    Returns:
        Generator[subprocess.Popen]: процесс тестового сервера.
    """
    scheme.Base.metadata.drop_all(db_engine)
    scheme.Base.metadata.create_all(db_engine)

    process = subprocess.Popen(
        ["python3", "/app/start.py", "-t", "--working-directory", WORKDIR],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _wait_for_server(process)

    with open(os.path.join(WORKDIR, "lastpid.txt"), "w+") as pid_file:
        pid_file.write(str(process.pid))

    yield process

    process.terminate()
    try:
        _, stderr = process.communicate(timeout=SERVER_STOP_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        # Следующий тест не сможет занять порт, пока этот сервер жив.
        process.kill()
        _, stderr = process.communicate()
    print(stderr.decode("utf8"))


@pytest.fixture
def add_user(server: subprocess.Popen) -> Callable[[], tuple]:
    """Дает функцию для регистрации нового тестового пользователя через POST
    /users и немедленного входа через POST /auth/login.

    Args:
        server: fixture тестового сервера (гарантирует порядок запуска).

    Returns:
        Callable[[], tuple]: функция без аргументов, возвращающая
            (username, password, nickname, email, access_token, refresh_token)
            очередного нового пользователя.
    """
    user_count = 0

    def _add_user() -> tuple:
        nonlocal user_count
        username = f"tester_username_{user_count}"
        nickname = f"tester_nickname_{user_count}"
        # Не совпадает с helpers.DEFAULT_VALUES: иначе проверка, что пароль не
        # попал в лог, срабатывала бы на значениях других строковых полей.
        password = "tester_password"
        email = f"test_{user_count}@test.test"
        answer = requests.post(
            LOCALHOST + "/users",
            json={
                "username": username,
                "nickname": nickname,
                "password": password,
                "email": email,
            },
        )
        assert_ok(answer, 201)
        user_count += 1

        login_answer = requests.post(
            LOCALHOST + "/auth/login",
            json={"username": username, "password": password},
        )
        assert_ok(login_answer)
        access_token = login_answer.json()["access_token"]
        refresh_token = login_answer.json()["refresh_token"]
        return (username, password, nickname, email, access_token, refresh_token)

    return _add_user


@pytest.fixture
def add_article(server: subprocess.Popen) -> Callable[..., int]:
    """Дает функцию для публикации тестовой статьи через POST /articles.

    Args:
        server: fixture тестового сервера (гарантирует порядок запуска).

    Returns:
        Callable[..., int]: функция (access_token, tags=None, preview=None) ->
            article_id; автор статьи — владелец access_token.
    """

    def _add_article(access_token: str, tags: list = None, preview: dict = None) -> int:
        # is None, а не `not`: явно переданные пустые значения нельзя подменять.
        if preview is None:
            preview = {"type": "image", "data": "ref"}
        if tags is None:
            tags = ["tag1", "tag2"]
        response = requests.post(
            LOCALHOST + "/articles",
            json={
                "title": "test_name",
                "preview": preview,
                "tags": tags,
                "body": {"block1": "text"},
            },
            headers=auth_headers(access_token),
        )
        assert_ok(response, 201)
        return response.json()["article_id"]

    return _add_article


@pytest.fixture
def add_comment(server: subprocess.Popen) -> Callable[[str, int], int]:
    """Дает функцию для добавления тестового комментария верхнего уровня через
    POST /articles/{id}/comments.

    Args:
        server: fixture тестового сервера (гарантирует порядок запуска).

    Returns:
        Callable[[str, int], int]: функция (access_token, article_id) -> id
            комментария; автор комментария — владелец access_token.
    """

    def _add_comment(access_token: str, article_id: int) -> int:
        response = requests.post(
            f"{LOCALHOST}/articles/{article_id}/comments",
            json={"text": "text", "parent": -1},
            headers=auth_headers(access_token),
        )
        assert_ok(response, 201)
        return response.json()["id"]

    return _add_comment


@pytest.fixture
def like_article(server: subprocess.Popen) -> Callable[[int, str], None]:
    """Дает функцию для лайка статьи через PUT /articles/{id}/like.

    Args:
        server: fixture тестового сервера (гарантирует порядок запуска).

    Returns:
        Callable[[int, str], None]: функция (article_id, access_token); лайк
            ставится от имени владельца access_token.
    """

    def _like_article(article_id: int, access_token: str) -> None:
        response = requests.put(
            f"{LOCALHOST}/articles/{article_id}/like",
            headers=auth_headers(access_token),
        )
        assert_ok(response, 204)

    return _like_article

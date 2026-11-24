"""
Этот файл служит для хранения unit-тестов конфигурации сервера (src/config.py):
проверки динамического формирования путей через DynamicPath и отсутствия устаревших
настроек SQLite.
"""

import os
from pathlib import Path

import pytest

from src import config


def test_dynamic_path_tracks_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path_obj = config.DynamicPath("log", "server_api.log")

    assert path_obj.parts == ("log", "server_api.log")
    assert not hasattr(path_obj, "endpont")

    monkeypatch.chdir(tmp_path)
    expected_dir = os.path.join(str(tmp_path), "log")
    expected_file = os.path.join(expected_dir, "server_api.log")
    assert path_obj.path == expected_file
    assert config.log_directory.path == expected_dir
    assert config.log_server_api.path == expected_file


def test_legacy_sqlite_and_secret_settings_removed() -> None:
    for attr in (
        "current_directory",
        "backup_directory",
        "db_user_directory",
        "db_user",
        "db_article_directory",
        "db_article",
        "db_comment_directory",
        "db_comment",
        "log_db_api",
        "delimiter",
        "user_id_name",
        "user_table_name",
        "article_id_name",
        "article_table_name",
        "comment_id_name",
        "comment_table_name",
        "db_url",
    ):
        assert not hasattr(config, attr)

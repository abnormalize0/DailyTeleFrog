---
id: 0041
title: Отвязать тесты от жёстких Docker-путей и заменить sleep 30s на проверку готовности MySQL
areas: [tests, deploy]
date: 2026-11-23
---

# 0041. Отвязать тесты от жёстких Docker-путей и заменить sleep 30s на проверку готовности MySQL

## Проблема
Тесты не запускаются локально вне Docker-контейнера из-за зашитых путей и обязательных переменных окружения, а `Makefile` ждёт готовности MySQL фиксированной паузой `sleep 30s`.

## Как возникает и к чему приводит
- *Как возникает:*
  - `tests/conftest.py` использует жёсткий путь `"/app/start.py"` и `load_dotenv(dotenv_path="../.env")`;
  - `tests/helpers.py` на уровне модуля вычисляет `WORKDIR = os.getenv("MVP_PATH") + "/test_tmp"`;
  - `src/conftest.py` читает `os.environ["MVP_DB_URL_TEST"]` без вызова `load_dotenv()`;
  - `Makefile` (`test-env`) завершается командой `sleep 30s`.
- *Негативный эффект:*
  - локальный запуск `pytest src` или `pytest tests` падает при импорте (`TypeError` без `MVP_PATH`, `KeyError` без экспортированного `MVP_DB_URL_TEST`) или не находит `/app/start.py` и `../.env`;
  - после удаления `/app/.env` из образа (см. `0038`) чтение `../.env` в Docker перестанет находить файл;
  - `sleep 30s` в `Makefile` либо тратит лишнее время, либо не дожидается MySQL на медленной машине.

## Желаемое поведение
- Вычислять корень `server/` через `Path(__file__).resolve().parent.parent` в `tests/conftest.py`, `tests/helpers.py` и `src/conftest.py`.
- В `tests/helpers.py` брать `MVP_PATH` с fallback на корень `server/`.
- В `tests/conftest.py` и `src/conftest.py` загружать `SERVER_ROOT / ".env"` через `load_dotenv(..., override=False)`, чтобы в Docker сохранялся приоритет `--env-file .env`, а локально подхватывался `server/.env`.
- В `tests/conftest.py` запускать сервер через `sys.executable` (без жёсткого `"/app/start.py"`).
- В `Makefile` (`test-env`) заменить `sleep 30s` на цикл ожидания с таймаутом (например, 60 попыток по 1 сек), проверяющий готовность MySQL реальным подключением к целевой БД (`SELECT 1` внутри `db-test`), чтобы избежать ложного срабатывания на временном init-сервере, и падающий с понятной ошибкой при истечении таймаута.

## Готово, когда
- В `tests/` и `src/conftest.py` нет жёстких путей `/app/...` и `../.env`.
- Импорт `tests/helpers.py` и запуск `pytest` работают без предварительно заданного `MVP_PATH`.
- `Makefile` не использует `sleep 30s` и корректно дожидается готовности MySQL.
- Прогнан `black` и полный `make test` проходит.

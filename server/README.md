# Сервер DailyTeleFrog

Бэкенд-сервер на Flask + SQLAlchemy + MySQL.

## Локальная установка

1. Перейдите в директорию `server/` и создайте виртуальное окружение:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r deployment/requirements.txt
```

> **Примечание:** для сборки `mysqlclient` вне Docker понадобятся системные пакеты разработки MySQL (`python3-dev`, `default-libmysqlclient-dev`, `build-essential`, `pkg-config` на Debian/Ubuntu).

## Конфигурация

Настройки задаются через переменные окружения (в Docker и при запуске `pytest` они подхватываются из файла `.env` в корне `server/`):

- `MVP_DB_URL_PRODUCTION` — SQLAlchemy DB URL для продакшн-режима.
- `MVP_DB_URL_TEST` — SQLAlchemy DB URL для тестового режима и тестов.
- `MVP_PATH` — корень рабочей директории для e2e-тестов (внутри Docker-контейнеров — `/app`).
- `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` — параметры MySQL для Docker-контейнера `mysql:1.0` (`make run`, `make test-env`).

Схема базы данных не создаётся через `start.py` — она должна уже существовать (тестовый набор пересоздаёт таблицы из `scheme.Base.metadata`).

## Запуск сервера

Из директории `server/` (при локальном запуске переменные из `.env` нужно предварительно экспортировать в shell, например `set -a; source .env; set +a`):

```bash
python3 start.py                               # продакшн-режим (MVP_DB_URL_PRODUCTION)
python3 start.py -t                            # тестовый режим (MVP_DB_URL_TEST)
python3 start.py -t --working-directory <dir>  # перейти в <dir> перед запуском (логи пишутся в <dir>/log)
```

## Docker

В директории `server/` команда `make` без аргументов выводит список всех доступных целей:

```bash
make build-os    # базовый образ с системными пакетами и Python-зависимостями
make build-code  # образ сервера (использует os_server:1.0, поэтому собирается после build-os)
make build-db    # образ MySQL
make run         # поднять сеть и контейнеры БД и сервера
```

## Тестирование

Запуск обоих слоёв тестов (unit-тесты `src/` и e2e-тесты `tests/`) в Docker. Перед первым запуском должен быть собран базовый образ `make build-os`:

```bash
make test       # unit- и e2e-тесты; логи сервера копируются в test_logs/ даже при падении
make test-unit  # только unit-тесты
```

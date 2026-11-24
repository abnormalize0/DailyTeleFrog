---
id: 0028
title: Удалить мёртвый код от старой архитектуры на SQLite и актуализировать README
areas: [deploy, logging]
date: 2026-11-23
---

# 0028. Удалить мёртвый код от старой архитектуры на SQLite и актуализировать README

## Проблема
В `start.py`, `src/config.py` и `README.md` сохранился неиспользуемый код, настройки и инструкции от ранней версии проекта на SQLite, включая захардкоженный пароль БД и создание пустого лог-файла `db_api.log` при каждом запуске сервера.

## Как возникает и к чему приводит
- *Как возникает:* при переходе на MySQL + SQLAlchemy старый код не был удалён:
  - в `start.py` остались нигде не вызываемые `backup()`, `init_users()`, `init_articles()`, `init_comments()` (с импортами `sqlite3`, `shutil`, `datetime`), а `set_up_loggers()` настраивает неиспользуемый логгер `config.log_db_api.path`;
  - в `src/config.py` остались неиспользуемые `current_directory`, `backup_directory`, пути к `.db`-файлам (`db_user*`, `db_article*`, `db_comment*`), `log_db_api`, `delimiter`, имена таблиц и колонок (`*_id_name`, `*_table_name`), опечатка `DynamicPath.endpont`, а также неиспользуемый `db_url = "mysql://server:4321@127.0.0.1/db"` с захардкоженным паролем;
  - в `README.md` указаны устаревшие шаги (`pip install -r requirements.txt` вместо `deployment/requirements.txt`, ручной `PYTHONPATH`, нет `.env`, `start.py` и `make test`).
- *Негативный эффект:*
  - мёртвый код и устаревший `README.md` вводят в заблуждение при чтении репозитория и при онбординге/ревью портфолио;
  - захардкоженный пароль в `src/config.py` вызывает срабатывания сканеров секретов, хотя строка даже не используется;
  - при каждом запуске сервера создаётся пустой файл `log/db_api.log`.

## Желаемое поведение
- Из `start.py` удалены `backup()`, `init_users()`, `init_articles()`, `init_comments()`, их неиспользуемые импорты и настройка `log_db_api`.
- Из `src/config.py` удалены все неиспользуемые SQLite-настройки, `log_db_api` и захардкоженный `db_url`; исправлена опечатка `DynamicPath.endpont` (на `parts`/`segments`) и опечатка в docstring.
- `README.md` отражает актуальный способ установки, настройки `.env`, запуска сервера и прогона тестов (в согласии с `AGENTS.md` и `Makefile`).

## Готово, когда
- В `start.py` и `src/config.py` нет неиспользуемых SQLite-функций, мёртвых констант, захардкоженного `db_url` и настройки пустого `db_api.log`.
- При запуске сервера не создаётся пустой `log/db_api.log`.
- `README.md` содержит актуальные команды установки, запуска и тестирования.
- Прогнан `black` и полный `make test` проходит.

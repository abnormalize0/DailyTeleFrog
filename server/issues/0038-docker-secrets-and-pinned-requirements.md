---
id: 0038
title: Убрать секреты из Docker-образов и зафиксировать зависимости
areas: [deploy]
date: 2026-11-23
---

# 0038. Убрать секреты из Docker-образов и зафиксировать зависимости

## Проблема
В Docker-образах сервера и MySQL зашиваются секреты и пустые переменные сборки, а зависимости Python не зафиксированы по версиям и смешивают прод- и dev-пакеты.

## Как возникает и к чему приводит
- *Как возникает:*
  - `deployment/code_server.dockerfile` содержит `COPY .env /app/.env`, хотя `Makefile` передаёт `--env-file .env` при `docker run`; при этом отсутствует `.dockerignore`;
  - `deployment/code_mysql.dockerfile` содержит 4 строки `ENV MYSQL_*=${MYSQL_*}` без `ARG`;
  - `deployment/requirements.txt` перечисляет пакеты без версий (`==`), включает тестовые пакеты (`pytest`, `requests`) и не содержит `black`.
- *Негативный эффект:*
  - файл `.env` с секретами и паролями попадает прямо в слой образа `code_server`;
  - в контекст сборки Docker попадают лишние файлы (`test_logs/`, `test_tmp/`, `log/`, `.env`, `.git/`);
  - в `code_mysql.dockerfile` зашиваются пустые переменные `MYSQL_*`;
  - сборки невоспроизводимы из-за незафиксированных версий, а тестовые пакеты едут в прод-образ.

## Желаемое поведение
- Удалить `COPY .env /app/.env` из `deployment/code_server.dockerfile` и добавить `.dockerignore` (исключить `.env`, `test_logs/`, `test_tmp/`, `log/`, `__pycache__/`, `.git/`).
- Удалить 4 строки `ENV MYSQL_*=${MYSQL_*}` из `deployment/code_mysql.dockerfile`.
- Зафиксировать точные версии (`==`) и разделить зависимости на `deployment/requirements.txt` (только прод runtime) и `deployment/requirements-dev.txt` (`-r requirements.txt` + `pytest`, `requests`, `black`).
- Перевести `deployment/os_server.dockerfile` / `deployment/code_server.dockerfile` и `Makefile` на multi-stage сборку: прод-образ ставит только `requirements.txt`, а тестовый stage доустанавливает `requirements-dev.txt`.

## Готово, когда
- В собранном прод-образе отсутствуют `.env`, `pytest`, `requests` и `black`.
- В `deployment/code_mysql.dockerfile` нет пустых `ENV MYSQL_*`.
- Версии пакетов зафиксированы через `==`.
- `make build-os`, `make build-code`, `make build-db` и полный `make test` проходят.

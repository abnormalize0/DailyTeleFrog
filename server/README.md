Установка сервера.

[[_TOC_]]

# Создание виртуальной среды

1. Перейдите в папку сервера
2. Создайте виртуальную среду командой `python -m venv ./your/path/to/venv`
3. В файле `./your/path/to/venv/bin/activate` добавьте переменную окружения PYTHONPATH и ее очистку в deactivate по аналогии с другим кодом. Переменная PYTHONPATH должна указывать на папку с сервером.

# Настройка виртуальной среды

1. Войдите в виртуальную среду.
2. Установите необходимые зависимости командой `pip install -r requirements.txt`
3. Установите клиент mysql по инструкции: https://pypi.org/project/mysqlclient/

# Запуск сервиса базы данных

1. Убедитесь, что у вас установлен make и docker.
2. В папке сервера выполните команду `make`, чтобы посмотреть список доступных опций для сборки и запуска сервисов.
3. Соберите сервер, а затем запустите его.

# Remote Dev Database

## General Connection

- URI: mysql://avnadmin:AVNS_FtxGUMQHo_0Xmq5KVMc@mysql-274e9cc5-serynabatov-46b9.i.aivencloud.com:11974/defaultdb?ssl-mode=REQUIRED
- database name: defaultdb
- host: mysql-274e9cc5-serynabatov-46b9.i.aivencloud.com
- port: 11974
- user: avnadmin
- password: AVNS_FtxGUMQHo_0Xmq5KVMc
- SSL mode: REQUIRED
- CA Certificate: under the certificates folder (we should redistribute it later)

Service has been deployed on Aiven:

```
https://console.aiven.io/account/a4d3ab17f06c/project/serynabatov-46b9/services/mysql-274e9cc5/overview
```
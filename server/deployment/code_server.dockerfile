ARG MIRROR=dockerhub.timeweb.cloud
FROM os_server:1.0

COPY src /app/src
COPY .env /app/.env
COPY start.py /app/start.py

ENV PYTHONPATH=/app
# Контейнер только держит окружение для тестов и `docker exec`, а сервер запускается
# явной командой (см. Makefile). Поэтому срока жизни нет: контейнер удаляет следующий
# `make test-env`.
CMD ["sleep", "infinity"]

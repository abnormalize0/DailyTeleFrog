ARG MIRROR=dockerhub.timeweb.cloud
FROM os_server:1.0

COPY src /app/src
COPY .env /app/.env
COPY start.py /app/start.py

ENV PYTHONPATH=/app
CMD ["sleep", "1h"]
ARG MIRROR=dockerhub.timeweb.cloud
FROM os_mvp

COPY ./src /app/src
COPY ./.env /app
COPY ./start.py /app
COPY ./requirements.txt /app

ENV PYTHONPATH=/app
CMD ["sleep", "1h"]
ARG MIRROR=dockerhub.timeweb.cloud
FROM ${MIRROR}/ubuntu:22.04

RUN ["apt-get", "update"]
RUN ["apt-get", "install", "-y", "python3"]
RUN ["apt-get", "install", "-y", "python3-pip"]
# Нужно для установки mysqlclient.
RUN ["apt-get", "install", "-y", "python3-dev", "default-libmysqlclient-dev", "build-essential", "pkg-config"]

RUN ["pip3", "install", "-r", "/app/requirements.txt"]
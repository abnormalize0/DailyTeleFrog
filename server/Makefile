# Автоматический сборщик подсказки, который подсмотрен тут:
# https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
.DEFAULT_GOAL := help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: build
build: ## Собрать образ базы данных PostgreSQL с параметрами из .env конфигурации.
	docker build -t server\:1.0 -f Dockerfile .

.PHONY: run
run: ## Запустить контейнер с образом нашей базы данных.
	docker run --env-file .env -dp 127.0.0.1:3306:3306 server\:1.0

.PHONY: clear
clear: 
	docker stop $(shell docker ps -a -q)
	docker rm $(shell docker ps -a -q)
	docker rmi -f $(shell docker images -aq)

.PHONY: exec
exec: ## ожидает переменную хэша контейнера
	docker exec -it $(CONTAINER) bash

.PHONY: check
check:
	docker ps -a

.PHONY: logs
logs: ## ожидает переменную хэша контейнера
	docker logs $(CONTAINER)
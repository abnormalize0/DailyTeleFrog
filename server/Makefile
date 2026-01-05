# Автоматический сборщик подсказки, который подсмотрен тут:
# https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
.DEFAULT_GOAL := help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: build-os
build-os: ## Собрать образы системы с необходимыми утилитами для всех контенеров.
	docker build -t os_server\:1.0 -f deployment/os_server.dockerfile .

.PHONY: build-code
build-code: ## Собрать образы с использованием кода сервера.
	docker build -t code_server\:1.0 -f deployment/code_server.dockerfile .

.PHONY: build-db
build-db: ## Собрать образ базы данных.
	docker build -t mysql\:1.0 -f deployment/code_mysql.dockerfile .

.PHONY: run
run: ## Запустить контейнеры базы данных и сервера.
	docker network create mvp-net
	docker run --env-file .env -dp 127.0.0.1:3306:3306 --name=db --network=mvp-net mysql\:1.0
	docker run --env-file .env -dp 127.0.0.1:5000:5000 --name=server --network=mvp-net server\:1.0

.PHONY: restart-server
restart-server: ## Обновляет код сервера и перезапускает контейнер.
	docker rm server --force
	docker build -t server\:1.0 -f mvp.dockerfile .
	docker run --env-file .env -dp 127.0.0.1:5000:5000 --name=server server\:1.0

.PHONY: test
test: ## Запуск end-to-end тестов.
	docker rm db-test --force
	docker rm server-test --force
	docker build -t code_mysql\:1.0 -f deployment/code_mysql.dockerfile .
	docker build -t code_server\:1.0 -f deployment/code_server.dockerfile .
	docker run --env-file .env -dp 127.0.0.1:3306:3306 --name=db-test --network=test-net mysql\:1.0
	docker run \
	--env-file .env \
	-dp 127.0.0.1:5000:5000 \
	--name=server-test \
	--network=test-net \
	server\:1.0
	# Контейнеру с бд нужно время, чтобы завестись после того, как он
	# запустился. Если убрать задержку, то будет ошибка "connection
	# refused".
	sleep 60s
	docker cp ./tests server-test:/app/tests
	docker exec -t server-test python3 /app/tests/run_tests.py
	rm -rf test_logs
	docker cp server-test:/app/test_tmp test_logs

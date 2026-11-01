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

# Команда задаётся здесь, потому что CMD образа code_server только держит контейнер
# живым: тесты сами запускают и останавливают сервер внутри него.
RUN_SERVER = docker run --env-file .env -dp 127.0.0.1:5000:5000 --name=server --network=mvp-net -w /app code_server\:1.0 python3 start.py

.PHONY: run
run: ## Запустить контейнеры базы данных и сервера.
	docker network create mvp-net
	docker run --env-file .env -dp 127.0.0.1:3306:3306 --name=db --network=mvp-net mysql\:1.0
	$(RUN_SERVER)

.PHONY: restart-server
restart-server: ## Обновляет код сервера и перезапускает контейнер.
	docker rm server --force
	docker build -t code_server\:1.0 -f deployment/code_server.dockerfile .
	$(RUN_SERVER)

.PHONY: test-env
test-env: ## Поднять чистые контейнеры с MySQL и кодом сервера для тестов.
	docker rm db-test --force
	docker rm server-test --force
	docker network rm test-net --force
	docker network create test-net
	docker build -t mysql\:1.0 -f deployment/code_mysql.dockerfile .
	docker build -t code_server\:1.0 -f deployment/code_server.dockerfile .
	# Флаг разрешает пользователю без SUPER создавать триггеры: ими тесты атомарности
	# вызывают настоящий сбой записи (см. decisions/0009-api-atomicity.md).
	docker run --env-file .env -dp 127.0.0.1:3306:3306 --name=db-test --network=test-net mysql\:1.0 --log-bin-trust-function-creators=1
	docker run \
	--env-file .env \
	-dp 127.0.0.1:5000:5000 \
	--name=server-test \
	--network=test-net \
	code_server\:1.0
	# Контейнеру с бд нужно время, чтобы завестись после того, как он
	# запустился. Если убрать задержку, то будет ошибка "connection
	# refused".
	sleep 30s

.PHONY: test-unit
test-unit: test-env ## Запуск только unit-тестов (без сервера, но с MySQL).
	docker exec -w /app -t server-test python3 -m pytest src -v

.PHONY: test
test: test-env ## Запуск unit- и end-to-end тестов.
	docker cp ./tests server-test:/app/tests
	# Логи копируются и после падения тестов: тогда они нужнее всего. Обычная
	# команда в рецепте остановила бы make на первой ошибке, поэтому коды
	# завершения запоминаются и возвращаются последним шагом.
	docker exec -w /app -t server-test python3 -m pytest src -v; unit_code=$$?; \
	docker exec -w /app -t server-test python3 -m pytest tests -v; e2e_code=$$?; \
	rm -rf test_logs; \
	docker cp server-test:/app/test_tmp test_logs; \
	exit $$(( unit_code || e2e_code ))

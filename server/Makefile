.PHONY: build
build:
	docker build -t server\:1.0 -f Dockerfile .

.PHONY: start
start:
	docker run -dp 127.0.0.1:3306:3306 server\:1.0
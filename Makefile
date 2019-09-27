NAME ?= pjsua
TIME := $(shell date +%s)

all: build start

.PHONY: build start stop login
build:
	docker build --tag="debian/pjsua:1.0" --build-arg CACHEBOOST=$(TIME) .

start:
	docker run -d --init --privileged --rm --network=host --name $(NAME) debian/pjsua:1.0

stop:
	docker stop $(NAME)

login:
	docker exec -it pjsua /bin/bash

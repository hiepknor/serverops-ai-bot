PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
COMPOSE ?= docker compose
IMAGE ?= serverops-ai-bot:latest

.PHONY: help venv install test lint check run init-only docker-build docker-up docker-down docker-logs docker-ps docker-check deploy clean

help:
	@printf '%s\n' \
		'Targets:' \
		'  make install       Create .venv and install dev dependencies' \
		'  make test          Run pytest' \
		'  make lint          Run ruff' \
		'  make check         Run test, lint, and init-only smoke check' \
		'  make run           Run bot locally with .env' \
		'  make init-only     Validate config and initialize audit DB without Telegram polling' \
		'  make docker-build  Build Docker image' \
		'  make docker-up     Start Docker Compose stack' \
		'  make docker-down   Stop Docker Compose stack' \
		'  make docker-logs   Follow container logs' \
		'  make docker-check  Build image and run container smoke check' \
		'  make deploy        Pull/build/start stack on server'

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip

install: venv
	$(VENV_PYTHON) -m pip install -e '.[dev]'

test:
	$(VENV_PYTHON) -m pytest

lint:
	$(VENV_PYTHON) -m ruff check .

init-only:
	SERVEROPS_INIT_ONLY=true $(VENV_PYTHON) -m app.main

check: test lint init-only

run:
	$(VENV_PYTHON) -m app.main

docker-build:
	docker build -t $(IMAGE) .

docker-up:
	$(COMPOSE) up -d --build

docker-down:
	$(COMPOSE) down

docker-logs:
	$(COMPOSE) logs -f --tail=200 serverops-ai-bot

docker-ps:
	$(COMPOSE) ps

docker-check:
	docker build -t $(IMAGE) .
	docker run --rm --env-file .env -e SERVEROPS_INIT_ONLY=true $(IMAGE) python -m app.main
	docker run --rm --env-file .env -e SERVEROPS_INIT_ONLY=true $(IMAGE) python -m app.healthcheck

deploy:
	git pull --ff-only
	$(COMPOSE) up -d --build
	$(COMPOSE) ps

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

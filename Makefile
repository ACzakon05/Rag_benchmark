DOCKER_COMMAND = docker compose
BACKEND = cd backend && uv run

.PHONY: help build up run watch stop down logs migrate create_migration downgrade test lint

help:	## Show this help
	@grep -hE '^[a-z_]+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*##/:/' | column -t -s ':'

build:	## Build docker images
	$(DOCKER_COMMAND) build

up:	## Run the environment in the foreground
	$(DOCKER_COMMAND) up

run:	## Run the environment in the background
	$(DOCKER_COMMAND) up -d

watch:	## Run the environment with hot reload
	$(DOCKER_COMMAND) watch

stop:	## Stop running containers
	$(DOCKER_COMMAND) stop

down:	## Remove containers
	$(DOCKER_COMMAND) down

logs:	## Follow logs of all services
	$(DOCKER_COMMAND) logs -f

# Alembic runs locally against the compose database: with compose watch, files generated
# inside the container would never reach the host.
migrate:	## Apply all migrations
	$(BACKEND) alembic upgrade head

create_migration:	## Autogenerate a migration, e.g. make create_migration m="add x"
	@if [ -z "$(m)" ]; then echo 'Usage: make create_migration m="description"'; exit 1; fi
	$(BACKEND) alembic revision --autogenerate -m "$(m)"

downgrade:	## Revert the last migration
	$(BACKEND) alembic downgrade -1

test:	## Run backend tests
	$(BACKEND) pytest

lint:	## Lint and format backend code
	$(BACKEND) ruff check . --fix && uv run ruff format .

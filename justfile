docker := "docker compose"

# Show this help
default:
    @just --list

# Build docker images
build:
    {{docker}} build

# Run the environment in the foreground
up:
    {{docker}} up

# Run the environment in the background
run:
    {{docker}} up -d

# Run the environment with hot reload
watch:
    {{docker}} watch

# Stop running containers
stop:
    {{docker}} stop

# Remove containers
down:
    {{docker}} down

# Follow logs of all services
logs:
    {{docker}} logs -f

# Apply all migrations (locally, against the compose database)
[working-directory: 'backend']
migrate:
    uv run alembic upgrade head

# Autogenerate a migration, e.g. just create-migration "add x"
[working-directory: 'backend']
create-migration message:
    uv run alembic revision --autogenerate -m "{{message}}"

# Revert the last migration
[working-directory: 'backend']
downgrade:
    uv run alembic downgrade -1

# Run backend tests
[working-directory: 'backend']
test *args:
    uv run pytest {{args}}

# Lint and format backend code
[working-directory: 'backend']
lint:
    uv run ruff check . --fix
    uv run ruff format .

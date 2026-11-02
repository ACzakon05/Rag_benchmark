#!/bin/bash
set -e -x

echo 'Applying migrations...'
alembic upgrade head

echo 'Starting the FastAPI application...'
if [ "$APP_ENV" = "development" ]; then
    exec fastapi dev app/main.py --host 0.0.0.0 --port 8000
else
    exec fastapi run app/main.py --host 0.0.0.0 --port 8000
fi

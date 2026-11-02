#!/bin/bash
set -e -x

echo 'Starting the Celery worker...'
exec celery -A app.celery_app worker --loglevel=info

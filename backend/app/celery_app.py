from celery import Celery

from app.config import settings

celery_app = Celery("rag_benchmark", broker=settings.redis_url, include=["app.runner.tasks"])
celery_app.conf.update(
    task_ignore_result=True,
    # Local models must be called one at a time (GPU memory), so the worker runs one
    # experiment at a time and doesn't reserve the next one while busy.
    worker_concurrency=1,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

from uuid import UUID

from app.celery_app import celery_app
from app.runner.orchestrator import run_experiment


@celery_app.task(name="run_experiment")
def run_experiment_task(experiment_id: str) -> None:
    run_experiment(UUID(experiment_id))

from uuid import UUID

from fastapi import APIRouter, status

from app.database import DbSession
from app.schemas.experiment import ExperimentConfig, ExperimentProgress, ExperimentRead
from app.services.experiment_service import experiment_service

router = APIRouter()


@router.post("/experiments", status_code=status.HTTP_202_ACCEPTED)
def create_experiment(config: ExperimentConfig, db: DbSession) -> ExperimentProgress:
    return experiment_service.create_and_enqueue(db, config)


@router.get("/experiments")
def list_experiments(db: DbSession) -> list[ExperimentRead]:
    return experiment_service.list_read(db)


@router.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: UUID, db: DbSession) -> ExperimentRead:
    return experiment_service.get_read(db, experiment_id)


@router.get("/experiments/{experiment_id}/progress")
def get_progress(experiment_id: UUID, db: DbSession) -> ExperimentProgress:
    return experiment_service.get_progress(db, experiment_id)

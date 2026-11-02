from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile, status

from app.database import DbSession
from app.schemas.dataset import DatasetSummary
from app.services.dataset_service import dataset_service

router = APIRouter()


@router.post("/datasets", status_code=status.HTTP_201_CREATED)
def upload_dataset(
    db: DbSession,
    documents: Annotated[list[UploadFile], File(description=".txt, .md or .pdf files")],
    testset: Annotated[UploadFile, File(description=".json or .csv test set")],
    name: Annotated[str | None, Form()] = None,
) -> DatasetSummary:
    dataset = dataset_service.create_from_upload(
        db,
        documents=[(d.filename or "", d.file) for d in documents],
        testset=(testset.filename or "", testset.file.read()),
        name=name,
    )
    return dataset_service.get_summary(dataset)


@router.get("/datasets")
def list_datasets(db: DbSession) -> list[DatasetSummary]:
    return [dataset_service.get_summary(d) for d in dataset_service.get_all(db, limit=1000)]


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: UUID, db: DbSession) -> DatasetSummary:
    return dataset_service.get_summary(dataset_service.get(db, dataset_id))

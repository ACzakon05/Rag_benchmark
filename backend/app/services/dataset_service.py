import csv
import io
import json
import shutil
from pathlib import Path
from typing import Any, BinaryIO
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Dataset, Document, Question
from app.repositories.repositories import CrudRepository
from app.schemas.dataset import DatasetSummary, DatasetValidationError, TestQuestion
from app.services.services import AppService
from app.utils.exceptions import UnprocessableError

DOCUMENT_EXTENSIONS = {".txt", ".md", ".pdf"}
TESTSET_EXTENSIONS = {".json", ".csv"}


class DatasetService(AppService[Dataset]):
    def create_from_upload(
        self,
        db: Session,
        documents: list[tuple[str, BinaryIO]],
        testset: tuple[str, bytes],
        name: str | None = None,
    ) -> Dataset:
        """Validate everything first, then write the files and rows; nothing is kept on failure."""
        filenames = _validate_documents([filename for filename, _ in documents])
        questions = parse_testset(*testset)

        dataset = Dataset(id=uuid4(), name=name or Path(testset[0]).stem)
        dataset_dir = settings.upload_dir / str(dataset.id)
        dataset_dir.mkdir(parents=True)
        try:
            for filename, (_, content) in zip(filenames, documents, strict=True):
                path = dataset_dir / filename
                with path.open("wb") as out:
                    shutil.copyfileobj(content, out)
                dataset.documents.append(
                    Document(filename=filename, path=str(path), size_bytes=path.stat().st_size)
                )
            dataset.questions = [
                Question(position=i, **q.model_dump()) for i, q in enumerate(questions)
            ]
            return self.create(db, dataset)
        except Exception:
            db.rollback()
            shutil.rmtree(dataset_dir, ignore_errors=True)
            raise

    def get_summary(self, dataset: Dataset) -> DatasetSummary:
        return DatasetSummary(
            dataset_id=str(dataset.id),
            name=dataset.name,
            created_at=dataset.created_at,
            document_count=len(dataset.documents),
            total_size_bytes=sum(d.size_bytes for d in dataset.documents),
            question_count=len(dataset.questions),
        )


def parse_testset(filename: str, content: bytes) -> list[TestQuestion]:
    rows = _read_rows(filename, content)
    errors: list[DatasetValidationError] = []
    questions: list[TestQuestion] = []
    for row_number, row in enumerate(rows, start=1):
        row_errors = _validate_row(row_number, row)
        if row_errors:
            errors.extend(row_errors)
        else:
            questions.append(TestQuestion.model_validate(row))
    if not errors and not questions:
        errors.append(DatasetValidationError(message="Test set contains no questions."))
    if errors:
        raise UnprocessableError([e.model_dump() for e in errors])
    return questions


def _read_rows(filename: str, content: bytes) -> list[Any]:
    extension = Path(filename).suffix.lower()
    if extension not in TESTSET_EXTENSIONS:
        raise _single_error(f"Test set must be a .json or .csv file, got '{filename}'.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise _single_error("Test set must be UTF-8 encoded.") from None

    if extension == ".csv":
        # DictReader fills short rows with None; dropping them reports the field as missing.
        rows = csv.DictReader(io.StringIO(text))
        return [{k: v for k, v in row.items() if k is not None and v is not None} for row in rows]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise _single_error(f"Invalid JSON: {e.msg} (line {e.lineno}).") from None
    if not isinstance(data, list):
        raise _single_error("Test set JSON must be a list of objects.")
    return data


def _validate_row(row_number: int, row: Any) -> list[DatasetValidationError]:
    if not isinstance(row, dict):
        return [DatasetValidationError(row=row_number, message="Row must be an object.")]
    try:
        TestQuestion.model_validate(row)
    except ValidationError as e:
        return [
            DatasetValidationError(
                row=row_number,
                field=str(err["loc"][0]) if err["loc"] else None,
                message="Missing field." if err["type"] == "missing" else err["msg"],
            )
            for err in e.errors()
        ]
    return [
        DatasetValidationError(row=row_number, field=field, message="Field must not be empty.")
        for field in TestQuestion.model_fields
        if not str(row[field]).strip()
    ]


def _validate_documents(filenames: list[str]) -> list[str]:
    errors: list[DatasetValidationError] = []
    if not filenames:
        errors.append(
            DatasetValidationError(field="documents", message="Upload at least one document.")
        )
    names = [Path(f).name for f in filenames]
    for name in names:
        if Path(name).suffix.lower() not in DOCUMENT_EXTENSIONS:
            errors.append(
                DatasetValidationError(
                    field="documents", message=f"Unsupported file type: '{name}'."
                )
            )
    for name in sorted({n for n in names if names.count(n) > 1}):
        errors.append(
            DatasetValidationError(field="documents", message=f"Duplicate file name: '{name}'.")
        )
    if errors:
        raise UnprocessableError([e.model_dump() for e in errors])
    return names


def _single_error(message: str) -> UnprocessableError:
    return UnprocessableError(
        [DatasetValidationError(field="testset", message=message).model_dump()]
    )


dataset_service = DatasetService(CrudRepository(Dataset))

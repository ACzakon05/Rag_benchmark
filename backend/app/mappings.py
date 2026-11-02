from typing import Annotated
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column

from app.config import settings

PrimaryKey = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]

str_32 = Annotated[str, mapped_column(String(32))]
str_255 = Annotated[str, mapped_column(String(255))]

Embedding = Annotated[list[float], mapped_column(Vector(settings.embedding_dim))]


def _fk(target: str) -> object:
    return mapped_column(ForeignKey(f"{target}.id", ondelete="CASCADE"), index=True)


FKDataset = Annotated[UUID, _fk("dataset")]
FKDocument = Annotated[UUID, _fk("document")]
FKTestQuestion = Annotated[UUID, _fk("test_question")]
FKExperiment = Annotated[UUID, _fk("experiment")]
FKRagConfig = Annotated[UUID, _fk("rag_config")]
FKQuestionResult = Annotated[UUID, _fk("question_result")]
FKChunk = Annotated[UUID, _fk("chunk")]

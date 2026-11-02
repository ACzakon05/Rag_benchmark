from typing import Annotated
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import MappedColumn, mapped_column

from app.config import settings

PrimaryKey = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]

str_32 = Annotated[str, mapped_column(String(32))]
str_255 = Annotated[str, mapped_column(String(255))]

Embedding = Annotated[list[float], mapped_column(Vector(settings.embedding_dim))]


def _fk(target: str, ondelete: str = "CASCADE", deferred: bool = False) -> MappedColumn:
    options = {"deferrable": True, "initially": "DEFERRED"} if deferred else {}
    return mapped_column(ForeignKey(f"{target}.id", ondelete=ondelete, **options))


FKDataset = Annotated[UUID, _fk("dataset")]
FKDocument = Annotated[UUID, _fk("document")]
FKQuestion = Annotated[UUID, _fk("question")]
FKExperiment = Annotated[UUID, _fk("experiment")]
FKRagConfig = Annotated[UUID, _fk("rag_config")]
FKCollection = Annotated[UUID, _fk("collection")]
FKQuestionResult = Annotated[UUID, _fk("question_result")]

# Collections and chunks are shared between experiments, so references to them must not
# cascade: deleting one while results still point at it should fail, not wipe the results.
# Deferred to commit, because a dataset delete cascades to both sides and Postgres would
# otherwise check the reference before the cascade has removed the referencing rows.
FKCollectionRef = Annotated[UUID, _fk("collection", ondelete="NO ACTION", deferred=True)]
FKChunkRef = Annotated[UUID, _fk("chunk", ondelete="NO ACTION", deferred=True)]

from typing import Any

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import BaseDbModel
from app.mappings import Embedding, FKDocument, FKRagConfig, PrimaryKey


class Chunk(BaseDbModel):
    # No ANN index: at MVP scale an exact scan filtered by collection is fast enough,
    # and an HNSW index combined with a WHERE filter can return fewer than k rows.
    __table_args__ = (Index("ix_chunk_collection_position", "collection_id", "position"),)

    id: Mapped[PrimaryKey]
    collection_id: Mapped[FKRagConfig]
    document_id: Mapped[FKDocument]
    position: Mapped[int]
    text: Mapped[str]
    meta: Mapped[dict[str, Any]] = mapped_column(default=dict)
    embedding: Mapped[Embedding]

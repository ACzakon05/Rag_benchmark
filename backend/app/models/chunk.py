from typing import Any

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import BaseDbModel
from app.mappings import Embedding, FKCollection, FKDataset, FKDocument, PrimaryKey, str_255
from app.schemas.config import ChunkingStrategy


class Collection(BaseDbModel):
    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "chunking",
            "chunk_size_tokens",
            "chunk_overlap_tokens",
            "embedding_model",
            name="collection_build_settings_key",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[PrimaryKey]
    dataset_id: Mapped[FKDataset]
    chunking: Mapped[ChunkingStrategy]
    chunk_size_tokens: Mapped[int | None]
    chunk_overlap_tokens: Mapped[int | None]
    embedding_model: Mapped[str_255]


class Chunk(BaseDbModel):
    # No ANN index: at MVP scale an exact scan filtered by collection is fast enough,
    # and an HNSW index combined with a WHERE filter can return fewer than k rows.
    __table_args__ = (Index("ix_chunk_collection_position", "collection_id", "position"),)

    id: Mapped[PrimaryKey]
    collection_id: Mapped[FKCollection]
    document_id: Mapped[FKDocument]
    position: Mapped[int]
    text: Mapped[str]
    meta: Mapped[dict[str, Any]] = mapped_column(default=dict)
    embedding: Mapped[Embedding]

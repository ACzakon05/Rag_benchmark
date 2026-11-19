"""Wyszukiwanie wektorowe (dense) w pgvector."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chunk
from app.retrieval.common import to_document_chunk
from app.retrieval.embedding import embed_query
from app.schemas.chunk import DocumentChunk


def dense_search(
    db: Session, collection_id: UUID, query: str, limit: int
) -> list[tuple[DocumentChunk, float]]:
    """Zwraca (chunk, podobieństwo kosinusowe) dla `limit` najlepszych chunków kolekcji."""
    distance = Chunk.embedding.cosine_distance(embed_query(query))
    stmt = (
        select(Chunk, distance.label("distance"))
        .where(Chunk.collection_id == collection_id)
        .order_by(distance)
        .limit(limit)
    )
    return [(to_document_chunk(row), 1 - dist) for row, dist in db.execute(stmt).all()]

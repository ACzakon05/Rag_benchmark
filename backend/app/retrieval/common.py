from __future__ import annotations

from app.models import Chunk
from app.schemas.chunk import DocumentChunk


def to_document_chunk(row: Chunk) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=str(row.id),
        document_id=str(row.document_id),
        text=row.text,
        position=row.position,
        metadata=row.meta,
    )

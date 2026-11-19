"""Konwersja wiersza bazy na schemat DocumentChunk."""

from __future__ import annotations

from uuid import uuid4

from app.config import settings
from app.models import Chunk
from app.retrieval.common import to_document_chunk


def test_maps_all_fields() -> None:
    row = Chunk(
        id=uuid4(),
        collection_id=uuid4(),
        document_id=uuid4(),
        position=7,
        text="treść",
        meta={"source": "a.md"},
        embedding=[0.0] * settings.embedding_dim,
    )

    chunk = to_document_chunk(row)

    assert chunk.chunk_id == str(row.id)
    assert chunk.document_id == str(row.document_id)
    assert chunk.text == "treść"
    assert chunk.position == 7
    assert chunk.metadata == {"source": "a.md"}

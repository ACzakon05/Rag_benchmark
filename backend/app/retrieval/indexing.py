from __future__ import annotations

from itertools import batched
from uuid import UUID

from app.database import SessionLocal
from app.models import Chunk
from app.retrieval.embedding import embed_documents
from app.schemas.chunk import DocumentChunk

EMBED_BATCH_SIZE = 32  # ile tekstów wysyłamy do Ollamy w jednym żądaniu


def index_chunks(collection_id: str, chunks: list[DocumentChunk]) -> None:
    """Embedding (nomic-embed-text) + zapis chunków i wektorów do tabeli `chunk`.

    BM25 nie wymaga zapisu: budowany jest w pamięci z chunków kolekcji (ADR-0001).
    Wszystko albo nic: przy błędzie w połowie nic nie zostaje w bazie.
    """
    if not chunks:
        return
    cid = UUID(collection_id)
    with SessionLocal() as db:
        for batch in batched(chunks, EMBED_BATCH_SIZE, strict=False):
            vectors = embed_documents([c.text for c in batch])
            db.add_all(
                Chunk(
                    id=UUID(c.chunk_id),
                    collection_id=cid,
                    document_id=UUID(c.document_id),
                    position=c.position,
                    text=c.text,
                    meta=c.metadata,
                    embedding=vector,
                )
                for c, vector in zip(batch, vectors, strict=True)
            )
        db.commit()

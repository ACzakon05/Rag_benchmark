"""Wyszukiwanie leksykalne BM25, budowane w pamięci z chunków kolekcji (ADR-0001)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session, defer

from app.models import Chunk
from app.retrieval.common import to_document_chunk
from app.schemas.chunk import DocumentChunk

_TOKEN = re.compile(r"\w+")


@dataclass(frozen=True)
class _Bm25Index:
    bm25: BM25Okapi
    chunks: list[DocumentChunk]


# Cache per kolekcja: BM25 nie jest budowany od nowa przy każdym zapytaniu.
_cache: dict[UUID, _Bm25Index] = {}


def bm25_search(
    db: Session, collection_id: UUID, query: str, limit: int
) -> list[tuple[DocumentChunk, float]]:
    """Zwraca (chunk, wynik BM25), od najlepszego; pomija chunki bez wspólnych słów."""
    index = _get_index(db, collection_id)
    if index is None:
        return []
    scores = index.bm25.get_scores(_tokenize(query))
    ranked = sorted(zip(index.chunks, scores, strict=True), key=lambda p: p[1], reverse=True)
    return [(chunk, float(score)) for chunk, score in ranked[:limit] if score > 0]


def clear_cache() -> None:
    _cache.clear()


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _get_index(db: Session, collection_id: UUID) -> _Bm25Index | None:
    if collection_id in _cache:
        return _cache[collection_id]
    stmt = (
        select(Chunk)
        .where(Chunk.collection_id == collection_id)
        .options(defer(Chunk.embedding))
        .order_by(Chunk.position)
    )
    chunks = [to_document_chunk(row) for row in db.scalars(stmt)]
    if not chunks:
        return None

    index = _Bm25Index(BM25Okapi([_tokenize(c.text) for c in chunks]), chunks)
    _cache[collection_id] = index
    return index

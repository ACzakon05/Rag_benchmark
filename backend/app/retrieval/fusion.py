"""Łączenie rankingów metodą Reciprocal Rank Fusion."""

from __future__ import annotations

from app.schemas.chunk import DocumentChunk

RRF_K = 60  # standardowa stała RRF


def rrf(rankings: list[list[DocumentChunk]]) -> list[tuple[DocumentChunk, float]]:
    """Łączy rankingi po samych pozycjach: wynik = Σ 1 / (RRF_K + pozycja)."""
    scores: dict[str, float] = {}
    by_id: dict[str, DocumentChunk] = {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking, start=1):
            by_id[chunk.chunk_id] = chunk
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1 / (RRF_K + rank)
    ordered = sorted(scores, key=scores.__getitem__, reverse=True)
    return [(by_id[chunk_id], scores[chunk_id]) for chunk_id in ordered]

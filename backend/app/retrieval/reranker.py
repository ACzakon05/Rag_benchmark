"""Reranker (Osoba 4) — model BAAI/bge-reranker-* przez Sentence-Transformers.

Ladowany lokalnie w procesie Pythona. Dla PL mozna podmienic wage na
BAAI/bge-reranker-v2-m3 (kod integracji pozostaje identyczny).
"""

from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.schemas.chunk import ScoredChunk

MAX_PAIR_TOKENS = 512


@lru_cache
def get_model():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(settings.reranker_model, max_length=MAX_PAIR_TOKENS)


def rerank(query: str, chunks: list[ScoredChunk], top_k: int) -> list[ScoredChunk]:
    """Przeszeregowanie pobranych fragmentow wg trafnosci do zapytania."""

    if not chunks:
        return []
    model = get_model()
    scores = model.predict([(query, c.chunk.text) for c in chunks])
    ranked = sorted(zip(chunks, scores, strict=True), key=lambda p: p[1], reverse=True)
    return [
        ScoredChunk(chunk=c.chunk, score=float(score), rank=rank)
        for rank, (c, score) in enumerate(ranked[:top_k], start=1)
    ]

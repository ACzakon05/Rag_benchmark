"""Modul Indeksowania i Wyszukiwania (Osoba 4).

Odpowiedzialnosc: tworzenie indeksow dla konfiguracji, wyszukiwanie fragmentow
oraz ich reranking.

Kontrakt dostarczany reszcie zespolu:
    index_chunks(collection_id, chunks) -> None
    search(collection_id, query, config) -> list[ScoredChunk]

Zaleznosci: przyjmuje liste DocumentChunk. Moze byc rozwijany niezaleznie
na sztucznych danych wejsciowych.
"""

from __future__ import annotations

from uuid import UUID

from app.database import SessionLocal
from app.retrieval.bm25 import bm25_search
from app.retrieval.dense import dense_search
from app.retrieval.embedding import embed_query
from app.retrieval.fusion import rrf
from app.retrieval.indexing import index_chunks
from app.retrieval.reranker import get_model, rerank
from app.schemas.chunk import ScoredChunk
from app.schemas.config import RetrievalMethod
from app.schemas.experiment import RagConfig

__all__ = ["index_chunks", "search", "warm_up"]

CANDIDATE_MULTIPLIER = 4  # ile razy więcej kandydatów niż top_k pobieramy dla hybrid / rerank


def search(collection_id: str, query: str, config: RagConfig) -> list[ScoredChunk]:
    """Wyszukiwanie: dense lub hybrydowe (dense + BM25 laczone przez RRF),
    opcjonalny reranking (bge-reranker)."""
    cid = UUID(collection_id)
    hybrid = config.retrieval == RetrievalMethod.HYBRID
    wide = hybrid or config.reranking_enabled
    pool = config.top_k * CANDIDATE_MULTIPLIER if wide else config.top_k
    with SessionLocal() as db:
        candidates = dense_search(db, cid, query, pool)
        if hybrid:
            lexical = bm25_search(db, cid, query, pool)
            fused = rrf([[c for c, _ in candidates], [c for c, _ in lexical]])
            candidates = fused[:pool]
    scored = [
        ScoredChunk(chunk=chunk, score=score, rank=rank)
        for rank, (chunk, score) in enumerate(candidates, start=1)
    ]
    if config.reranking_enabled:
        return rerank(query, scored, config.top_k)
    return scored[: config.top_k]


def warm_up(config: RagConfig) -> None:
    """Ładuje modele z góry, żeby pierwsze pytanie nie zawyżało czasów w benchmarku."""
    embed_query("warm up")
    if config.reranking_enabled:
        get_model()

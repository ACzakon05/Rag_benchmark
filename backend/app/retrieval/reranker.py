"""Reranker (Osoba 4) — model BAAI/bge-reranker-* przez Sentence-Transformers.

Ladowany lokalnie w procesie Pythona. Dla PL mozna podmienic wage na
BAAI/bge-reranker-v2-m3 (kod integracji pozostaje identyczny).
Szkielet — bez implementacji.
"""

from __future__ import annotations

from app.schemas.chunk import ScoredChunk


def rerank(query: str, chunks: list[ScoredChunk], top_k: int) -> list[ScoredChunk]:
    """Przeszeregowanie pobranych fragmentow wg trafnosci do zapytania."""
    raise NotImplementedError

"""Modul Indeksowania i Wyszukiwania (Osoba 4).

Odpowiedzialnosc: tworzenie indeksow dla konfiguracji, wyszukiwanie fragmentow
oraz ich reranking.

Kontrakt dostarczany reszcie zespolu:
    index_chunks(collection_id, chunks) -> None
    search(collection_id, query, config) -> list[ScoredChunk]

Zaleznosci: przyjmuje liste DocumentChunk. Moze byc rozwijany niezaleznie
na sztucznych danych wejsciowych.
Szkielet — bez implementacji.
"""

from __future__ import annotations

from app.schemas.chunk import DocumentChunk, ScoredChunk
from app.schemas.experiment import RagConfig


def index_chunks(collection_id: str, chunks: list[DocumentChunk]) -> None:
    """Embedding (nomic-embed-text) + zapis do bazy wektorowej oraz indeks BM25.

    Osobna kolekcja per konfiguracja, by po benchmarku byla gotowa dla Playground.
    """
    raise NotImplementedError


def search(collection_id: str, query: str, config: RagConfig) -> list[ScoredChunk]:
    """Wyszukiwanie: dense lub hybrydowe (dense + BM25 laczone przez RRF),
    opcjonalny reranking (bge-reranker)."""
    raise NotImplementedError

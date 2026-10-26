"""Kontrakty danych dla fragmentow dokumentow (interfejs ingestion -> retrieval).

Szkielet — do zatwierdzenia na Etapie 1.
"""

from __future__ import annotations

from pydantic import BaseModel


class DocumentChunk(BaseModel):
    """Ustandaryzowany fragment tekstu zwracany przez modul ingestion."""

    chunk_id: str
    document_id: str
    text: str
    position: int                    # kolejnosc w dokumencie
    metadata: dict = {}              # np. naglowek, numer strony


class ScoredChunk(BaseModel):
    """Fragment zwrocony przez wyszukiwanie wraz z ocena i rankingiem."""

    chunk: DocumentChunk
    score: float
    rank: int
    contains_expected_snippet: bool | None = None  # wypelniane przez evaluation

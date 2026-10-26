"""Kontrakty danych dla modulu Playground (US-5).

Szkielet — do zatwierdzenia na Etapie 1.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.chunk import ScoredChunk


class PlaygroundQuery(BaseModel):
    """Zapytanie na zywo do wybranej konfiguracji (istniejacy juz indeks)."""

    experiment_id: str
    config_label: str
    question: str


class PlaygroundResponse(BaseModel):
    """Odpowiedz na zywo wraz ze zrodlami i pomiarem czasu."""

    answer: str
    retrieved_chunks: list[ScoredChunk]
    retrieval_time_ms: float
    generation_time_ms: float

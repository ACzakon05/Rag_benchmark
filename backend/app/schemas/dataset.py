"""Kontrakty danych dla zbioru dokumentow i zestawu testowego (US-1).

Szkielet — pola ustalone na podstawie specyfikacji; do zatwierdzenia na Etapie 1.
"""

from __future__ import annotations

from pydantic import BaseModel


class TestQuestion(BaseModel):
    """Pojedynczy wiersz zbioru testowego (JSON/CSV)."""

    question: str
    ground_truth_answer: str
    expected_context_snippet: str  # krotki, jednoznaczny cytat ze zrodla
    # is_unanswerable: bool = False  # Should-have: pytania bez odpowiedzi


class DatasetSummary(BaseModel):
    """Podsumowanie wgranego zbioru prezentowane w UI."""

    dataset_id: str
    document_count: int
    total_size_bytes: int
    question_count: int


class DatasetValidationError(BaseModel):
    """Czytelny komunikat walidacji pliku testowego."""

    row: int | None = None
    field: str | None = None
    message: str

"""Kontrakty danych dla definicji i stanu eksperymentu (US-2).

Szkielet — do zatwierdzenia na Etapie 1.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.schemas.config import ChunkingStrategy, RetrievalMethod


class RagConfig(BaseModel):
    """Pojedynczy wariant potoku RAG (np. Konfiguracja A/B/C/D)."""

    label: str                       # "A", "B", ...
    chunking: ChunkingStrategy
    chunk_size_tokens: int | None = None    # dla FIXED_TOKENS
    chunk_overlap_tokens: int | None = None
    retrieval: RetrievalMethod
    top_k: int                       # liczba pobieranych fragmentow
    reranking_enabled: bool


class ExperimentConfig(BaseModel):
    """Definicja calego eksperymentu — od 2 do 4 wariantow na jednym zbiorze."""

    dataset_id: str
    configs: list[RagConfig]         # walidacja: 2 <= len <= 4


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentProgress(BaseModel):
    """Postep zadania w tle prezentowany w UI (np. 'Konfiguracja 2/4, pytanie 6/15')."""

    experiment_id: str
    status: ExperimentStatus
    current_config: int
    total_configs: int
    current_question: int
    total_questions: int
    message: str | None = None

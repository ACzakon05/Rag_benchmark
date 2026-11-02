"""Kontrakty danych dla definicji i stanu eksperymentu (US-2).

Szkielet — do zatwierdzenia na Etapie 1.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.schemas.config import ChunkingStrategy, RetrievalMethod


class RagConfig(BaseModel):
    """Pojedynczy wariant potoku RAG (np. Konfiguracja A/B/C/D)."""

    label: str = Field(min_length=1, max_length=32)  # "A", "B", ...
    chunking: ChunkingStrategy
    chunk_size_tokens: int | None = Field(None, gt=0)  # dla FIXED_TOKENS
    chunk_overlap_tokens: int | None = Field(None, ge=0)
    retrieval: RetrievalMethod
    top_k: int = Field(gt=0, le=50)  # liczba pobieranych fragmentow
    reranking_enabled: bool

    @model_validator(mode="after")
    def _check_chunking(self) -> Self:
        if self.chunking == ChunkingStrategy.FIXED_TOKENS:
            if self.chunk_size_tokens is None or self.chunk_overlap_tokens is None:
                raise ValueError("fixed_tokens requires chunk_size_tokens and chunk_overlap_tokens")
            if self.chunk_overlap_tokens >= self.chunk_size_tokens:
                raise ValueError("chunk_overlap_tokens must be smaller than chunk_size_tokens")
        else:
            self.chunk_size_tokens = None
            self.chunk_overlap_tokens = None
        return self


class ExperimentConfig(BaseModel):
    """Definicja calego eksperymentu — od 2 do 4 wariantow na jednym zbiorze."""

    dataset_id: str
    configs: list[RagConfig] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def _check_unique_labels(self) -> Self:
        labels = [c.label for c in self.configs]
        if len(set(labels)) != len(labels):
            raise ValueError("config labels must be unique")
        return self


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


class ExperimentRead(BaseModel):
    """Eksperyment z konfiguracjami (lista eksperymentow, wybor konfiguracji w Playground)."""

    experiment_id: str
    dataset_id: str
    status: ExperimentStatus
    error: str | None
    generation_model: str
    judge_model: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    configs: list[RagConfig]

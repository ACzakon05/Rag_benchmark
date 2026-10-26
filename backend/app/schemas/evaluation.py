"""Kontrakty danych dla wynikow ewaluacji (US-3, US-4).

Szkielet — do zatwierdzenia na Etapie 1.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.chunk import ScoredChunk


class RetrievalMetrics(BaseModel):
    """Deterministyczne metryki jakosci wyszukiwania."""

    recall_at_k: float
    mrr: float


class JudgeMetrics(BaseModel):
    """Oceny LLM-as-a-Judge (jeden prompt zwraca obie oceny naraz)."""

    answer_correctness: float        # poprawnosc wzgledem wzorca
    faithfulness: float              # zgodnosc z kontekstem / brak halucynacji
    rationale: str | None = None     # krotkie uzasadnienie oceny


class SystemMetrics(BaseModel):
    """Metryki wydajnosciowe."""

    retrieval_time_ms: float
    total_time_ms: float
    tokens_used: int


class QuestionResult(BaseModel):
    """Wynik jednej konfiguracji dla jednego pytania (widok mikro)."""

    config_label: str
    question: str
    ground_truth_answer: str
    generated_answer: str
    retrieved_chunks: list[ScoredChunk]
    judge: JudgeMetrics
    system: SystemMetrics


class ConfigAggregateResult(BaseModel):
    """Usrednione metryki dla jednej konfiguracji (widok makro / tabela)."""

    config_label: str
    retrieval: RetrievalMetrics
    answer_correctness: float
    faithfulness: float
    avg_retrieval_time_ms: float
    avg_total_time_s: float
    total_tokens: int


class ExperimentResults(BaseModel):
    """Komplet wynikow eksperymentu zwracany do dashboardu."""

    experiment_id: str
    aggregates: list[ConfigAggregateResult]       # tabela zbiorcza
    per_question: list[QuestionResult]            # szczegoly

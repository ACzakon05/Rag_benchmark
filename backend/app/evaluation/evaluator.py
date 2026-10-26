"""Modul Ewaluacji (Osoba 5).

Odpowiedzialnosc: wyliczanie metryk jakosci wyszukiwania (deterministyczne)
oraz jakosci odpowiedzi (LLM-as-a-Judge).

Kontrakt dostarczany reszcie zespolu:
    evaluate(question, ground_truth, retrieved_chunks, answer) -> EvaluationMetrics

Zaleznosci: brak zaleznosci od baz danych czy chunkerow. Moze byc rozwijany
w 100% niezaleznie. Szkielet — bez implementacji.
"""

from __future__ import annotations

from app.schemas.chunk import ScoredChunk
from app.schemas.evaluation import JudgeMetrics, RetrievalMetrics


def snippet_hit(chunk_text: str, expected_snippet: str, threshold: float = 0.8) -> bool:
    """Czy chunk zawiera wzorcowy cytat (pokrycie >= threshold).

    Rozwiazuje ryzyko roz-nych chunk_id przy roznych strategiach chunkingu —
    trafnosc liczymy po tresci cytatu, nie po identyfikatorze.
    """
    raise NotImplementedError


def compute_retrieval_metrics(
    retrieved_chunks: list[ScoredChunk], expected_snippet: str, k: int
) -> RetrievalMetrics:
    """Recall@k oraz MRR na podstawie obecnosci wzorcowego cytatu."""
    raise NotImplementedError


def judge_answer(
    question: str, ground_truth: str, context: list[ScoredChunk], answer: str
) -> JudgeMetrics:
    """LLM-as-a-Judge (qwen3:8b). Jeden prompt zwraca poprawnosc + wiernosc.

    Wymuszony format JSON (format="json"), temperature=0, retry przy bledzie parsowania.
    """
    raise NotImplementedError

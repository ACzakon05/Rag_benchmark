"""Stand-in for the real pipeline until ingestion, retrieval and evaluation are implemented.

Writes made-up but plausible results through the same tables the real runner will use, so the
frontend can be built against real API responses. Remove once the orchestrator is real.
"""

import random
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import (
    Chunk,
    Collection,
    Document,
    Experiment,
    Question,
    QuestionResult,
    RagConfig,
    RetrievedChunk,
)
from app.schemas.config import ChunkingStrategy, RetrievalMethod
from app.schemas.experiment import ExperimentStatus

MAX_CHUNKS_PER_DOCUMENT = 200


def run_fake_experiment(experiment_id: UUID) -> None:
    with SessionLocal() as db:
        experiment = db.get(Experiment, experiment_id)
        if experiment is None:
            return
        try:
            _set_status(db, experiment, ExperimentStatus.INDEXING, started_at=datetime.now(UTC))
            for collection in {c.collection_id: c.collection for c in experiment.configs}.values():
                _index_collection(db, collection, experiment.dataset.documents)

            _set_status(db, experiment, ExperimentStatus.RUNNING)
            for rag_config in experiment.configs:
                chunks = _chunks_of(db, rag_config.collection_id)
                for question in experiment.dataset.questions:
                    _answer_question(db, rag_config, question, chunks)
                    time.sleep(settings.fake_runner_delay_s)

            _set_status(db, experiment, ExperimentStatus.COMPLETED, finished_at=datetime.now(UTC))
        except Exception as e:
            db.rollback()
            _set_status(
                db, experiment, ExperimentStatus.FAILED, error=str(e), finished_at=datetime.now(UTC)
            )
            raise


def fake_search(chunks: list[Chunk], query: str, k: int) -> list[tuple[Chunk, float]]:
    """Word-overlap ranking; good enough to show sensible sources in the Playground."""
    words = set(re.findall(r"\w+", query.lower()))
    scored = [
        (c, len(words & set(re.findall(r"\w+", c.text.lower()))) / (len(words) or 1))
        for c in chunks
    ]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)[:k]


def _set_status(
    db: Session, experiment: Experiment, status: ExperimentStatus, **fields: object
) -> None:
    experiment.status = status
    for name, value in fields.items():
        setattr(experiment, name, value)
    db.commit()


def _chunks_of(db: Session, collection_id: UUID) -> list[Chunk]:
    stmt = select(Chunk).where(Chunk.collection_id == collection_id).order_by(Chunk.position)
    return list(db.scalars(stmt).all())


def _index_collection(db: Session, collection: Collection, documents: list[Document]) -> None:
    if _chunks_of(db, collection.id):
        return
    position = 0
    for document in documents:
        for text in _split(_read_text(Path(document.path)), collection)[:MAX_CHUNKS_PER_DOCUMENT]:
            db.add(
                Chunk(
                    collection_id=collection.id,
                    document_id=document.id,
                    position=position,
                    text=text,
                    meta={"source": document.filename, "fake": True},
                    embedding=_random_unit_vector(),
                )
            )
            position += 1
    db.commit()


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    if path.suffix.lower() == ".pdf":
        try:
            return "\n\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        except Exception:
            return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _split(text: str, collection: Collection) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if collection.chunking == ChunkingStrategy.STRUCTURAL:
        return paragraphs
    max_chars = (collection.chunk_size_tokens or 256) * 4
    chunks, current = [], ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) > max_chars:
            chunks.append(current)
            current = ""
        current = f"{current}\n\n{paragraph}".strip()
    return [*chunks, current] if current else chunks


def _random_unit_vector() -> list[float]:
    vector = [random.gauss(0, 1) for _ in range(settings.embedding_dim)]
    norm = sum(x * x for x in vector) ** 0.5
    return [x / norm for x in vector]


def _answer_question(
    db: Session, rag_config: RagConfig, question: Question, chunks: list[Chunk]
) -> None:
    rng = random.Random(f"{rag_config.id}{question.id}")
    snippet = question.expected_context_snippet.lower()
    hits = [c for c in chunks if snippet in c.text.lower()]
    others = [c for c in chunks if c not in hits]

    hit_chance = (
        0.45
        + 0.15 * (rag_config.retrieval == RetrievalMethod.HYBRID)
        + 0.2 * rag_config.reranking_enabled
    )
    retrieved = rng.sample(others, min(rag_config.top_k, len(others)))
    if hits and rng.random() < hit_chance:
        retrieved.insert(rng.randrange(min(3, len(retrieved) + 1)), rng.choice(hits))
    retrieved = retrieved[: rag_config.top_k]

    first_hit = next((rank for rank, c in enumerate(retrieved, start=1) if c in hits), None)
    recall = 1.0 if first_hit else 0.0
    retrieval_ms = rng.uniform(15, 60) + (
        rng.uniform(120, 250) if rag_config.reranking_enabled else 0
    )
    generation_ms = rng.uniform(800, 2500)

    result = QuestionResult(
        rag_config_id=rag_config.id,
        question_id=question.id,
        generated_answer=f"[fake] {retrieved[0].text[:200]}"
        if retrieved
        else "[fake] No context found.",
        recall_at_k=recall,
        mrr=1 / first_hit if first_hit else 0.0,
        answer_correctness=_clamp(rng.gauss(0.45 + 0.4 * recall, 0.12)),
        faithfulness=_clamp(rng.gauss(0.6 + 0.3 * recall, 0.1)),
        judge_rationale="[fake] Generated by the fake runner.",
        retrieval_time_ms=retrieval_ms,
        generation_time_ms=generation_ms,
        total_time_ms=retrieval_ms + generation_ms + rng.uniform(5, 30),
        prompt_tokens=60 + sum(len(c.text) // 4 for c in retrieved),
        completion_tokens=rng.randint(30, 150),
    )
    result.retrieved = [
        RetrievedChunk(
            chunk_id=chunk.id,
            rank=rank,
            score=round(1 - rank * rng.uniform(0.03, 0.08), 4),
            contains_expected_snippet=chunk in hits,
        )
        for rank, chunk in enumerate(retrieved, start=1)
    ]
    db.add(result)
    db.commit()


def _clamp(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 3)

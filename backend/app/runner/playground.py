"""Obsluga pojedynczych zapytan na zywo z modulu Playground (Osoba 1).

Zapytanie trafia prosto do istniejacej juz kolekcji wybranej konfiguracji
(bez ponownego indeksowania).
"""

import random
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Chunk, RagConfig
from app.runner.fake_runner import fake_search
from app.schemas.chunk import ScoredChunk
from app.schemas.playground import PlaygroundResponse
from app.services.experiment_service import chunk_to_schema
from app.utils.exceptions import InvalidStateError


def answer_query(db: Session, rag_config: RagConfig, question: str) -> PlaygroundResponse:
    """search -> (reranking) -> generate dla gotowego indeksu konfiguracji."""
    chunks = list(db.scalars(select(Chunk).where(Chunk.collection_id == rag_config.collection_id)))
    if not chunks:
        raise InvalidStateError(
            "This configuration has no indexed chunks yet. Run the experiment first."
        )
    if not settings.fake_runner:
        raise NotImplementedError

    started = time.perf_counter()
    found = fake_search(chunks, question, rag_config.top_k)
    retrieval_ms = (time.perf_counter() - started) * 1000
    top_text = found[0][0].text[:200] if found else ""
    return PlaygroundResponse(
        answer=f"[fake] Based on the sources: {top_text}",
        retrieved_chunks=[
            ScoredChunk(chunk=chunk_to_schema(chunk), score=round(score, 4), rank=rank)
            for rank, (chunk, score) in enumerate(found, start=1)
        ],
        retrieval_time_ms=retrieval_ms,
        generation_time_ms=random.uniform(800, 2500),
    )

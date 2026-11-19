"""Drobne funkcje pomocnicze wspólne dla testów retrieval."""

from __future__ import annotations

from uuid import uuid4

from app.schemas.chunk import DocumentChunk, ScoredChunk
from app.schemas.config import ChunkingStrategy, RetrievalMethod
from app.schemas.experiment import RagConfig

CORPUS = [
    "Maksymalny limit X wynosi 100 jednostek na dobę.",
    "Reklamacje należy składać w ciągu 14 dni od daty zakupu.",
    "Serwer obsługuje do 500 jednoczesnych połączeń.",
    "Hasło powinno mieć co najmniej 12 znaków i jedną cyfrę.",
    "Kopie zapasowe wykonywane są codziennie o godzinie 2:00.",
    "Dostęp do systemu wymaga uwierzytelnienia dwuskładnikowego.",
]
LIMIT_TEXT = CORPUS[0]
LIMIT_QUERY = "Jaki jest limit X?"


def make_chunk(chunk_id: str | None = None, text: str = "", position: int = 0) -> DocumentChunk:
    chunk_id = chunk_id or str(uuid4())
    return DocumentChunk(
        chunk_id=chunk_id, document_id=str(uuid4()), text=text or chunk_id, position=position
    )


def make_chunks(document_id: str, texts: list[str]) -> list[DocumentChunk]:
    return [
        DocumentChunk(chunk_id=str(uuid4()), document_id=document_id, text=text, position=i)
        for i, text in enumerate(texts)
    ]


def make_scored(chunk_id: str, rank: int = 1, score: float = 0.5) -> ScoredChunk:
    return ScoredChunk(chunk=make_chunk(chunk_id), score=score, rank=rank)


def make_config(
    retrieval: RetrievalMethod = RetrievalMethod.DENSE,
    top_k: int = 3,
    reranking: bool = False,
) -> RagConfig:
    return RagConfig(
        label="A",
        chunking=ChunkingStrategy.STRUCTURAL,
        retrieval=retrieval,
        top_k=top_k,
        reranking_enabled=reranking,
    )

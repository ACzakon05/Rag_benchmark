"""Fixture'y testów retrieval: sztuczne embeddingi, baza z testcontainers, podmiana SessionLocal.

Testy jednostkowe nie potrzebują ani Ollamy, ani bazy. Testy integracyjne używają
fixture `db`, która uruchamia pgvector w Dockerze (a gdy Dockera brak, pomija test).
"""

from __future__ import annotations

import math
import os
import re
import zlib
from collections.abc import Callable, Iterator
from uuid import UUID

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (rejestruje tabele w metadanych)
from app.config import settings
from app.database import BaseDbModel
from app.models import Collection, Dataset, Document
from app.retrieval import bm25
from app.schemas.config import ChunkingStrategy

PGVECTOR_IMAGE = "pgvector/pgvector:pg17"
PREFIXES = ("search_document: ", "search_query: ")


def _vectorize(text_: str) -> list[float]:
    """Deterministyczny „embedding”: haszowany worek słów, znormalizowany.

    Teksty ze wspólnymi słowami mają duże podobieństwo kosinusowe, więc wyszukiwanie wektorowe
    daje sensowne wyniki bez prawdziwego modelu.
    """
    for prefix in PREFIXES:
        text_ = text_.removeprefix(prefix)
    vector = [0.0] * settings.embedding_dim
    for token in re.findall(r"\w+", text_.lower()):
        vector[zlib.crc32(token.encode()) % settings.embedding_dim] += 1.0
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [_vectorize(t) for t in texts]


@pytest.fixture
def embedding_client(monkeypatch: pytest.MonkeyPatch) -> FakeEmbeddingClient:
    client = FakeEmbeddingClient()
    monkeypatch.setattr("app.retrieval.embedding.get_embedding_client", lambda: client)
    return client


@pytest.fixture(autouse=True)
def _clear_bm25_cache() -> Iterator[None]:
    bm25.clear_cache()
    yield
    bm25.clear_cache()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")
    try:
        from testcontainers.community.postgres import PostgresContainer

        container = PostgresContainer(PGVECTOR_IMAGE, driver="psycopg")
        container.start()
    except Exception as e:
        pytest.skip(f"Docker / testcontainers niedostępne: {e}")
    try:
        engine = create_engine(container.get_connection_url())
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        BaseDbModel.metadata.create_all(engine)
        yield engine
        engine.dispose()
    finally:
        container.stop()


@pytest.fixture
def db(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> sessionmaker[Session]:
    """Czysta baza na każdy test + podmiana SessionLocal w modułach retrieval."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE dataset RESTART IDENTITY CASCADE"))
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    monkeypatch.setattr("app.retrieval.indexing.SessionLocal", factory)
    monkeypatch.setattr("app.retrieval.retriever.SessionLocal", factory)
    return factory


@pytest.fixture
def make_collection(db: sessionmaker[Session]) -> Callable[[], tuple[UUID, UUID]]:
    """Tworzy dataset + dokument + pustą kolekcję, zwraca (collection_id, document_id)."""

    def _make() -> tuple[UUID, UUID]:
        with db() as session:
            dataset = Dataset(name="test")
            document = Document(filename="a.txt", path="/dev/null", size_bytes=0)
            dataset.documents.append(document)
            session.add(dataset)
            session.flush()
            collection = Collection(
                dataset_id=dataset.id,
                chunking=ChunkingStrategy.STRUCTURAL,
                chunk_size_tokens=None,
                chunk_overlap_tokens=None,
                embedding_model="test/fake",
            )
            session.add(collection)
            session.commit()
            return collection.id, document.id

    return _make

"""Integracja z prawdziwym Postgresem + pgvector (testcontainers) i sztucznymi embeddingami.

Bez Dockera testy są pomijane. Prawdziwy model embeddingowy nie jest potrzebny.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Chunk
from app.retrieval import indexing, reranker
from app.retrieval.retriever import index_chunks, search
from app.schemas.config import RetrievalMethod
from tests.retrieval.conftest import FakeEmbeddingClient
from tests.retrieval.helpers import CORPUS, LIMIT_QUERY, LIMIT_TEXT, make_chunks, make_config

MakeCollection = Callable[[], tuple[UUID, UUID]]


def _count(db: sessionmaker[Session], collection_id: UUID) -> int:
    with db() as session:
        stmt = select(func.count()).select_from(Chunk).where(Chunk.collection_id == collection_id)
        return session.scalar(stmt) or 0


@pytest.fixture
def indexed(
    db: sessionmaker[Session],
    make_collection: MakeCollection,
    embedding_client: FakeEmbeddingClient,
) -> UUID:
    collection_id, document_id = make_collection()
    index_chunks(str(collection_id), make_chunks(str(document_id), CORPUS))
    return collection_id


def test_index_chunks_stores_rows_with_vectors(
    db: sessionmaker[Session],
    make_collection: MakeCollection,
    embedding_client: FakeEmbeddingClient,
) -> None:
    collection_id, document_id = make_collection()
    chunks = make_chunks(str(document_id), CORPUS)
    for chunk in chunks:
        chunk.metadata = {"source": "a.txt"}

    index_chunks(str(collection_id), chunks)

    with db() as session:
        rows = session.scalars(
            select(Chunk).where(Chunk.collection_id == collection_id).order_by(Chunk.position)
        ).all()
    assert [r.text for r in rows] == CORPUS
    assert [str(r.id) for r in rows] == [c.chunk_id for c in chunks]
    assert all(r.document_id == document_id for r in rows)
    assert all(r.meta == {"source": "a.txt"} for r in rows)
    assert all(len(r.embedding) == settings.embedding_dim for r in rows)


def test_index_chunks_with_empty_list_does_nothing(
    db: sessionmaker[Session],
    make_collection: MakeCollection,
    embedding_client: FakeEmbeddingClient,
) -> None:
    collection_id, _ = make_collection()

    index_chunks(str(collection_id), [])

    assert _count(db, collection_id) == 0
    assert embedding_client.calls == []


def test_index_chunks_embeds_in_batches(
    db: sessionmaker[Session],
    make_collection: MakeCollection,
    embedding_client: FakeEmbeddingClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(indexing, "EMBED_BATCH_SIZE", 2)
    collection_id, document_id = make_collection()

    index_chunks(str(collection_id), make_chunks(str(document_id), CORPUS[:5]))

    assert [len(call) for call in embedding_client.calls] == [2, 2, 1]
    assert _count(db, collection_id) == 5


def test_index_chunks_is_all_or_nothing(
    db: sessionmaker[Session],
    make_collection: MakeCollection,
    embedding_client: FakeEmbeddingClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(indexing, "EMBED_BATCH_SIZE", 2)
    collection_id, document_id = make_collection()
    original = embedding_client.embed

    def flaky(texts: list[str]) -> list[list[float]]:
        if len(embedding_client.calls) == 1:  # druga paczka
            raise RuntimeError("Ollama padła")
        return original(texts)

    monkeypatch.setattr(embedding_client, "embed", flaky)

    with pytest.raises(RuntimeError, match="Ollama padła"):
        index_chunks(str(collection_id), make_chunks(str(document_id), CORPUS))

    assert _count(db, collection_id) == 0


def test_dense_search_finds_the_relevant_chunk(indexed: UUID) -> None:
    results = search(str(indexed), LIMIT_QUERY, make_config(RetrievalMethod.DENSE, top_k=3))

    assert len(results) == 3
    assert results[0].chunk.text == LIMIT_TEXT
    assert [r.rank for r in results] == [1, 2, 3]
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert 0.0 < scores[0] <= 1.0001


def test_dense_search_respects_top_k(indexed: UUID) -> None:
    assert len(search(str(indexed), LIMIT_QUERY, make_config(top_k=1))) == 1
    assert len(search(str(indexed), LIMIT_QUERY, make_config(top_k=50))) == len(CORPUS)


def test_hybrid_search_finds_the_relevant_chunk(indexed: UUID) -> None:
    results = search(str(indexed), LIMIT_QUERY, make_config(RetrievalMethod.HYBRID, top_k=3))

    assert results[0].chunk.text == LIMIT_TEXT
    assert len(results) == 3


def test_hybrid_returns_chunk_with_exact_keyword_even_when_vectors_disagree(
    indexed: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    # zapytanie z rzadkim słowem "uwierzytelnienia": BM25 podbija właściwy chunk
    results = search(str(indexed), "uwierzytelnienia", make_config(RetrievalMethod.HYBRID, top_k=2))

    assert results[0].chunk.text == "Dostęp do systemu wymaga uwierzytelnienia dwuskładnikowego."


def test_search_is_limited_to_the_given_collection(
    db: sessionmaker[Session],
    make_collection: MakeCollection,
    embedding_client: FakeEmbeddingClient,
) -> None:
    col_a, doc_a = make_collection()
    col_b, doc_b = make_collection()
    index_chunks(str(col_a), make_chunks(str(doc_a), ["limit X wynosi 100"]))
    index_chunks(str(col_b), make_chunks(str(doc_b), ["limit Y wynosi 200", "limit Z wynosi 300"]))

    for method in (RetrievalMethod.DENSE, RetrievalMethod.HYBRID):
        results = search(str(col_a), LIMIT_QUERY, make_config(method, top_k=10))
        assert [r.chunk.text for r in results] == ["limit X wynosi 100"]


def test_search_on_empty_collection_returns_empty_list(
    db: sessionmaker[Session],
    make_collection: MakeCollection,
    embedding_client: FakeEmbeddingClient,
) -> None:
    collection_id, _ = make_collection()

    for method in (RetrievalMethod.DENSE, RetrievalMethod.HYBRID):
        assert search(str(collection_id), LIMIT_QUERY, make_config(method)) == []


def test_returned_chunks_keep_ids_and_metadata(indexed: UUID) -> None:
    result = search(str(indexed), LIMIT_QUERY, make_config(top_k=1))[0]

    UUID(result.chunk.chunk_id)
    UUID(result.chunk.document_id)
    assert result.chunk.position == 0
    assert result.contains_expected_snippet is None


def test_search_with_rerank_uses_model_order(
    indexed: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    class PreferShort:
        def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
            return [-float(len(text)) for _, text in pairs]  # krótszy tekst = lepszy

    monkeypatch.setattr(reranker, "get_model", lambda: PreferShort())

    results = search(str(indexed), LIMIT_QUERY, make_config(top_k=2, reranking=True))

    shortest = sorted(CORPUS, key=len)[:2]
    assert [r.chunk.text for r in results] == shortest

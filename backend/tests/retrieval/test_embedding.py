"""Embeddingi: prefiksy nomic i walidacja wymiaru."""

from __future__ import annotations

import pytest

from app.config import settings
from app.retrieval.embedding import embed_documents, embed_query


class SpyClient:
    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or settings.embedding_dim
        self.received: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.received.extend(texts)
        return [[0.1] * self.dim for _ in texts]


@pytest.fixture
def spy(monkeypatch: pytest.MonkeyPatch) -> SpyClient:
    client = SpyClient()
    monkeypatch.setattr("app.retrieval.embedding.get_embedding_client", lambda: client)
    return client


def test_nomic_documents_get_document_prefix(spy: SpyClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "embedding_model", "ollama/nomic-embed-text")

    embed_documents(["a", "b"])

    assert spy.received == ["search_document: a", "search_document: b"]


def test_nomic_query_gets_query_prefix(spy: SpyClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "embedding_model", "ollama/nomic-embed-text")

    embed_query("pytanie")

    assert spy.received == ["search_query: pytanie"]


def test_other_models_get_no_prefix(spy: SpyClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "embedding_model", "openai/text-embedding-3-small")

    embed_documents(["a"])
    embed_query("q")

    assert spy.received == ["a", "q"]


def test_embed_query_returns_single_vector(spy: SpyClient) -> None:
    vector = embed_query("q")

    assert len(vector) == settings.embedding_dim
    assert isinstance(vector[0], float)


def test_embed_documents_returns_one_vector_per_text(spy: SpyClient) -> None:
    assert len(embed_documents(["a", "b", "c"])) == 3


def test_wrong_dimension_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.retrieval.embedding.get_embedding_client", lambda: SpyClient(dim=1024))

    with pytest.raises(ValueError, match="1024 dimensions"):
        embed_documents(["a"])
    with pytest.raises(ValueError, match="expected 768"):
        embed_query("q")

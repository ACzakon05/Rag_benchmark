"""search() i warm_up(): orkiestracja trybów. Zależności są podmienione na atrapy."""

from __future__ import annotations

from contextlib import nullcontext
from uuid import uuid4

import pytest

from app.retrieval import retriever
from app.schemas.chunk import ScoredChunk
from app.schemas.config import RetrievalMethod
from tests.retrieval.helpers import make_chunk, make_config


class Spy:
    """Zbiera wywołania podmienionych funkcji."""

    def __init__(self) -> None:
        self.dense_limits: list[int] = []
        self.bm25_limits: list[int] = []
        self.rerank_calls: list[tuple[str, list[ScoredChunk], int]] = []
        self.dense_ids: list[str] = [f"d{i}" for i in range(50)]
        self.bm25_ids: list[str] = []
        self.model_loaded = 0
        self.query_embedded = 0


@pytest.fixture
def spy(monkeypatch: pytest.MonkeyPatch) -> Spy:
    s = Spy()

    def dense(_db, _cid, _query, limit):
        s.dense_limits.append(limit)
        return [(make_chunk(i), 1 - 0.01 * n) for n, i in enumerate(s.dense_ids[:limit])]

    def lexical(_db, _cid, _query, limit):
        s.bm25_limits.append(limit)
        return [(make_chunk(i), 10.0 - n) for n, i in enumerate(s.bm25_ids[:limit])]

    def fake_rerank(query, chunks, top_k):
        s.rerank_calls.append((query, chunks, top_k))
        return list(reversed(chunks))[:top_k]

    def fake_get_model():
        s.model_loaded += 1

    def fake_embed_query(_query):
        s.query_embedded += 1
        return [0.0]

    monkeypatch.setattr(retriever, "SessionLocal", lambda: nullcontext(object()))
    monkeypatch.setattr(retriever, "dense_search", dense)
    monkeypatch.setattr(retriever, "bm25_search", lexical)
    monkeypatch.setattr(retriever, "rerank", fake_rerank)
    monkeypatch.setattr(retriever, "get_model", fake_get_model)
    monkeypatch.setattr(retriever, "embed_query", fake_embed_query)
    return s


def _search(config, query: str = "pytanie") -> list[ScoredChunk]:
    return retriever.search(str(uuid4()), query, config)


def _ids(results: list[ScoredChunk]) -> list[str]:
    return [r.chunk.chunk_id for r in results]


def test_dense_returns_top_k_with_consecutive_ranks(spy: Spy) -> None:
    results = _search(make_config(RetrievalMethod.DENSE, top_k=3))

    assert _ids(results) == ["d0", "d1", "d2"]
    assert [r.rank for r in results] == [1, 2, 3]
    assert results[0].score == pytest.approx(1.0)


def test_dense_without_rerank_fetches_exactly_top_k_and_skips_bm25(spy: Spy) -> None:
    _search(make_config(RetrievalMethod.DENSE, top_k=3))

    assert spy.dense_limits == [3]
    assert spy.bm25_limits == []
    assert spy.rerank_calls == []


def test_search_does_not_mutate_the_config(spy: Spy) -> None:
    # regresja: `hybrid = config.retrieval = HYBRID` przestawiało tryb na hybrid
    config = make_config(RetrievalMethod.DENSE, top_k=3)

    _search(config)

    assert config.retrieval == RetrievalMethod.DENSE
    assert spy.bm25_limits == []


def test_hybrid_fetches_wider_pool_from_both_retrievers(spy: Spy) -> None:
    spy.bm25_ids = ["d2", "x0"]

    _search(make_config(RetrievalMethod.HYBRID, top_k=3))

    assert spy.dense_limits == [12]
    assert spy.bm25_limits == [12]


def test_hybrid_fuses_rankings_with_rrf(spy: Spy) -> None:
    spy.bm25_ids = ["d2", "x0"]  # d2: 3. w dense i 1. w BM25 -> wygrywa

    results = _search(make_config(RetrievalMethod.HYBRID, top_k=3))

    assert _ids(results)[0] == "d2"
    assert len(results) == 3
    assert [r.rank for r in results] == [1, 2, 3]
    assert results[0].score == pytest.approx(1 / 63 + 1 / 61)


def test_hybrid_can_return_chunks_found_only_by_bm25(spy: Spy) -> None:
    spy.dense_ids = ["d0", "d1"]
    spy.bm25_ids = ["x0", "x1", "x2"]

    results = _search(make_config(RetrievalMethod.HYBRID, top_k=10))

    assert {"x0", "x1", "x2"} <= set(_ids(results))


def test_rerank_gets_wide_pool_and_returns_top_k(spy: Spy) -> None:
    results = _search(make_config(RetrievalMethod.DENSE, top_k=2, reranking=True), "moje pytanie")

    assert spy.dense_limits == [8]
    [(query, candidates, top_k)] = spy.rerank_calls
    assert query == "moje pytanie"
    assert len(candidates) == 8
    assert [c.rank for c in candidates] == list(range(1, 9))
    assert top_k == 2
    assert len(results) == 2


def test_hybrid_with_rerank_uses_wide_pool_and_reranks_fused_list(spy: Spy) -> None:
    spy.bm25_ids = ["x0"]

    _search(make_config(RetrievalMethod.HYBRID, top_k=2, reranking=True))

    assert spy.dense_limits == [8]
    assert spy.bm25_limits == [8]
    [(_, candidates, _)] = spy.rerank_calls
    assert len(candidates) == 8


def test_fewer_results_than_top_k_is_fine(spy: Spy) -> None:
    spy.dense_ids = ["d0", "d1"]

    results = _search(make_config(RetrievalMethod.DENSE, top_k=5))

    assert _ids(results) == ["d0", "d1"]


def test_empty_collection_returns_empty_list(spy: Spy) -> None:
    spy.dense_ids = []

    assert _search(make_config(RetrievalMethod.HYBRID, top_k=3)) == []


def test_invalid_collection_id_raises(spy: Spy) -> None:
    with pytest.raises(ValueError):
        retriever.search("to-nie-uuid", "pytanie", make_config())


def test_candidate_multiplier_is_four() -> None:
    assert retriever.CANDIDATE_MULTIPLIER == 4


def test_warm_up_embeds_but_skips_model_without_rerank(spy: Spy) -> None:
    retriever.warm_up(make_config(reranking=False))

    assert spy.query_embedded == 1
    assert spy.model_loaded == 0


def test_warm_up_loads_reranker_model_when_enabled(spy: Spy) -> None:
    retriever.warm_up(make_config(reranking=True))

    assert spy.query_embedded == 1
    assert spy.model_loaded == 1

"""Reranker: kolejność wg ocen modelu, przycinanie do top_k, brak ładowania dla pustej listy."""

from __future__ import annotations

import pytest

from app.retrieval import reranker
from tests.retrieval.helpers import make_scored


class FakeModel:
    def __init__(self, scores_by_text: dict[str, float]) -> None:
        self.scores_by_text = scores_by_text
        self.pairs: list[tuple[str, str]] = []

    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        self.pairs = list(pairs)
        return [self.scores_by_text[text] for _, text in pairs]


@pytest.fixture
def model(monkeypatch: pytest.MonkeyPatch) -> FakeModel:
    fake = FakeModel({"a": 0.1, "b": 0.9, "c": 0.5, "d": 0.7})
    monkeypatch.setattr(reranker, "get_model", lambda: fake)
    return fake


def _candidates() -> list:
    return [make_scored(x, rank=i) for i, x in enumerate("abcd", start=1)]


def test_orders_by_model_score_descending(model: FakeModel) -> None:
    result = reranker.rerank("pytanie", _candidates(), top_k=4)

    assert [r.chunk.text for r in result] == ["b", "d", "c", "a"]
    assert [r.score for r in result] == [0.9, 0.7, 0.5, 0.1]


def test_ranks_are_renumbered_from_one(model: FakeModel) -> None:
    result = reranker.rerank("pytanie", _candidates(), top_k=4)

    assert [r.rank for r in result] == [1, 2, 3, 4]


def test_cuts_to_top_k(model: FakeModel) -> None:
    result = reranker.rerank("pytanie", _candidates(), top_k=2)

    assert [r.chunk.text for r in result] == ["b", "d"]


def test_top_k_larger_than_candidates_returns_all(model: FakeModel) -> None:
    assert len(reranker.rerank("pytanie", _candidates(), top_k=10)) == 4


def test_model_gets_query_chunk_pairs(model: FakeModel) -> None:
    reranker.rerank("pytanie", _candidates(), top_k=4)

    assert model.pairs == [("pytanie", "a"), ("pytanie", "b"), ("pytanie", "c"), ("pytanie", "d")]


def test_scores_are_plain_floats(model: FakeModel) -> None:
    result = reranker.rerank("pytanie", _candidates(), top_k=1)

    assert type(result[0].score) is float


def test_empty_input_does_not_load_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom() -> None:
        raise AssertionError("model nie powinien być ładowany")

    monkeypatch.setattr(reranker, "get_model", boom)

    assert reranker.rerank("pytanie", [], top_k=3) == []

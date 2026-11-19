"""RRF: łączenie rankingów po pozycjach."""

from __future__ import annotations

import pytest

from app.retrieval.fusion import RRF_K, rrf
from tests.retrieval.helpers import make_chunk

A, B, C, D, E = (make_chunk(x) for x in "ABCDE")
# make_chunk(x) ustawia chunk_id == x, więc ten sam chunk w dwóch listach ma to samo id


def _ids(result: list) -> list[str]:
    return [chunk.chunk_id for chunk, _ in result]


def test_matches_worked_example() -> None:
    result = rrf([[A, B, C, D], [C, A, E, B]])

    assert _ids(result) == ["A", "C", "B", "E", "D"]
    scores = {chunk.chunk_id: score for chunk, score in result}
    assert scores["A"] == pytest.approx(1 / 61 + 1 / 62)
    assert scores["C"] == pytest.approx(1 / 63 + 1 / 61)
    assert scores["B"] == pytest.approx(1 / 62 + 1 / 64)
    assert scores["E"] == pytest.approx(1 / 63)
    assert scores["D"] == pytest.approx(1 / 64)


def test_single_ranking_keeps_order() -> None:
    assert _ids(rrf([[C, A, B]])) == ["C", "A", "B"]


def test_empty_input() -> None:
    assert rrf([]) == []
    assert rrf([[], []]) == []


def test_chunk_first_in_both_rankings_gets_double_score() -> None:
    [(chunk, score)] = rrf([[A], [A]])

    assert chunk.chunk_id == "A"
    assert score == pytest.approx(2 / (RRF_K + 1))


def test_agreement_beats_a_single_first_place() -> None:
    # X jest 1. tylko w jednym rankingu, Y 3. w obu: zgodność rankingów wygrywa
    x, y = make_chunk("X"), make_chunk("Y")
    filler = [make_chunk(f"f{i}") for i in range(4)]

    result = rrf([[x, *filler[:1], y], [*filler[1:2], *filler[2:3], y]])

    assert _ids(result)[0] == "Y"


def test_chunk_in_one_ranking_scores_less_than_in_both() -> None:
    result = dict((c.chunk_id, s) for c, s in rrf([[A, B], [A]]))

    assert result["A"] > result["B"]


def test_scores_are_sorted_descending() -> None:
    scores = [score for _, score in rrf([[A, B, C, D], [E, D, C, B, A]])]

    assert scores == sorted(scores, reverse=True)


def test_returns_original_chunk_objects() -> None:
    [(chunk, _)] = rrf([[A]])

    assert chunk is A

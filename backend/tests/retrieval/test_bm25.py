"""BM25: tokenizacja, ranking, limit i cache. Bez bazy: sesję udaje FakeDb."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.config import settings
from app.models import Chunk
from app.retrieval import bm25
from app.retrieval.bm25 import bm25_search

CORPUS = [
    "serwer obsługuje 500 połączeń",
    "serwer wymaga restartu co tydzień",
    "limit dobowy wynosi 100 jednostek",
    "reklamacje składa się w ciągu 14 dni",
    "hasło musi mieć 12 znaków",
    "kopie zapasowe powstają codziennie",
    "dostęp wymaga uwierzytelnienia",
    "faktury wystawiamy na koniec miesiąca",
]


class FakeDb:
    """Udaje Session: zlicza zapytania i zwraca z góry przygotowane wiersze."""

    def __init__(self, texts: list[str]) -> None:
        self.rows = [
            Chunk(
                id=uuid4(),
                collection_id=uuid4(),
                document_id=uuid4(),
                position=i,
                text=text,
                meta={},
                embedding=[0.0] * settings.embedding_dim,
            )
            for i, text in enumerate(texts)
        ]
        self.queries = 0

    def scalars(self, _stmt: object):
        self.queries += 1
        return iter(self.rows)


CID = UUID(int=1)


def test_tokenize_lowercases_and_keeps_polish_letters() -> None:
    assert bm25._tokenize("Limit X: 100 zł, żółć!") == ["limit", "x", "100", "zł", "żółć"]


def test_best_match_is_first() -> None:
    results = bm25_search(FakeDb(CORPUS), CID, "limit dobowy", limit=5)

    assert results[0][0].text == "limit dobowy wynosi 100 jednostek"


def test_returns_only_chunks_sharing_a_word_with_the_query() -> None:
    results = bm25_search(FakeDb(CORPUS), CID, "serwer", limit=10)

    assert {chunk.text for chunk, _ in results} == {
        "serwer obsługuje 500 połączeń",
        "serwer wymaga restartu co tydzień",
    }


def test_scores_are_positive_and_sorted_descending() -> None:
    results = bm25_search(FakeDb(CORPUS), CID, "serwer restartu", limit=10)
    scores = [score for _, score in results]

    assert all(score > 0 for score in scores)
    assert scores == sorted(scores, reverse=True)
    assert results[0][0].text == "serwer wymaga restartu co tydzień"


def test_query_without_matches_returns_empty_list() -> None:
    assert bm25_search(FakeDb(CORPUS), CID, "zebra kosmos", limit=5) == []


def test_limit_is_respected() -> None:
    assert len(bm25_search(FakeDb(CORPUS), CID, "serwer", limit=1)) == 1


def test_search_is_case_insensitive() -> None:
    results = bm25_search(FakeDb(CORPUS), CID, "SERWER", limit=5)

    assert len(results) == 2


def test_index_is_cached_per_collection() -> None:
    db = FakeDb(CORPUS)

    bm25_search(db, CID, "serwer", limit=5)
    bm25_search(db, CID, "limit", limit=5)

    assert db.queries == 1


def test_different_collections_are_cached_separately() -> None:
    db = FakeDb(CORPUS)

    bm25_search(db, UUID(int=1), "serwer", limit=5)
    bm25_search(db, UUID(int=2), "serwer", limit=5)

    assert db.queries == 2


def test_clear_cache_forces_reload() -> None:
    db = FakeDb(CORPUS)
    bm25_search(db, CID, "serwer", limit=5)

    bm25.clear_cache()
    bm25_search(db, CID, "serwer", limit=5)

    assert db.queries == 2


def test_empty_collection_returns_nothing_and_is_not_cached() -> None:
    db = FakeDb([])
    assert bm25_search(db, CID, "serwer", limit=5) == []

    db.rows = FakeDb(CORPUS).rows  # kolekcja zostaje zaindeksowana później
    results = bm25_search(db, CID, "serwer", limit=5)

    assert db.queries == 2
    assert len(results) == 2

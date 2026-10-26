"""Obsluga pojedynczych zapytan na zywo z modulu Playground (Osoba 1).

Zapytanie trafia prosto do istniejacej juz kolekcji wybranej konfiguracji
(bez ponownego indeksowania). Szkielet — bez implementacji.
"""

from __future__ import annotations

from app.schemas.playground import PlaygroundQuery, PlaygroundResponse


def answer_query(query: PlaygroundQuery) -> PlaygroundResponse:
    """search -> (reranking) -> generate dla gotowego indeksu konfiguracji."""
    raise NotImplementedError

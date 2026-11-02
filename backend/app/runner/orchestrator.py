"""Modul Wykonawczy (Osoba 1) — orkiestracja eksperymentu.

Odpowiedzialnosc: spina ingestion + retrieval + evaluation, mierzy czasy i tokeny,
prowadzi sekwencyjna petle wykonawcza (1 zapytanie naraz dla modeli lokalnych).

Przeplyw (per konfiguracja):
  1. chunk_documents -> index_chunks (brakujace kolekcje, wspoldzielone - ADR-0004)
  2. dla kazdego pytania: search -> (reranking) -> generate -> evaluate
  3. zapis wynikow do PostgreSQL; aktualizacja postepu (ExperimentProgress)

Szkielet — bez implementacji.
"""

from __future__ import annotations

from uuid import UUID

from app.config import settings
from app.runner.fake_runner import run_fake_experiment


def run_experiment(experiment_id: UUID) -> None:
    """Zadanie w tle: wykonuje caly eksperyment sekwencyjnie i zapisuje wyniki."""
    if settings.fake_runner:
        run_fake_experiment(experiment_id)
        return
    raise NotImplementedError

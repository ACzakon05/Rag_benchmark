"""Modul Wykonawczy (Osoba 1) — orkiestracja eksperymentu.

Odpowiedzialnosc: spina ingestion + retrieval + evaluation, mierzy czasy i tokeny,
prowadzi sekwencyjna petle wykonawcza (1 zapytanie naraz dla modeli lokalnych).

Przeplyw (per konfiguracja):
  1. chunk_documents -> index_chunks (dedykowana kolekcja)
  2. dla kazdego pytania: search -> (reranking) -> generate -> evaluate
  3. zapis wynikow do SQLite; aktualizacja postepu (ExperimentProgress)

Szkielet — bez implementacji.
"""

from __future__ import annotations

from app.schemas.experiment import ExperimentConfig


def run_experiment(experiment_id: str, config: ExperimentConfig) -> None:
    """Zadanie w tle: wykonuje caly eksperyment sekwencyjnie i zapisuje wyniki."""
    raise NotImplementedError

"""Endpointy zarzadzania zbiorami danych (US-1). Wlasciciel: Osoba 1.

Szkielet — sygnatury i kontrakty we/wy. Bez logiki.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.dataset import DatasetSummary

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetSummary)
def upload_dataset():
    """Wgranie dokumentow (.txt/.md/.pdf) + pliku testowego (.json/.csv).

    multipart/form-data: documents[] + testset. Waliduje strukture testsetu
    (question, ground_truth_answer, expected_context_snippet) i zwraca podsumowanie.
    """
    raise NotImplementedError


@router.get("/{dataset_id}", response_model=DatasetSummary)
def get_dataset(dataset_id: str):
    """Podsumowanie wgranego zbioru."""
    raise NotImplementedError

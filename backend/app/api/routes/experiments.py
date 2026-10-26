"""Endpointy konfiguracji i uruchamiania eksperymentow (US-2). Wlasciciel: Osoba 1.

Szkielet — sygnatury i kontrakty we/wy. Bez logiki.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.experiment import ExperimentConfig, ExperimentProgress

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentProgress, status_code=202)
def create_experiment(config: ExperimentConfig):
    """Tworzy eksperyment (2-4 konfiguracje) i startuje zadanie w tle."""
    raise NotImplementedError


@router.get("/{experiment_id}/progress", response_model=ExperimentProgress)
def get_progress(experiment_id: str):
    """Aktualny postep (np. 'Konfiguracja 2/4, pytanie 6/15')."""
    raise NotImplementedError

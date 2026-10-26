"""Endpointy wynikow eksperymentu (US-3, US-4). Wlasciciel: Osoba 1.

Szkielet — sygnatury i kontrakty we/wy. Bez logiki.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.evaluation import ExperimentResults

router = APIRouter(prefix="/experiments", tags=["results"])


@router.get("/{experiment_id}/results", response_model=ExperimentResults)
def get_results(experiment_id: str):
    """Komplet wynikow: tabela zbiorcza (makro) + szczegoly pytan (mikro)."""
    raise NotImplementedError


@router.get("/{experiment_id}/export")
def export_results(experiment_id: str, fmt: str = "json"):
    """Should-have: eksport wynikow do CSV / JSON."""
    raise NotImplementedError

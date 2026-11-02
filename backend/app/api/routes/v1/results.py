"""Endpointy wynikow eksperymentu (US-3, US-4). Wlasciciel: Osoba 1.

Szkielet — sygnatury i kontrakty we/wy. Bez logiki.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.database import DbSession
from app.schemas.evaluation import ExperimentResults
from app.services.experiment_service import experiment_service

router = APIRouter()


@router.get("/experiments/{experiment_id}/results")
def get_results(experiment_id: UUID, db: DbSession) -> ExperimentResults:
    """Tabela zbiorcza (makro) + szczegoly pytan (mikro); w trakcie eksperymentu czesciowe."""
    return experiment_service.get_results(db, experiment_id)


@router.get("/experiments/{experiment_id}/export")
def export_results(experiment_id: str, fmt: str = "json"):
    """Should-have: eksport wynikow do CSV / JSON."""
    raise NotImplementedError

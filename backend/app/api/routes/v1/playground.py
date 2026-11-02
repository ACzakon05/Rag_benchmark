"""Endpointy modulu Playground (US-5). Wlasciciel: Osoba 1.

Szkielet — sygnatury i kontrakty we/wy. Bez logiki.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.database import DbSession
from app.schemas.playground import PlaygroundQuery, PlaygroundResponse
from app.services.playground_service import playground_service

router = APIRouter()


@router.post("/playground/ask")
def ask(query: PlaygroundQuery, db: DbSession) -> PlaygroundResponse:
    """Pytanie na zywo do wybranej konfiguracji (gotowy indeks, bez reindeksacji)."""
    return playground_service.ask(db, query)


# Should-have: aktywacja wybranej konfiguracji jako stalego endpointu REST
# POST /api/v1/ask dla zewnetrznych aplikacji — do zaprojektowania w kolejnej iteracji.

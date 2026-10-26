"""Endpointy modulu Playground (US-5). Wlasciciel: Osoba 1.

Szkielet — sygnatury i kontrakty we/wy. Bez logiki.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.playground import PlaygroundQuery, PlaygroundResponse

router = APIRouter(prefix="/playground", tags=["playground"])


@router.post("/ask", response_model=PlaygroundResponse)
def ask(query: PlaygroundQuery):
    """Pytanie na zywo do wybranej konfiguracji (gotowy indeks, bez reindeksacji)."""
    raise NotImplementedError


# Should-have: aktywacja wybranej konfiguracji jako stalego endpointu REST
# POST /api/v1/ask dla zewnetrznych aplikacji — do zaprojektowania w kolejnej iteracji.

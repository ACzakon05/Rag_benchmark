"""Sesja i inicjalizacja bazy relacyjnej (SQLite + SQLModel).

Szkielet — bez logiki. Wlasciciel: Osoba 1.
"""

from __future__ import annotations

# from sqlmodel import Session, create_engine

# engine = ...  # TODO: create_engine(settings.database_url)


def init_db() -> None:
    """Tworzy tabele na starcie aplikacji (Etap 1)."""
    raise NotImplementedError


def get_session():
    """Dependency FastAPI dostarczajacy sesje DB."""
    raise NotImplementedError

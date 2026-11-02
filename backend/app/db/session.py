"""Sesja i inicjalizacja bazy relacyjnej (PostgreSQL + pgvector, SQLModel).

Szkielet — bez logiki. Wlasciciel: Osoba 1.
"""

from __future__ import annotations

# from sqlmodel import Session, create_engine

# engine = ...  # TODO: create_engine(settings.database_url)


def init_db() -> None:
    """Na starcie aplikacji: `CREATE EXTENSION IF NOT EXISTS vector`, potem tabele (Etap 1)."""
    raise NotImplementedError


def get_session():
    """Dependency FastAPI dostarczajacy sesje DB."""
    raise NotImplementedError

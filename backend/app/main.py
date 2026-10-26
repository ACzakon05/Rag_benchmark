"""Punkt wejscia aplikacji FastAPI.

Szkielet — montuje routery i konfiguruje CORS. Bez logiki biznesowej.
Wlasciciel: Osoba 1 (Architekt Backendu & Orkiestracji).
"""

from __future__ import annotations

from fastapi import FastAPI

# from fastapi.middleware.cors import CORSMiddleware
# from app.api.routes import datasets, experiments, results, playground

app = FastAPI(title="RAG Benchmark & Playground", version="0.1.0")

# TODO (Etap 1): CORS, rejestracja routerow, inicjalizacja DB, lifespan.
# app.include_router(datasets.router, prefix="/api/v1")
# app.include_router(experiments.router, prefix="/api/v1")
# app.include_router(results.router, prefix="/api/v1")
# app.include_router(playground.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    """Prosty health-check (do walking skeleton, Etap 2)."""
    raise NotImplementedError

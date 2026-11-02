from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import head_router
from app.config import settings
from app.database import DbSession

api = FastAPI(title="RAG Benchmark & Playground", version="0.1.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(head_router)


@api.get("/health")
async def health(db: DbSession) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

"""Konfiguracja aplikacji wczytywana ze zmiennych srodowiskowych (.env).

Szkielet — pola odpowiadaja plikowi .env.example. Bez logiki.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:8501"  # Streamlit dev

    database_url: str = "sqlite:///./data/sqlite/app.db"

    vector_db_provider: str = "qdrant"
    qdrant_url: str = "http://qdrant:6333"

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://host.docker.internal:11434"
    generation_model: str = "qwen3:8b"
    judge_model: str = "qwen3:8b"
    embedding_model: str = "nomic-embed-text"
    reranker_model: str = "BAAI/bge-reranker-base"

    openai_api_key: str | None = None
    openai_base_url: str | None = None

    max_concurrent_llm_calls: int = 1
    judge_temperature: float = 0.0

    class Config:
        env_file = ".env"


# def get_settings() -> Settings: ...  # TODO: cache (lru_cache)

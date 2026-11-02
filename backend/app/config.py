from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    api_v1: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:8501"]

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "rag_benchmark"
    db_user: str = "rag"
    db_password: SecretStr = SecretStr("rag")
    # Part of the schema: changing it requires a migration.
    embedding_dim: int = 768

    redis_host: str = "localhost"
    redis_port: int = 6379

    upload_dir: Path = REPO_ROOT / "data" / "uploads"

    ollama_base_url: str = "http://localhost:11434"
    # LiteLLM model ids: the prefix selects the provider (ollama_chat/, openai/, anthropic/, ...).
    # API keys are read by LiteLLM straight from the environment (OPENAI_API_KEY, ...).
    generation_model: str = "ollama_chat/qwen3:8b"
    judge_model: str = "ollama_chat/qwen3:8b"
    embedding_model: str = "ollama/nomic-embed-text"
    reranker_model: str = "BAAI/bge-reranker-base"

    # Until ingestion, retrieval and evaluation exist, the worker writes made-up results so the
    # frontend has data to show. Fake collections use their own embedding model name, so a
    # real run never reuses fake chunks.
    fake_runner: bool = True
    fake_runner_delay_s: float = 0.3

    max_concurrent_llm_calls: int = 1
    judge_temperature: float = 0.0

    @property
    def db_uri(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password.get_secret_value()}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

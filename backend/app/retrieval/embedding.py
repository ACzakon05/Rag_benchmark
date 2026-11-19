from __future__ import annotations

from app.config import settings
from app.llm.client import get_embedding_client


def embed_documents(texts: list[str]) -> list[list[float]]:
    prefix = "search_document: " if _uses_prefixes() else ""

    return _embed([prefix + text for text in texts])


def embed_query(query: str) -> list[float]:
    prefix = "search_query: " if _uses_prefixes() else ""
    [vector] = _embed([prefix + query])
    return vector


def _embed(texts: list[str]) -> list[list[float]]:
    vectors = get_embedding_client().embed(texts)
    for vector in vectors:
        if len(vector) != settings.embedding_dim:
            raise ValueError(
                f"Embedding has {len(vector)} dimensions, expected {settings.embedding_dim}. "
                "Check EMBEDDING_MODEL / EMBEDDING_DIM."
            )
    return vectors


def _uses_prefixes() -> bool:
    # nomic-embed-text był trenowany z prefiksami zależnymi od roli tekstu;
    # po zmianie modelu w .env prefiksy znikają automatycznie.
    return "nomic" in settings.embedding_model

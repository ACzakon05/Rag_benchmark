"""Ujednolicony klient LLM (Osoba 1) — wzorzec Adaptera.

Komunikacja z Ollama przez interfejs kompatybilny z OpenAI API. Dodanie modeli
komercyjnych (OpenAI, Anthropic, Cohere) nie wymaga zmian w logice silnika RAG
ani ewaluatora — wystarczy zmiana URL, nazwy modelu i klucza API.

Szkielet — bez implementacji.
"""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    """Wspolny interfejs dla dostawcow (Ollama / OpenAI-compatible)."""

    def generate(self, prompt: str, *, model: str, temperature: float = 0.0) -> tuple[str, int]:
        """Zwraca (tekst_odpowiedzi, liczba_tokenow)."""
        ...

    def generate_json(self, prompt: str, *, model: str, schema: dict | None = None) -> dict:
        """Wymuszona odpowiedz JSON (dla LLM-as-a-Judge)."""
        ...

    def embed(self, texts: list[str], *, model: str) -> list[list[float]]:
        """Embeddingi (nomic-embed-text)."""
        ...


def get_llm_client() -> LLMClient:
    """Fabryka klienta wg LLM_PROVIDER z konfiguracji."""
    raise NotImplementedError

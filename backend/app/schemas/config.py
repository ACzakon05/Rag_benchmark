"""Enumy i typy opisujace warianty konfiguracji potoku RAG.

Kontrakt wspoldzielony przez konfigurator (frontend), runner i evaluation.
Szkielet — wartosci do zatwierdzenia na Etapie 1.
"""

from __future__ import annotations

from enum import Enum


class ChunkingStrategy(str, Enum):
    """Strategia dzielenia dokumentu na fragmenty."""

    FIXED_TOKENS = "fixed_tokens"   # stala liczba tokenow + overlap
    STRUCTURAL = "structural"       # po naglowkach / akapitach


class RetrievalMethod(str, Enum):
    """Metoda wyszukiwania fragmentow."""

    DENSE = "dense"         # wektorowe
    HYBRID = "hybrid"       # dense + BM25 (laczone przez RRF)


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"       # adapter kompatybilny z OpenAI API

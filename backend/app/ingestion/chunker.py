"""Modul Ingestii i Chunkingu (Osoba 3).

Odpowiedzialnosc: ekstrakcja czystego tekstu z plikow (.txt/.md/.pdf) oraz
dzielenie go na fragmenty wg wybranej strategii.

Kontrakt dostarczany reszcie zespolu:
    chunk_documents(files, config) -> list[DocumentChunk]

Zaleznosci: brak. Moze byc rozwijany w 100% niezaleznie.
Szkielet — bez implementacji.
"""

from __future__ import annotations

from app.schemas.chunk import DocumentChunk
from app.schemas.experiment import RagConfig


def extract_text(file_path: str) -> str:
    """Ekstrakcja czystego tekstu z .txt / .md / tekstowego .pdf."""
    raise NotImplementedError


def chunk_fixed_tokens(text: str, document_id: str, size: int, overlap: int) -> list[DocumentChunk]:
    """Chunking o stalej liczbie tokenow z overlapem."""
    raise NotImplementedError


def chunk_structural(text: str, document_id: str) -> list[DocumentChunk]:
    """Chunking wg struktury: naglowki Markdown (#, ##, ###) / akapity."""
    raise NotImplementedError


def chunk_documents(files: list[str], config: RagConfig) -> list[DocumentChunk]:
    """Glowny interfejs modulu: pliki + konfiguracja -> lista fragmentow."""
    raise NotImplementedError

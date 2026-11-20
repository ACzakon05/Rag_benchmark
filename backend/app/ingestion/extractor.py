"""Ekstrakcja czystego tekstu z plików .txt, .md oraz tekstowych .pdf (Osoba 3)."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = frozenset({".txt", ".md", ".pdf"})

_EXCESS_BLANK_LINES = re.compile(r"\n{3,}")
_TRAILING_SPACES = re.compile(r"[ \t]+\n")
_DOT_LEADERS = re.compile(r"(?:\.\s*){4,}")
_MULTI_SPACES = re.compile(r"[ \t]{2,}")


def extract_text(file_path: str | Path) -> str:
    """Ekstrakcja czystego tekstu z .txt / .md / tekstowego .pdf."""
    path = _validate_path(file_path)
    if path.suffix.lower() == ".pdf":
        pages = extract_pdf_pages(path)
        return "\n\n".join(text for _, text in pages)
    return _normalize_text(_read_text_bytes(path.read_bytes()))


def extract_pdf_pages(file_path: str | Path) -> list[tuple[int, str]]:
    """Zwraca listę (numer_strony_od_1, tekst) dla niepustych stron PDF."""
    path = _validate_path(file_path)
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got '{path.name}'.")

    reader = PdfReader(path)
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError(f"PDF file '{path.name}' is encrypted and cannot be read.")

    pages: list[tuple[int, str]] = []
    for page_num, page in enumerate(reader.pages, start=1):
        cleaned = _normalize_text(page.extract_text() or "")
        if cleaned:
            pages.append((page_num, cleaned))
    return pages


def _validate_path(file_path: str | Path) -> Path:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Document not found: '{path}'.")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{path.suffix}' for '{path.name}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )
    return path


def _read_text_bytes(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1250"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _DOT_LEADERS.sub(" ... ", text)
    text = _MULTI_SPACES.sub(" ", text)
    text = _TRAILING_SPACES.sub("\n", text)
    text = _EXCESS_BLANK_LINES.sub("\n\n", text)
    return text.strip()

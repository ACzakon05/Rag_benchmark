"""Modul Ingestii i Chunkingu (Osoba 3).

Odpowiedzialnosc: ekstrakcja czystego tekstu z plikow (.txt/.md/.pdf) oraz
dzielenie go na fragmenty wg wybranej strategii.

Kontrakt dostarczany reszcie zespolu:
    chunk_documents(files, config) -> list[DocumentChunk]

Zaleznosci: brak. Moze byc rozwijany w 100% niezaleznie.
Szkielet — bez implementacji.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.ingestion.extractor import extract_pdf_pages, extract_text
from app.schemas.chunk import DocumentChunk
from app.schemas.config import ChunkingStrategy
from app.schemas.experiment import RagConfig

__all__ = [
    "chunk_documents",
    "chunk_fixed_tokens",
    "chunk_structural",
    "extract_text",
]

DocumentInput = str | Path | tuple[str, str | Path]

# Domyślny limit zgodny z oknem rerankera (MAX_PAIR_TOKENS = 512 w retrieval/reranker.py).
DEFAULT_STRUCTURAL_MAX_TOKENS = 512

_TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]")
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})")
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ0-9])")


@dataclass(frozen=True)
class _Section:
    heading_path: str | None
    heading_prefix: str | None
    body: str


def chunk_fixed_tokens(
    text: str,
    document_id: str,
    size: int,
    overlap: int,
    *,
    metadata: dict[str, Any] | None = None,
) -> list[DocumentChunk]:
    """Chunking o stałej liczbie tokenów z overlapem.

    Wycina dokładne zakresy znaków z oryginału, dzięki czemu nie psuje polskich
    znaków ani dopasowania cytatu `expected_context_snippet`.
    """
    if size <= 0:
        raise ValueError("size must be greater than 0")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    spans = [(m.start(), m.end()) for m in _TOKEN_PATTERN.finditer(text)]
    if not spans:
        return []

    base_meta = dict(metadata) if metadata else {}
    step = size - overlap
    chunks: list[DocumentChunk] = []

    for position, start_idx in enumerate(range(0, len(spans), step)):
        end_idx = min(start_idx + size, len(spans))
        chunk_text = text[spans[start_idx][0] : spans[end_idx - 1][1]].strip()
        if chunk_text:
            chunks.append(
                DocumentChunk(
                    chunk_id=str(uuid4()),
                    document_id=document_id,
                    text=chunk_text,
                    position=position,
                    metadata={
                        **base_meta,
                        "strategy": ChunkingStrategy.FIXED_TOKENS.value,
                        "token_count": end_idx - start_idx,
                    },
                )
            )
        if end_idx >= len(spans):
            break

    return chunks


def chunk_structural(
    text: str,
    document_id: str,
    *,
    max_chunk_tokens: int = DEFAULT_STRUCTURAL_MAX_TOKENS,
    metadata: dict[str, Any] | None = None,
) -> list[DocumentChunk]:
    """Chunking wg struktury: nagłówki Markdown (#, ##, ###) lub akapity (.txt/.pdf)."""
    if max_chunk_tokens <= 0:
        raise ValueError("max_chunk_tokens must be greater than 0")

    cleaned = text.strip()
    if not cleaned:
        return []

    base_meta = dict(metadata) if metadata else {}
    sections = _parse_markdown_sections(cleaned)

    raw_pieces: list[tuple[str, str | None]] = []
    if sections is not None:
        for section in sections:
            for piece in _split_section(section, max_chunk_tokens):
                raw_pieces.append((piece, section.heading_path))
    else:
        for paragraph in _split_paragraphs(cleaned):
            for piece in _fit_to_limit(paragraph, max_chunk_tokens):
                raw_pieces.append((piece, None))

    chunks: list[DocumentChunk] = []
    for position, (piece_text, heading_path) in enumerate(raw_pieces):
        chunk_meta: dict[str, Any] = {
            **base_meta,
            "strategy": ChunkingStrategy.STRUCTURAL.value,
            "token_count": _count_tokens(piece_text),
        }
        if heading_path:
            chunk_meta["heading"] = heading_path
        chunks.append(
            DocumentChunk(
                chunk_id=str(uuid4()),
                document_id=document_id,
                text=piece_text,
                position=position,
                metadata=chunk_meta,
            )
        )
    return chunks


def chunk_documents(
    files: Sequence[DocumentInput],
    config: RagConfig,
    *,
    document_ids: Sequence[str] | None = None,
) -> list[DocumentChunk]:
    """Główny interfejs modułu: pliki + konfiguracja -> lista fragmentów.

    Akceptuje listę ścieżek (`list[str]`) zgodnie z kontraktem lub pary
    `(document_id, file_path)` / parametr `document_ids`, aby orchestrator mógł
    przekazać rzeczywiste UUID z tabeli `document`.
    """
    resolved = _resolve_inputs(files, document_ids)
    all_chunks: list[DocumentChunk] = []

    for doc_id, path in resolved:
        text, page_spans = _load_document(path)
        if not text:
            continue

        base_meta: dict[str, Any] = {"source": path.name}
        if config.chunking == ChunkingStrategy.FIXED_TOKENS:
            if config.chunk_size_tokens is None or config.chunk_overlap_tokens is None:
                raise ValueError("fixed_tokens requires chunk_size_tokens and chunk_overlap_tokens")
            doc_chunks = chunk_fixed_tokens(
                text,
                doc_id,
                size=config.chunk_size_tokens,
                overlap=config.chunk_overlap_tokens,
                metadata=base_meta,
            )
        elif config.chunking == ChunkingStrategy.STRUCTURAL:
            doc_chunks = chunk_structural(text, doc_id, metadata=base_meta)
        else:
            raise ValueError(f"Unsupported chunking strategy: {config.chunking}")

        if page_spans:
            _attach_page_metadata(text, doc_chunks, page_spans)
        all_chunks.extend(doc_chunks)

    return all_chunks


def _resolve_inputs(
    files: Sequence[DocumentInput],
    document_ids: Sequence[str] | None,
) -> list[tuple[str, Path]]:
    if document_ids is not None and len(document_ids) != len(files):
        raise ValueError("document_ids must have the same length as files")

    resolved: list[tuple[str, Path]] = []
    for idx, item in enumerate(files):
        if isinstance(item, tuple):
            doc_id, raw_path = item
            if document_ids is not None:
                doc_id = document_ids[idx]
            resolved.append((str(doc_id), Path(raw_path)))
        else:
            doc_id = str(document_ids[idx]) if document_ids is not None else str(uuid4())
            resolved.append((doc_id, Path(item)))
    return resolved


def _load_document(path: Path) -> tuple[str, list[tuple[int, int, int]]]:
    """Zwraca pełny tekst oraz (dla PDF) mapowanie zakresów znaków na numery stron."""
    if path.suffix.lower() != ".pdf":
        return extract_text(path), []

    pages = extract_pdf_pages(path)
    if not pages:
        return "", []

    parts: list[str] = []
    spans: list[tuple[int, int, int]] = []
    cursor = 0
    for idx, (page_num, page_text) in enumerate(pages):
        if idx > 0:
            cursor += 2  # separator "\n\n"
        start = cursor
        end = start + len(page_text)
        spans.append((page_num, start, end))
        parts.append(page_text)
        cursor = end
    return "\n\n".join(parts), spans


def _attach_page_metadata(
    full_text: str,
    chunks: list[DocumentChunk],
    page_spans: list[tuple[int, int, int]],
) -> None:
    search_from = 0
    for chunk in chunks:
        probe = chunk.text[:80]
        pos = full_text.find(probe, search_from)
        if pos == -1:
            pos = full_text.find(probe)
        if pos == -1:
            continue
        chunk_end = pos + len(chunk.text)
        search_from = pos
        pages = [page_num for page_num, start, end in page_spans if start < chunk_end and end > pos]
        if pages:
            chunk.metadata["page"] = pages[0]
            if len(pages) > 1:
                chunk.metadata["pages"] = pages


def _count_tokens(text: str) -> int:
    return len(_TOKEN_PATTERN.findall(text))


def _parse_markdown_sections(text: str) -> list[_Section] | None:
    """Dzieli dokument na sekcje wg nagłówków Markdown; zwraca None, gdy brak nagłówków."""
    lines = text.split("\n")
    has_headings = False
    in_fence = False
    for line in lines:
        if _FENCE_PATTERN.match(line):
            in_fence = not in_fence
            continue
        if not in_fence and _HEADING_PATTERN.match(line):
            has_headings = True
            break
    if not has_headings:
        return None

    sections: list[_Section] = []
    heading_stack: list[tuple[int, str, str]] = []  # (level, title, raw_line)
    active_headings: list[str] = []
    body_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(body_lines).strip()
        if not body:
            return
        path = " > ".join(title for _, title, _ in heading_stack) if heading_stack else None
        prefix = "\n".join(active_headings) if active_headings else None
        sections.append(_Section(heading_path=path, heading_prefix=prefix, body=body))
        body_lines.clear()
        active_headings.clear()

    in_fence = False
    for line in lines:
        if _FENCE_PATTERN.match(line):
            in_fence = not in_fence
            body_lines.append(line)
            continue

        match = None if in_fence else _HEADING_PATTERN.match(line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            raw_line = line.strip()
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            # Jeśli poprzedni nagłówek nadrzędny był pusty (brak akapitu przed podnagłówkiem),
            # zachowujemy go w prefiksie, żeby nie tracić kontekstu sekcji.
            if active_headings and len(active_headings) >= len(heading_stack) + 1:
                active_headings = [raw for _, _, raw in heading_stack]
            heading_stack.append((level, title, raw_line))
            active_headings.append(raw_line)
        else:
            body_lines.append(line)

    flush()
    # Dokument zawierający wyłącznie nagłówki bez treści: zwróć same nagłówki zamiast pustej listy.
    if not sections and heading_stack:
        raw = "\n".join(h for _, _, h in heading_stack)
        path = " > ".join(title for _, title, _ in heading_stack)
        sections.append(_Section(heading_path=path, heading_prefix=None, body=raw))

    return sections


def _split_section(section: _Section, max_tokens: int) -> list[str]:
    prefix = f"{section.heading_prefix}\n" if section.heading_prefix else ""
    full = f"{prefix}{section.body}".strip()
    if _count_tokens(full) <= max_tokens:
        return [full]

    prefix_tokens = _count_tokens(prefix)
    body_budget = max(max_tokens - prefix_tokens, max_tokens // 2)

    paragraphs = _split_paragraphs(section.body)
    grouped = _pack_units(paragraphs, body_budget, separator="\n\n")
    return [f"{prefix}{part}".strip() for part in grouped]


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in _PARAGRAPH_SPLIT.split(text) if p.strip()]


def _fit_to_limit(paragraph: str, max_tokens: int) -> list[str]:
    if _count_tokens(paragraph) <= max_tokens:
        return [paragraph]

    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(paragraph) if s.strip()]
    if len(sentences) > 1:
        return _pack_units(sentences, max_tokens, separator=" ")
    return _slice_by_tokens(paragraph, max_tokens)


def _pack_units(units: list[str], max_tokens: int, *, separator: str) -> list[str]:
    packed: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for unit in units:
        unit_tokens = _count_tokens(unit)
        if unit_tokens > max_tokens:
            if current_parts:
                packed.append(separator.join(current_parts))
                current_parts, current_tokens = [], 0
            sub_units = (
                _fit_to_limit(unit, max_tokens)
                if separator == "\n\n"
                else _slice_by_tokens(unit, max_tokens)
            )
            packed.extend(sub_units)
            continue

        if current_parts and current_tokens + unit_tokens > max_tokens:
            packed.append(separator.join(current_parts))
            current_parts, current_tokens = [], 0

        current_parts.append(unit)
        current_tokens += unit_tokens

    if current_parts:
        packed.append(separator.join(current_parts))
    return packed


def _slice_by_tokens(text: str, max_tokens: int) -> list[str]:
    spans = [(m.start(), m.end()) for m in _TOKEN_PATTERN.finditer(text)]
    if not spans:
        return []
    pieces: list[str] = []
    for start_idx in range(0, len(spans), max_tokens):
        end_idx = min(start_idx + max_tokens, len(spans))
        piece = text[spans[start_idx][0] : spans[end_idx - 1][1]].strip()
        if piece:
            pieces.append(piece)
    return pieces

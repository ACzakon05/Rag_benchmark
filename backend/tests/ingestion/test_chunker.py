"""Testy strategii chunkingu (fixed_tokens, structural) oraz chunk_documents."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.ingestion import chunker, extractor
from app.ingestion.chunker import chunk_documents, chunk_fixed_tokens, chunk_structural
from app.schemas.config import ChunkingStrategy, RetrievalMethod
from app.schemas.experiment import RagConfig


def _fixed_config(size: int = 20, overlap: int = 5) -> RagConfig:
    return RagConfig(
        label="A",
        chunking=ChunkingStrategy.FIXED_TOKENS,
        chunk_size_tokens=size,
        chunk_overlap_tokens=overlap,
        retrieval=RetrievalMethod.DENSE,
        top_k=3,
        reranking_enabled=False,
    )


def _structural_config() -> RagConfig:
    return RagConfig(
        label="B",
        chunking=ChunkingStrategy.STRUCTURAL,
        retrieval=RetrievalMethod.HYBRID,
        top_k=3,
        reranking_enabled=True,
    )


def test_fixed_tokens_splits_with_exact_overlap_and_no_redundant_tail() -> None:
    doc_id = str(uuid4())
    text = " ".join(f"w{i}" for i in range(10))

    chunks = chunk_fixed_tokens(text, doc_id, size=6, overlap=2)

    assert [c.text for c in chunks] == [
        "w0 w1 w2 w3 w4 w5",
        "w4 w5 w6 w7 w8 w9",
    ]
    assert [c.position for c in chunks] == [0, 1]
    assert all(c.document_id == doc_id for c in chunks)
    assert all(UUID(c.chunk_id) for c in chunks)
    assert len({c.chunk_id for c in chunks}) == 2


def test_fixed_tokens_preserves_polish_text_and_punctuation() -> None:
    text = "Zażółć gęślą jaźń — limit wynosi 100 zł (brutto)."
    chunks = chunk_fixed_tokens(text, str(uuid4()), size=50, overlap=0)

    assert len(chunks) == 1
    assert chunks[0].text == text


def test_fixed_tokens_empty_input_returns_empty_list() -> None:
    assert chunk_fixed_tokens("   \n\t ", str(uuid4()), size=10, overlap=2) == []


@pytest.mark.parametrize(
    ("size", "overlap"),
    [(0, 0), (-5, 0), (10, -1), (10, 10), (10, 12)],
)
def test_fixed_tokens_validates_parameters(size: int, overlap: int) -> None:
    with pytest.raises(ValueError):
        chunk_fixed_tokens("jeden dwa trzy", str(uuid4()), size=size, overlap=overlap)


def test_structural_markdown_splits_by_headings_and_keeps_hierarchy() -> None:
    md = "# Bezpieczeństwo\n\n## Hasła\nHasło musi mieć 14 znaków.\n\n## VPN\nUżywamy WireGuard.\n"
    chunks = chunk_structural(md, str(uuid4()))

    assert len(chunks) == 2
    assert "# Bezpieczeństwo" in chunks[0].text
    assert "## Hasła" in chunks[0].text
    assert "14 znaków" in chunks[0].text
    assert chunks[0].metadata["heading"] == "Bezpieczeństwo > Hasła"

    assert "## VPN" in chunks[1].text
    assert "WireGuard" in chunks[1].text
    assert chunks[1].metadata["heading"] == "Bezpieczeństwo > VPN"
    assert [c.position for c in chunks] == [0, 1]


def test_structural_ignores_hash_comments_inside_code_blocks() -> None:
    md = "# Skrypt\n\n```python\n# to jest komentarz, nie nagłówek\nprint('ok')\n```\n"
    chunks = chunk_structural(md, str(uuid4()))

    assert len(chunks) == 1
    assert "# to jest komentarz" in chunks[0].text
    assert chunks[0].metadata["heading"] == "Skrypt"


def test_structural_splits_oversized_markdown_section_and_repeats_heading() -> None:
    p1 = " ".join(f"alfa{i}" for i in range(15))
    p2 = " ".join(f"beta{i}" for i in range(15))
    md = f"## Długa sekcja\n\n{p1}\n\n{p2}"

    chunks = chunk_structural(md, str(uuid4()), max_chunk_tokens=22)

    assert len(chunks) == 2
    assert chunks[0].text.startswith("## Długa sekcja")
    assert chunks[1].text.startswith("## Długa sekcja")
    assert "alfa0" in chunks[0].text
    assert "beta0" in chunks[1].text


def test_structural_plain_text_splits_by_paragraphs() -> None:
    txt = "Pierwszy akapit o kopiach zapasowych.\n\nDrugi akapit o czasie RTO."
    chunks = chunk_structural(txt, str(uuid4()))

    assert [c.text for c in chunks] == [
        "Pierwszy akapit o kopiach zapasowych.",
        "Drugi akapit o czasie RTO.",
    ]
    assert all("heading" not in c.metadata for c in chunks)


def test_structural_empty_input_returns_empty_list() -> None:
    assert chunk_structural("  \n\n ", str(uuid4())) == []


def test_chunk_documents_accepts_plain_paths_and_produces_valid_uuids(tmp_path: Path) -> None:
    f1 = tmp_path / "a.md"
    f2 = tmp_path / "b.txt"
    f1.write_text("# Sekcja A\nTreść dokumentu A.", encoding="utf-8")
    f2.write_text("Akapit pierwszy.\n\nAkapit drugi.", encoding="utf-8")

    chunks = chunk_documents([str(f1), str(f2)], _structural_config())

    assert len(chunks) == 3
    assert [c.metadata["source"] for c in chunks] == ["a.md", "b.txt", "b.txt"]
    for c in chunks:
        UUID(c.chunk_id)
        UUID(c.document_id)
    assert chunks[1].document_id == chunks[2].document_id
    assert chunks[0].document_id != chunks[1].document_id


def test_chunk_documents_uses_supplied_document_ids(tmp_path: Path) -> None:
    f1 = tmp_path / "doc.txt"
    f1.write_text(" ".join(f"słowo{i}" for i in range(12)), encoding="utf-8")
    known_id = str(uuid4())

    by_kwarg = chunk_documents([str(f1)], _fixed_config(size=6, overlap=2), document_ids=[known_id])
    by_tuple = chunk_documents([(known_id, f1)], _fixed_config(size=6, overlap=2))

    assert len(by_kwarg) == 3
    assert len(by_tuple) == 3
    assert all(c.document_id == known_id for c in by_kwarg)
    assert all(c.document_id == known_id for c in by_tuple)


def test_chunk_documents_attaches_pdf_page_numbers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf_path = tmp_path / "manual.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    fake_reader = SimpleNamespace(
        is_encrypted=False,
        pages=[
            SimpleNamespace(extract_text=lambda: "Treść ze strony pierwszej."),
            SimpleNamespace(extract_text=lambda: "Treść ze strony drugiej."),
        ],
    )
    monkeypatch.setattr(extractor, "PdfReader", lambda _p: fake_reader)
    monkeypatch.setattr(chunker, "extract_pdf_pages", extractor.extract_pdf_pages)

    chunks = chunk_documents([pdf_path], _structural_config())

    assert [c.metadata["page"] for c in chunks] == [1, 2]
    assert all(c.metadata["source"] == "manual.pdf" for c in chunks)


def test_chunk_documents_rejects_mismatched_document_ids(tmp_path: Path) -> None:
    f1 = tmp_path / "a.txt"
    f1.write_text("tekst", encoding="utf-8")

    with pytest.raises(ValueError, match="same length"):
        chunk_documents([f1], _structural_config(), document_ids=[str(uuid4()), str(uuid4())])


def test_structural_splits_oversized_paragraph_by_sentences_and_tokens() -> None:
    # Oversized paragraph with multiple sentences -> sentence packing
    para = "Pierwsze zdanie ma kilka słów. Drugie zdanie ma kolejne słowa. Trzecie zdanie kończy."
    sentence_chunks = chunk_structural(para, str(uuid4()), max_chunk_tokens=10)
    assert len(sentence_chunks) >= 2
    assert all(c.metadata["token_count"] <= 10 for c in sentence_chunks)

    # Single giant sentence with no punctuation -> token slicing fallback
    giant = " ".join(f"tok{i}" for i in range(25))
    sliced_chunks = chunk_structural(giant, str(uuid4()), max_chunk_tokens=10)
    assert len(sliced_chunks) == 3
    assert [c.metadata["token_count"] for c in sliced_chunks] == [10, 10, 5]


def test_structural_handles_headings_only_and_invalid_limit() -> None:
    chunks = chunk_structural("# Tylko nagłówek\n## Podnagłówek", str(uuid4()))
    assert len(chunks) == 1
    assert "Tylko nagłówek" in chunks[0].text

    with pytest.raises(ValueError, match="max_chunk_tokens"):
        chunk_structural("tekst", str(uuid4()), max_chunk_tokens=0)


def test_chunk_documents_skips_empty_files_and_tracks_multipage_pdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty_txt = tmp_path / "empty.txt"
    empty_txt.write_text("   \n\n ", encoding="utf-8")

    empty_pdf = tmp_path / "scan.pdf"
    empty_pdf.write_bytes(b"%PDF-1.4")

    multi_pdf = tmp_path / "multi.pdf"
    multi_pdf.write_bytes(b"%PDF-1.4")

    def fake_reader(path: Path) -> SimpleNamespace:
        if path.name == "scan.pdf":
            return SimpleNamespace(
                is_encrypted=False, pages=[SimpleNamespace(extract_text=lambda: "")]
            )
        return SimpleNamespace(
            is_encrypted=False,
            pages=[
                SimpleNamespace(extract_text=lambda: "alfa beta gamma"),
                SimpleNamespace(extract_text=lambda: "delta epsilon zeta"),
            ],
        )

    monkeypatch.setattr(extractor, "PdfReader", fake_reader)
    monkeypatch.setattr(chunker, "extract_pdf_pages", extractor.extract_pdf_pages)

    chunks = chunk_documents([empty_txt, empty_pdf, multi_pdf], _fixed_config(size=20, overlap=0))

    assert len(chunks) == 1
    assert chunks[0].metadata["page"] == 1
    assert chunks[0].metadata["pages"] == [1, 2]

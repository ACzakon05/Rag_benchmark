"""Weryfikacja spójności wzorcowego zbioru demonstracyjnego (datasets/demo/)."""

from __future__ import annotations

from pathlib import Path

from app.ingestion.chunker import chunk_documents, extract_text
from app.schemas.config import ChunkingStrategy, RetrievalMethod
from app.schemas.experiment import RagConfig
from app.services.dataset_service import parse_testset

DEMO_DIR = Path(__file__).resolve().parents[3] / "datasets" / "demo"
DOC_EXTENSIONS = {".txt", ".md", ".pdf"}


def _demo_documents() -> list[Path]:
    return sorted(
        p for p in DEMO_DIR.iterdir() if p.is_file() and p.suffix.lower() in DOC_EXTENSIONS
    )


def test_demo_meets_mvp_dod_counts() -> None:
    docs = _demo_documents()
    json_questions = parse_testset("testset.json", (DEMO_DIR / "testset.json").read_bytes())
    csv_questions = parse_testset("testset.csv", (DEMO_DIR / "testset.csv").read_bytes())

    assert len(docs) >= 5
    assert len(json_questions) >= 10
    assert json_questions == csv_questions


def test_every_expected_snippet_exists_verbatim_in_demo_documents() -> None:
    corpus = "\n\n".join(extract_text(doc) for doc in _demo_documents())
    questions = parse_testset("testset.json", (DEMO_DIR / "testset.json").read_bytes())

    for idx, q in enumerate(questions, start=1):
        assert q.expected_context_snippet in corpus, (
            f"Pytanie #{idx} ma cytat nieobecny w dokumentach demo: {q.expected_context_snippet!r}"
        )


def test_demo_chunks_cleanly_under_both_strategies() -> None:
    docs = _demo_documents()
    fixed_cfg = RagConfig(
        label="A",
        chunking=ChunkingStrategy.FIXED_TOKENS,
        chunk_size_tokens=128,
        chunk_overlap_tokens=24,
        retrieval=RetrievalMethod.DENSE,
        top_k=4,
        reranking_enabled=False,
    )
    structural_cfg = RagConfig(
        label="B",
        chunking=ChunkingStrategy.STRUCTURAL,
        retrieval=RetrievalMethod.HYBRID,
        top_k=4,
        reranking_enabled=True,
    )

    fixed_chunks = chunk_documents(docs, fixed_cfg)
    structural_chunks = chunk_documents(docs, structural_cfg)

    assert len(fixed_chunks) > len(docs)
    assert len(structural_chunks) > len(docs)

    questions = parse_testset("testset.json", (DEMO_DIR / "testset.json").read_bytes())
    structural_texts = [c.text for c in structural_chunks]
    for q in questions:
        assert any(q.expected_context_snippet in text for text in structural_texts), (
            f"Cytat został rozcięty w chunkingu strukturalnym: {q.expected_context_snippet!r}"
        )

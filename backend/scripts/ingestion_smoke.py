"""Ręczne sprawdzenie modułu ingestion na zbiorze demonstracyjnym datasets/demo/.

Uruchomienie z katalogu backend/:
    PYTHONPATH=. uv run python scripts/ingestion_smoke.py
"""

from __future__ import annotations

from pathlib import Path

from app.ingestion.chunker import chunk_documents
from app.schemas.config import ChunkingStrategy, RetrievalMethod
from app.schemas.experiment import RagConfig
from app.services.dataset_service import parse_testset

DEMO_DIR = Path(__file__).resolve().parents[2] / "datasets" / "demo"


def main() -> None:
    docs = sorted(p for p in DEMO_DIR.iterdir() if p.suffix.lower() in {".md", ".txt", ".pdf"})
    questions = parse_testset("testset.json", (DEMO_DIR / "testset.json").read_bytes())
    print(f"Dokumenty: {len(docs)} | Pytania testowe: {len(questions)}")

    configs = [
        RagConfig(
            label="fixed_128_24",
            chunking=ChunkingStrategy.FIXED_TOKENS,
            chunk_size_tokens=128,
            chunk_overlap_tokens=24,
            retrieval=RetrievalMethod.DENSE,
            top_k=4,
            reranking_enabled=False,
        ),
        RagConfig(
            label="structural",
            chunking=ChunkingStrategy.STRUCTURAL,
            retrieval=RetrievalMethod.HYBRID,
            top_k=4,
            reranking_enabled=True,
        ),
    ]

    for cfg in configs:
        chunks = chunk_documents(docs, cfg)
        avg_tokens = sum(c.metadata.get("token_count", 0) for c in chunks) / max(len(chunks), 1)
        exact_hits = sum(
            any(q.expected_context_snippet in c.text for c in chunks) for q in questions
        )
        print(
            f"\n== {cfg.label}: {len(chunks)} chunków, "
            f"śr. {avg_tokens:.1f} tokenów, "
            f"pełne pokrycie cytatów: {exact_hits}/{len(questions)}"
        )
        for sample in chunks[:3]:
            heading = sample.metadata.get("heading", "-")
            print(
                f"   [{sample.metadata['source']} | {heading}] {sample.text.splitlines()[0][:75]}"
            )


if __name__ == "__main__":
    main()

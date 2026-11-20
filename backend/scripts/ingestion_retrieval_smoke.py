"""Live smoke test: ingestion -> retrieval na datasets/demo/ z prawdziwym Postgres + Ollama.

Uruchomienie z katalogu backend/ (działający Postgres z migracjami + Ollama z nomic-embed-text):
    PYTHONPATH=. uv run python scripts/ingestion_retrieval_smoke.py [--no-rerank]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from uuid import UUID

from app.config import settings
from app.database import SessionLocal
from app.ingestion.chunker import chunk_documents
from app.models import Collection, Dataset, Document
from app.retrieval.retriever import index_chunks, search, warm_up
from app.schemas.config import ChunkingStrategy, RetrievalMethod
from app.schemas.experiment import RagConfig
from app.services.dataset_service import parse_testset

DEMO_DIR = Path(__file__).resolve().parents[2] / "datasets" / "demo"
DOC_EXTENSIONS = {".md", ".txt", ".pdf"}


def _build_configs(with_rerank: bool) -> list[RagConfig]:
    configs = [
        RagConfig(
            label="A (fixed 128 + dense)",
            chunking=ChunkingStrategy.FIXED_TOKENS,
            chunk_size_tokens=128,
            chunk_overlap_tokens=24,
            retrieval=RetrievalMethod.DENSE,
            top_k=3,
            reranking_enabled=False,
        ),
        RagConfig(
            label="B (fixed 128 + hybrid)",
            chunking=ChunkingStrategy.FIXED_TOKENS,
            chunk_size_tokens=128,
            chunk_overlap_tokens=24,
            retrieval=RetrievalMethod.HYBRID,
            top_k=3,
            reranking_enabled=False,
        ),
        RagConfig(
            label="C (structural + hybrid)",
            chunking=ChunkingStrategy.STRUCTURAL,
            retrieval=RetrievalMethod.HYBRID,
            top_k=3,
            reranking_enabled=False,
        ),
    ]
    if with_rerank:
        configs.append(
            RagConfig(
                label="D (structural + hybrid + rerank)",
                chunking=ChunkingStrategy.STRUCTURAL,
                retrieval=RetrievalMethod.HYBRID,
                top_k=3,
                reranking_enabled=True,
            )
        )
    return configs


def _collection_key(cfg: RagConfig) -> tuple[ChunkingStrategy, int | None, int | None]:
    return (cfg.chunking, cfg.chunk_size_tokens, cfg.chunk_overlap_tokens)


def main() -> None:
    with_rerank = "--no-rerank" not in sys.argv
    docs = sorted(
        p for p in DEMO_DIR.iterdir() if p.is_file() and p.suffix.lower() in DOC_EXTENSIONS
    )
    questions = parse_testset("testset.json", (DEMO_DIR / "testset.json").read_bytes())
    configs = _build_configs(with_rerank)

    print(
        f"embedding={settings.embedding_model}  reranker={settings.reranker_model}\n"
        f"docs={len(docs)}  questions={len(questions)}  configs={len(configs)}"
    )

    with SessionLocal() as db:
        dataset = Dataset(name="ingestion-retrieval-smoke")
        doc_rows = [
            Document(filename=p.name, path=str(p), size_bytes=p.stat().st_size) for p in docs
        ]
        dataset.documents.extend(doc_rows)
        db.add(dataset)
        db.flush()

        collections: dict[tuple[ChunkingStrategy, int | None, int | None], UUID] = {}
        for cfg in configs:
            key = _collection_key(cfg)
            if key not in collections:
                col = Collection(
                    dataset_id=dataset.id,
                    chunking=cfg.chunking,
                    chunk_size_tokens=cfg.chunk_size_tokens,
                    chunk_overlap_tokens=cfg.chunk_overlap_tokens,
                    embedding_model=settings.embedding_model,
                )
                db.add(col)
                db.flush()
                collections[key] = col.id

        db.commit()
        dataset_id = dataset.id
        doc_inputs = [(str(row.id), row.path) for row in doc_rows]

    try:
        # 1. Chunking + indeksowanie raz na unikalną kolekcję (ADR-0004)
        chunk_counts: dict[tuple[ChunkingStrategy, int | None, int | None], int] = {}
        for cfg in configs:
            key = _collection_key(cfg)
            if key in chunk_counts:
                continue
            started = time.perf_counter()
            chunks = chunk_documents(doc_inputs, cfg)
            index_chunks(str(collections[key]), chunks)
            elapsed = time.perf_counter() - started
            chunk_counts[key] = len(chunks)
            print(f"Indexed {cfg.chunking.value:<12} -> {len(chunks):2d} chunks in {elapsed:.2f}s")

        # 2. Wyszukiwanie dla wszystkich konfiguracji i wyliczenie Recall@k + MRR
        print(f"\n{'Config':<34} {'Chunks':>6} {'Recall@3':>9} {'MRR':>7} {'Avg ms':>8}")
        print("-" * 68)

        for cfg in configs:
            key = _collection_key(cfg)
            cid = str(collections[key])
            warm_up(cfg)

            recalls: list[float] = []
            mrrs: list[float] = []
            times_ms: list[float] = []
            misses: list[str] = []

            for q in questions:
                started = time.perf_counter()
                results = search(cid, q.question, cfg)
                times_ms.append((time.perf_counter() - started) * 1000)

                needle = q.expected_context_snippet.lower()
                hit_rank = next(
                    (r.rank for r in results if needle in r.chunk.text.lower()),
                    None,
                )
                recalls.append(1.0 if hit_rank else 0.0)
                mrrs.append(1.0 / hit_rank if hit_rank else 0.0)
                if hit_rank is None:
                    misses.append(q.question)

            print(
                f"{cfg.label:<34} {chunk_counts[key]:>6} "
                f"{sum(recalls) / len(recalls):>9.3f} "
                f"{sum(mrrs) / len(mrrs):>7.3f} "
                f"{sum(times_ms) / len(times_ms):>8.1f}"
            )
            for missed in misses:
                print(f"    [MISS] {missed}")
    finally:
        with SessionLocal() as db:
            row = db.get(Dataset, dataset_id)
            if row is not None:
                db.delete(row)
                db.commit()


if __name__ == "__main__":
    main()

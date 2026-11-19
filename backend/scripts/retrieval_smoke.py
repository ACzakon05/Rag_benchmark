"""Ręczne sprawdzenie modułu retrieval na prawdziwej bazie i prawdziwych modelach.

Uruchomienie z katalogu backend/ (baza z migracjami + Ollama z nomic-embed-text):
    PYTHONPATH=. uv run python scripts/retrieval_smoke.py [--no-rerank]
"""

from __future__ import annotations

import sys
import time
from uuid import uuid4

from app.config import settings
from app.database import SessionLocal
from app.models import Collection, Dataset, Document
from app.retrieval.retriever import index_chunks, search
from app.schemas.chunk import DocumentChunk
from app.schemas.config import ChunkingStrategy, RetrievalMethod
from app.schemas.experiment import RagConfig

TEXTS = [
    "Maksymalny limit X wynosi 100 jednostek na dobę.",
    "Reklamacje należy składać w ciągu 14 dni od daty zakupu.",
    "Serwer obsługuje do 500 jednoczesnych połączeń.",
    "Hasło powinno mieć co najmniej 12 znaków i jedną cyfrę.",
    "Kopie zapasowe wykonywane są codziennie o godzinie 2:00.",
    "Dostęp do systemu wymaga uwierzytelnienia dwuskładnikowego.",
]
QUERIES = [
    ("Jaki jest limit X?", TEXTS[0]),
    ("Ile mam czasu na złożenie reklamacji?", TEXTS[1]),
    ("Jak często robione są backupy?", TEXTS[4]),
]


def main() -> None:
    with_rerank = "--no-rerank" not in sys.argv
    print(f"embedding: {settings.embedding_model}  reranker: {settings.reranker_model}")

    with SessionLocal() as db:
        dataset = Dataset(name="smoke")
        document = Document(filename="smoke.txt", path="/dev/null", size_bytes=0)
        dataset.documents.append(document)
        db.add(dataset)
        db.flush()
        collection = Collection(
            dataset_id=dataset.id,
            chunking=ChunkingStrategy.STRUCTURAL,
            chunk_size_tokens=None,
            chunk_overlap_tokens=None,
            embedding_model=settings.embedding_model,
        )
        db.add(collection)
        db.commit()
        dataset_id, collection_id, document_id = dataset.id, collection.id, document.id

    try:
        chunks = [
            DocumentChunk(chunk_id=str(uuid4()), document_id=str(document_id), text=t, position=i)
            for i, t in enumerate(TEXTS)
        ]
        started = time.perf_counter()
        index_chunks(str(collection_id), chunks)
        print(f"index_chunks: {len(chunks)} chunków w {time.perf_counter() - started:.2f}s")

        hits, total = 0, 0
        for retrieval in (RetrievalMethod.DENSE, RetrievalMethod.HYBRID):
            for rerank_on in (False, True) if with_rerank else (False,):
                config = RagConfig(
                    label="smoke",
                    chunking=ChunkingStrategy.STRUCTURAL,
                    retrieval=retrieval,
                    top_k=3,
                    reranking_enabled=rerank_on,
                )
                print(f"\n== {retrieval.value}, rerank={rerank_on}")
                for query, expected in QUERIES:
                    started = time.perf_counter()
                    results = search(str(collection_id), query, config)
                    elapsed = (time.perf_counter() - started) * 1000
                    top = results[0].chunk.text if results else "(brak)"
                    ok = bool(results) and top == expected
                    hits, total = hits + ok, total + 1
                    print(f"  [{'OK' if ok else 'XX'}] {elapsed:7.0f} ms  {query}")
                    for r in results:
                        print(f"        {r.rank}. {r.score:8.4f}  {r.chunk.text[:60]}")
        print(f"\nTrafione na 1. miejscu: {hits}/{total}")
    finally:
        with SessionLocal() as db:
            db.delete(db.get(Dataset, dataset_id))  # kaskadowo usuwa dokumenty, kolekcję, chunki
            db.commit()


if __name__ == "__main__":
    main()

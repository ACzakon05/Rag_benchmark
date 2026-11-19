# ADR-0006: Retrieval design - exact search, in-memory BM25, RRF, lazy reranker

## Context

The retrieval module has to serve four variants (dense, hybrid, each with or without
reranking) on collections of at most a few thousand chunks, from two kinds of processes: the
Celery worker (benchmark) and the API (Playground). ADR-0001 fixed the storage (pgvector,
BM25 in memory) and ADR-0004 the collections; this ADR records the remaining design choices.

## Decision

1. **Exact vector search, no ANN index.** Cosine distance (`<=>`) filtered by `collection_id`.
   An HNSW index combined with a `WHERE` filter can return fewer than `k` rows, and an exact scan
   is fast enough at this scale.
2. **BM25 built in memory** from the collection's chunks (`rank-bm25`, embeddings deferred when
   loading), cached per collection in each process. Collections don't change after indexing, so
   the cache needs no invalidation; an empty collection is never cached.
3. **Reciprocal Rank Fusion with `k = 60`** to merge dense and BM25 rankings. It uses ranks
   only, so the two score scales don't have to be normalised.
4. **Candidate pool of `4 x top_k`** for hybrid search and for reranking, so fusion and the
   reranker have something to choose from. Plain dense search fetches exactly `top_k`.
5. **Reranker loaded lazily, once per process** (`lru_cache`), never at import time (ADR-0005).
   `warm_up()` lets the orchestrator load the models before timing starts.
6. **Model prefixes live in one place** (`embedding.py`): `nomic-embed-text` needs
   `search_document: ` / `search_query: `; other models get no prefix.
7. **Indexing is atomic**: all chunks of a call are embedded in batches and written in one
   transaction, so a failure leaves no half-indexed collection.

## Consequences

- Search time grows linearly with collection size; revisit (ANN or ParadeDB, see ADR-0001) if
  collections reach hundreds of thousands of chunks.
- BM25 has no stemming, which hurts inflected languages such as Polish; a stemmer or a
  multilingual setup is an option once real data is available.
- The first reranked query in a fresh process is slow (model download and load, about a minute
  on first use), so benchmark code should call `warm_up()` first.
- Scores are not comparable between modes; only the order is meaningful.

## Alternatives considered

- **HNSW / IVFFlat index** - faster at scale, but filtered queries may return fewer results and
  add tuning work that the MVP doesn't need.
- **Weighted score fusion** - needs score normalisation that is unstable per query.
- **BM25 in Postgres (`ts_rank`)** - not real BM25 (see ADR-0001).

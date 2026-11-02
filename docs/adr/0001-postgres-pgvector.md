# ADR-0001: PostgreSQL + pgvector as the single database

## Context

The specification (section 5) proposes two separate stores:

- **SQLite + SQLModel** for metadata: datasets, experiments, configs, evaluation results,
  Playground query history,
- **Qdrant** (or ChromaDB) in a separate container for chunk vectors, one collection per config.

That means two technologies to run, two data models to keep in sync (e.g. deleting an
experiment has to clean up both SQLite rows and Qdrant collections), and two APIs for the
team to learn.

## Decision

Use **one database: PostgreSQL with the pgvector extension** (`pgvector/pgvector:pg17`
image) for both relational data and vectors.

Why:

1. **One service to maintain** - one container in Docker Compose, one connection string,
   one volume, one healthcheck.
2. **Easier migrations** - the whole schema, vector table included, is versioned with a
   single SQLAlchemy migration tool (Alembic). No separately managed vector collections.
3. **The team already knows Postgres** - plain SQL and SQLAlchemy instead of learning the
   Qdrant client API; easy debugging with `psql` or any SQL client.

## Consequences

- Vectors live in the chunks table (`vector(768)` for `nomic-embed-text`). A "collection"
  is now just a `collection_id` column, so Person 4's interface stays the same:
  `index_chunks(collection_id, chunks)` / `search(collection_id, query, config)`.
- Chunks, results and metadata can be joined directly (useful for the per-question view),
  and foreign keys with `ON DELETE CASCADE` keep everything consistent.
- Postgres has no native BM25 (`ts_rank` isn't BM25), so **BM25 stays in `rank-bm25`**,
  built in memory from the collection's chunks loaded from the DB. ParadeDB `pg_search`
  is an option later if needed.
- pgvector is slower than dedicated vector DBs at large scale - irrelevant at MVP size
  (thousands of chunks).
- The vector dimension is part of the schema: switching to an embedding model with a
  different dimension needs a migration (`EMBEDDING_DIM` in `.env`).
- The extension must be enabled on init: `CREATE EXTENSION IF NOT EXISTS vector`.

## Alternatives considered

- **SQLite + Qdrant (spec)** - two services, two data models to sync.
- **SQLite + embedded ChromaDB** - no extra container, but still two stores, and SQLite
  handles concurrent writes from the background job + API reads poorly.
- **PostgreSQL + Qdrant** - Postgres is already there, so Qdrant would be a second
  service with no real benefit at MVP scale.

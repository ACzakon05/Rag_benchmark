# ADR-0005: Celery + Redis for background jobs

## Context

An experiment runs for minutes (dozens of LLM calls), so the API has to start it in the
background and return immediately. Local models must be called one at a time, otherwise
parallel requests exhaust GPU memory. The specification asks for a background task queue
but doesn't name one.

## Decision

Run experiments as **Celery** tasks in a separate **worker** process, with **Redis** as the
message broker. The worker processes one task at a time. All experiment state and results
live in PostgreSQL; Celery's result backend isn't used.

Why:

1. **Well known** - the most widely used Python task queue, familiar to the team, with
   plenty of documentation.
2. **Separate process** - long runs and heavy models (reranker) stay out of the API process.
3. **Redis holds no real data** - it only carries "run experiment X" messages, so it needs no
   schema, migrations or backups, and losing it at worst means re-queuing a task.
4. **Room to grow** - Redis can later serve live progress updates or caching.

## Consequences

- Two more containers in Docker Compose: `redis` and `worker` (same image as the backend).
- Modules called by the worker (ingestion, retrieval, evaluation) must be plain synchronous
  functions without import-time side effects.
- If the worker crashes mid-run, the experiment stays marked as running in the database and
  has to be failed or restarted explicitly.

## Alternatives considered

- **Celery with PostgreSQL as the broker** - no Redis, but that transport is experimental
  and polling-based.
- **PostgreSQL-native queue (e.g. procrastinate)** - no Redis, but less familiar.
- **Background task inside the API process** - no extra services, but runs are lost on API
  restart and heavy work competes with request handling.

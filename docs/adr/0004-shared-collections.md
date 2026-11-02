# ADR-0004: Chunk collections shared between configurations

## Context

The specification gives each RAG configuration its own vector collection. A configuration,
however, mixes two kinds of settings:

- **build-time** - chunking strategy, chunk size and overlap, embedding model: they decide
  which chunks and vectors exist,
- **query-time** - retrieval method, k, reranking: they only decide how existing chunks are
  searched.

Typical experiments vary both (e.g. A and C chunk the same way and differ only in reranking),
so a collection per configuration chunks and embeds the same documents several times.
Embedding is the slowest part of indexing.

## Decision

A **collection** is a dataset chunked and embedded with one set of build-time settings.
Configurations hold only the query-time settings and point at a collection. Configurations
with the same build-time settings share one collection, also across experiments on the same
dataset.

## Consequences

- Indexing time drops - an experiment with 4 configurations usually builds 2 collections.
- A later experiment on the same dataset reuses existing collections without re-indexing.
- `collection_id` in the retrieval interface identifies a collection, not a configuration;
  the runner resolves a configuration to its collection.
- Collections outlive experiments: deleting an experiment keeps them, deleting the dataset
  removes them. A collection still referenced by results can't be deleted on its own.

## Alternatives considered

- **A collection per configuration (spec)** - simpler mapping, but repeats chunking and
  embedding for every configuration.

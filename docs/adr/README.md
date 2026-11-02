# Architecture Decision Records

Short notes on architectural decisions: context, decision, consequences.
Where an ADR differs from `SPECIFICATION.md`, the ADR wins.

One file per decision, numbered: `NNNN-short-title.md`. To change a decision,
add a new ADR rather than rewriting an old one.

- [0001 - PostgreSQL + pgvector as the single database](0001-postgres-pgvector.md)
- [0002 - SQLAlchemy + Alembic instead of SQLModel](0002-sqlalchemy-alembic.md)
- [0003 - LiteLLM as the LLM client library](0003-litellm-client.md)
- [0004 - Chunk collections shared between configurations](0004-shared-collections.md)

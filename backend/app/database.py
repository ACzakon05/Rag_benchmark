from collections.abc import Iterator
from datetime import datetime
from enum import Enum
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy import UUID as SQL_UUID
from sqlalchemy import DateTime, MetaData, Text, create_engine, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    declared_attr,
    mapped_column,
    sessionmaker,
)

from app.config import settings
from app.schemas.config import ChunkingStrategy, RetrievalMethod
from app.schemas.experiment import ExperimentStatus

# Matches PostgreSQL's default constraint names, so migrations can drop constraints by name.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
    "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

engine = create_engine(settings.db_uri, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _varchar_enum(enum: type[Enum]) -> SQLEnum:
    # Stored as VARCHAR, not a native PG enum, so adding a value needs no migration.
    return SQLEnum(
        enum, native_enum=False, length=32, values_callable=lambda e: [m.value for m in e]
    )


def _snake_case(name: str) -> str:
    return "".join(f"_{c.lower()}" if c.isupper() and i else c.lower() for i, c in enumerate(name))


class BaseDbModel(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        return _snake_case(cls.__name__)

    type_annotation_map = {
        str: Text,
        UUID: SQL_UUID,
        datetime: DateTime(timezone=True),
        dict[str, Any]: JSONB,
        ChunkingStrategy: _varchar_enum(ChunkingStrategy),
        RetrievalMethod: _varchar_enum(RetrievalMethod),
        ExperimentStatus: _varchar_enum(ExperimentStatus),
    }


def _get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


DbSession = Annotated[Session, Depends(_get_db)]

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseDbModel
from app.mappings import FKDataset, FKExperiment, PrimaryKey, str_32
from app.schemas.config import ChunkingStrategy, RetrievalMethod
from app.schemas.experiment import ExperimentStatus


class Experiment(BaseDbModel):
    id: Mapped[PrimaryKey]
    dataset_id: Mapped[FKDataset]
    status: Mapped[ExperimentStatus] = mapped_column(default=ExperimentStatus.PENDING)
    current_config: Mapped[int] = mapped_column(default=0)
    current_question: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None]

    configs: Mapped[list["RagConfig"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RagConfig.label",
    )


class RagConfig(BaseDbModel):
    """One RAG variant of an experiment. Its id is the `collection_id` of its chunk index."""

    __table_args__ = (UniqueConstraint("experiment_id", "label"),)

    id: Mapped[PrimaryKey]
    experiment_id: Mapped[FKExperiment]
    label: Mapped[str_32]
    chunking: Mapped[ChunkingStrategy]
    chunk_size_tokens: Mapped[int | None]
    chunk_overlap_tokens: Mapped[int | None]
    retrieval: Mapped[RetrievalMethod]
    top_k: Mapped[int]
    reranking_enabled: Mapped[bool]

    experiment: Mapped[Experiment] = relationship(back_populates="configs")

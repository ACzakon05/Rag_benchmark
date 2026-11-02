from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseDbModel
from app.mappings import FKCollectionRef, FKDataset, FKExperiment, PrimaryKey, str_32, str_255
from app.schemas.config import RetrievalMethod
from app.schemas.experiment import ExperimentStatus


class Experiment(BaseDbModel):
    id: Mapped[PrimaryKey]
    dataset_id: Mapped[FKDataset]
    status: Mapped[ExperimentStatus] = mapped_column(default=ExperimentStatus.PENDING)
    error: Mapped[str | None]
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]
    generation_model: Mapped[str_255]
    judge_model: Mapped[str_255]

    configs: Mapped[list["RagConfig"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RagConfig.label",
    )


class RagConfig(BaseDbModel):
    __table_args__ = (UniqueConstraint("experiment_id", "label"),)

    id: Mapped[PrimaryKey]
    experiment_id: Mapped[FKExperiment]
    collection_id: Mapped[FKCollectionRef]
    label: Mapped[str_32]
    retrieval: Mapped[RetrievalMethod]
    top_k: Mapped[int]
    reranking_enabled: Mapped[bool]

    experiment: Mapped[Experiment] = relationship(back_populates="configs")

from sqlalchemy.orm import Mapped, relationship

from app.database import BaseDbModel
from app.mappings import FKDataset, PrimaryKey, str_255


class Dataset(BaseDbModel):
    id: Mapped[PrimaryKey]
    name: Mapped[str_255]

    documents: Mapped[list["Document"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan", passive_deletes=True
    )
    questions: Mapped[list["TestQuestion"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TestQuestion.position",
    )


class Document(BaseDbModel):
    id: Mapped[PrimaryKey]
    dataset_id: Mapped[FKDataset]
    filename: Mapped[str_255]
    path: Mapped[str]
    size_bytes: Mapped[int]

    dataset: Mapped[Dataset] = relationship(back_populates="documents")


class TestQuestion(BaseDbModel):
    __test__ = False

    id: Mapped[PrimaryKey]
    dataset_id: Mapped[FKDataset]
    position: Mapped[int]
    question: Mapped[str]
    ground_truth_answer: Mapped[str]
    expected_context_snippet: Mapped[str]

    dataset: Mapped[Dataset] = relationship(back_populates="questions")

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from app.database import BaseDbModel
from app.mappings import FKChunk, FKQuestionResult, FKRagConfig, FKTestQuestion, PrimaryKey


class QuestionResult(BaseDbModel):
    __table_args__ = (UniqueConstraint("rag_config_id", "question_id"),)

    id: Mapped[PrimaryKey]
    rag_config_id: Mapped[FKRagConfig]
    question_id: Mapped[FKTestQuestion]
    generated_answer: Mapped[str]

    recall_at_k: Mapped[float]
    mrr: Mapped[float]
    answer_correctness: Mapped[float | None]
    faithfulness: Mapped[float | None]
    judge_rationale: Mapped[str | None]

    retrieval_time_ms: Mapped[float]
    generation_time_ms: Mapped[float]
    total_time_ms: Mapped[float]
    prompt_tokens: Mapped[int]
    completion_tokens: Mapped[int]

    retrieved: Mapped[list["RetrievedChunk"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, order_by="RetrievedChunk.rank"
    )


class RetrievedChunk(BaseDbModel):
    __table_args__ = (UniqueConstraint("question_result_id", "rank"),)

    id: Mapped[PrimaryKey]
    question_result_id: Mapped[FKQuestionResult]
    chunk_id: Mapped[FKChunk]
    rank: Mapped[int]
    score: Mapped[float]
    contains_expected_snippet: Mapped[bool]


class PlaygroundQuery(BaseDbModel):
    id: Mapped[PrimaryKey]
    rag_config_id: Mapped[FKRagConfig]
    question: Mapped[str]
    answer: Mapped[str]
    retrieval_time_ms: Mapped[float]
    generation_time_ms: Mapped[float]

from uuid import UUID

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models import Chunk, Collection, Experiment, Question, QuestionResult, RagConfig
from app.models import RetrievedChunk as RetrievedChunkRow
from app.repositories.repositories import CrudRepository
from app.runner.tasks import run_experiment_task
from app.schemas.chunk import DocumentChunk, ScoredChunk
from app.schemas.config import ChunkingStrategy
from app.schemas.evaluation import (
    ConfigAggregateResult,
    ExperimentResults,
    JudgeMetrics,
    RetrievalMetrics,
    SystemMetrics,
)
from app.schemas.evaluation import QuestionResult as QuestionResultSchema
from app.schemas.experiment import (
    ExperimentConfig,
    ExperimentProgress,
    ExperimentRead,
    ExperimentStatus,
)
from app.schemas.experiment import RagConfig as RagConfigSchema
from app.services.dataset_service import dataset_service
from app.services.services import AppService
from app.utils.exceptions import AppError, UnprocessableError

FAKE_EMBEDDING_MODEL = "fake/random"


class QueueUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ExperimentService(AppService[Experiment]):
    def create_and_enqueue(self, db: Session, config: ExperimentConfig) -> ExperimentProgress:
        dataset = dataset_service.get(db, parse_uuid(config.dataset_id, "dataset_id"))
        experiment = Experiment(
            dataset_id=dataset.id,
            status=ExperimentStatus.PENDING,
            generation_model="fake" if settings.fake_runner else settings.generation_model,
            judge_model="fake" if settings.fake_runner else settings.judge_model,
        )
        experiment.configs = [
            RagConfig(
                label=c.label,
                collection_id=self._get_or_create_collection(db, dataset.id, c).id,
                retrieval=c.retrieval,
                top_k=c.top_k,
                reranking_enabled=c.reranking_enabled,
            )
            for c in config.configs
        ]
        experiment = self.create(db, experiment)
        try:
            run_experiment_task.delay(str(experiment.id))
        except Exception as e:
            self.repository.update(
                db,
                experiment,
                {"status": ExperimentStatus.FAILED, "error": "Could not queue the experiment."},
            )
            raise QueueUnavailableError("Task queue is unavailable, try again later.") from e
        return self.get_progress(db, experiment.id)

    def get_read(self, db: Session, experiment_id: UUID) -> ExperimentRead:
        return self._to_read(self.get(db, experiment_id))

    def list_read(self, db: Session) -> list[ExperimentRead]:
        stmt = (
            select(Experiment)
            .options(selectinload(Experiment.configs).selectinload(RagConfig.collection))
            .order_by(Experiment.created_at.desc())
        )
        return [self._to_read(e) for e in db.scalars(stmt).all()]

    def get_progress(self, db: Session, experiment_id: UUID) -> ExperimentProgress:
        """Progress is derived from stored results, so it can never disagree with them."""
        experiment = self.get(db, experiment_id)
        total_questions = _question_count(db, experiment.dataset_id)
        done = _results_per_config(db, experiment.id)
        configs = experiment.configs

        current_config, current_question = 0, 0
        if experiment.status in (ExperimentStatus.RUNNING, ExperimentStatus.COMPLETED):
            for index, rag_config in enumerate(configs, start=1):
                current_config, current_question = index, done.get(rag_config.id, 0)
                if current_question < total_questions:
                    break
        return ExperimentProgress(
            experiment_id=str(experiment.id),
            status=experiment.status,
            current_config=current_config,
            total_configs=len(configs),
            current_question=current_question,
            total_questions=total_questions,
            message=experiment.error,
        )

    def get_results(self, db: Session, experiment_id: UUID) -> ExperimentResults:
        """Returns what's stored so far, so a running experiment gives partial results."""
        experiment = self.get(db, experiment_id)
        labels = {c.id: c.label for c in experiment.configs}
        return ExperimentResults(
            experiment_id=str(experiment.id),
            aggregates=_aggregates(db, experiment.id, labels),
            per_question=_per_question(db, experiment.id, labels),
        )

    def _get_or_create_collection(
        self, db: Session, dataset_id: UUID, config: RagConfigSchema
    ) -> Collection:
        embedding_model = FAKE_EMBEDDING_MODEL if settings.fake_runner else settings.embedding_model
        stmt = select(Collection).where(
            Collection.dataset_id == dataset_id,
            Collection.chunking == config.chunking,
            Collection.chunk_size_tokens.is_not_distinct_from(config.chunk_size_tokens),
            Collection.chunk_overlap_tokens.is_not_distinct_from(config.chunk_overlap_tokens),
            Collection.embedding_model == embedding_model,
        )
        if collection := db.scalars(stmt).first():
            return collection
        collection = Collection(
            dataset_id=dataset_id,
            chunking=config.chunking,
            chunk_size_tokens=config.chunk_size_tokens,
            chunk_overlap_tokens=config.chunk_overlap_tokens,
            embedding_model=embedding_model,
        )
        db.add(collection)
        db.flush()
        return collection

    def _to_read(self, experiment: Experiment) -> ExperimentRead:
        return ExperimentRead(
            experiment_id=str(experiment.id),
            dataset_id=str(experiment.dataset_id),
            status=experiment.status,
            error=experiment.error,
            generation_model=experiment.generation_model,
            judge_model=experiment.judge_model,
            created_at=experiment.created_at,
            started_at=experiment.started_at,
            finished_at=experiment.finished_at,
            configs=[_config_to_schema(c) for c in experiment.configs],
        )


def get_config_by_label(db: Session, experiment_id: UUID, label: str) -> RagConfig | None:
    stmt = select(RagConfig).where(
        RagConfig.experiment_id == experiment_id, RagConfig.label == label
    )
    return db.scalars(stmt).first()


def parse_uuid(value: str, field: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise UnprocessableError([{"field": field, "message": "Must be a UUID."}]) from None


def _config_to_schema(config: RagConfig) -> RagConfigSchema:
    collection = config.collection
    return RagConfigSchema.model_construct(
        label=config.label,
        chunking=ChunkingStrategy(collection.chunking),
        chunk_size_tokens=collection.chunk_size_tokens,
        chunk_overlap_tokens=collection.chunk_overlap_tokens,
        retrieval=config.retrieval,
        top_k=config.top_k,
        reranking_enabled=config.reranking_enabled,
    )


def _question_count(db: Session, dataset_id: UUID) -> int:
    return db.scalar(select(func.count()).where(Question.dataset_id == dataset_id)) or 0


def _results_per_config(db: Session, experiment_id: UUID) -> dict[UUID, int]:
    stmt = (
        select(QuestionResult.rag_config_id, func.count())
        .join(RagConfig, RagConfig.id == QuestionResult.rag_config_id)
        .where(RagConfig.experiment_id == experiment_id)
        .group_by(QuestionResult.rag_config_id)
    )
    return {config_id: count for config_id, count in db.execute(stmt).all()}


def _aggregates(
    db: Session, experiment_id: UUID, labels: dict[UUID, str]
) -> list[ConfigAggregateResult]:
    r = QuestionResult
    stmt = (
        select(
            r.rag_config_id,
            func.avg(r.recall_at_k),
            func.avg(r.mrr),
            func.avg(r.answer_correctness),
            func.avg(r.faithfulness),
            func.avg(r.retrieval_time_ms),
            func.avg(r.total_time_ms),
            func.sum(r.prompt_tokens + r.completion_tokens),
        )
        .join(RagConfig, RagConfig.id == r.rag_config_id)
        .where(RagConfig.experiment_id == experiment_id)
        .group_by(r.rag_config_id)
    )
    rows = sorted(db.execute(stmt).all(), key=lambda row: labels[row[0]])
    return [
        ConfigAggregateResult(
            config_label=labels[config_id],
            retrieval=RetrievalMetrics(recall_at_k=recall, mrr=mrr),
            answer_correctness=correctness,
            faithfulness=faithfulness,
            avg_retrieval_time_ms=retrieval_ms,
            avg_total_time_s=total_ms / 1000,
            total_tokens=tokens,
        )
        for (
            config_id,
            recall,
            mrr,
            correctness,
            faithfulness,
            retrieval_ms,
            total_ms,
            tokens,
        ) in rows
    ]


def _per_question(
    db: Session, experiment_id: UUID, labels: dict[UUID, str]
) -> list[QuestionResultSchema]:
    stmt = (
        select(QuestionResult, Question)
        .join(Question, Question.id == QuestionResult.question_id)
        .join(RagConfig, RagConfig.id == QuestionResult.rag_config_id)
        .where(RagConfig.experiment_id == experiment_id)
        .options(selectinload(QuestionResult.retrieved).selectinload(RetrievedChunkRow.chunk))
        .order_by(Question.position, RagConfig.label)
    )
    return [
        QuestionResultSchema(
            config_label=labels[result.rag_config_id],
            question=question.question,
            ground_truth_answer=question.ground_truth_answer,
            generated_answer=result.generated_answer,
            retrieved_chunks=[_to_scored_chunk(rc) for rc in result.retrieved],
            judge=JudgeMetrics(
                answer_correctness=result.answer_correctness,
                faithfulness=result.faithfulness,
                rationale=result.judge_rationale,
            ),
            system=SystemMetrics(
                retrieval_time_ms=result.retrieval_time_ms,
                total_time_ms=result.total_time_ms,
                tokens_used=result.prompt_tokens + result.completion_tokens,
            ),
        )
        for result, question in db.execute(stmt).all()
    ]


def _to_scored_chunk(retrieved: RetrievedChunkRow) -> ScoredChunk:
    return ScoredChunk(
        chunk=chunk_to_schema(retrieved.chunk),
        score=retrieved.score,
        rank=retrieved.rank,
        contains_expected_snippet=retrieved.contains_expected_snippet,
    )


def chunk_to_schema(chunk: Chunk) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=str(chunk.id),
        document_id=str(chunk.document_id),
        text=chunk.text,
        position=chunk.position,
        metadata=chunk.meta,
    )


experiment_service = ExperimentService(CrudRepository(Experiment))

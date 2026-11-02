from sqlalchemy.orm import Session

from app.models import PlaygroundQuery as PlaygroundQueryRow
from app.runner.playground import answer_query
from app.schemas.playground import PlaygroundQuery, PlaygroundResponse
from app.services.experiment_service import experiment_service, get_config_by_label, parse_uuid
from app.utils.exceptions import ResourceNotFoundError


class PlaygroundService:
    def ask(self, db: Session, query: PlaygroundQuery) -> PlaygroundResponse:
        experiment = experiment_service.get(db, parse_uuid(query.experiment_id, "experiment_id"))
        rag_config = get_config_by_label(db, experiment.id, query.config_label)
        if rag_config is None:
            raise ResourceNotFoundError(
                f"config '{query.config_label}' of experiment", experiment.id
            )

        response = answer_query(db, rag_config, query.question)
        db.add(
            PlaygroundQueryRow(
                rag_config_id=rag_config.id,
                question=query.question,
                answer=response.answer,
                retrieval_time_ms=response.retrieval_time_ms,
                generation_time_ms=response.generation_time_ms,
            )
        )
        db.commit()
        return response


playground_service = PlaygroundService()

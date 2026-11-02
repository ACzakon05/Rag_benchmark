from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.database import BaseDbModel
from app.repositories.repositories import CrudRepository
from app.utils.exceptions import ResourceNotFoundError


class AppService[ModelType: BaseDbModel]:
    def __init__(self, repository: CrudRepository[ModelType]):
        self.repository = repository
        self.name = repository.model.__tablename__

    def get(self, db: Session, object_id: UUID) -> ModelType:
        if (obj := self.repository.get(db, object_id)) is None:
            raise ResourceNotFoundError(self.name, object_id)
        return obj

    def get_all(self, db: Session, *, offset: int = 0, limit: int = 100) -> Sequence[ModelType]:
        return self.repository.get_all(db, offset=offset, limit=limit)

    def create(self, db: Session, obj: ModelType) -> ModelType:
        return self.repository.create(db, obj)

    def update(self, db: Session, object_id: UUID, values: dict[str, Any]) -> ModelType:
        return self.repository.update(db, self.get(db, object_id), values)

    def delete(self, db: Session, object_id: UUID) -> None:
        self.repository.delete(db, self.get(db, object_id))

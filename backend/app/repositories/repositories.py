from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import BaseDbModel


class CrudRepository[ModelType: BaseDbModel]:
    def __init__(self, model: type[ModelType]):
        self.model = model

    def get(self, db: Session, object_id: UUID) -> ModelType | None:
        return db.get(self.model, object_id)

    def get_all(self, db: Session, *, offset: int = 0, limit: int = 100) -> Sequence[ModelType]:
        stmt = select(self.model).order_by(self.model.created_at).offset(offset).limit(limit)
        return db.scalars(stmt).all()

    def create(self, db: Session, obj: ModelType) -> ModelType:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, obj: ModelType, values: dict[str, Any]) -> ModelType:
        for field, value in values.items():
            setattr(obj, field, value)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: ModelType) -> None:
        db.delete(obj)
        db.commit()

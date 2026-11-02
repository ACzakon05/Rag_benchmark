from uuid import UUID

from fastapi import status


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ResourceNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, entity: str, entity_id: UUID | None = None):
        name = entity.replace("_", " ").capitalize()
        super().__init__(f"{name} {entity_id} not found." if entity_id else f"{name} not found.")


class InvalidStateError(AppError):
    status_code = status.HTTP_409_CONFLICT

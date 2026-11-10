"""Concurrency and optimistic locking exceptions."""

from app.shared.errors import AppError


class OptimisticLockError(AppError):
    """Raised when an entity update fails due to a version mismatch (HTTP 412)."""

    def __init__(self, message: str = "Resource modified by another transaction. Version mismatch.") -> None:
        super().__init__(
            message=message,
            code="PRECONDITION_FAILED",
            status_code=412,
        )


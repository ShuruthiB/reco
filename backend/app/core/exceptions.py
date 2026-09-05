from typing import Any


class RecoError(Exception):
    """Base application error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "internal_error",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(RecoError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="not_found", status_code=404, details=details)


class ValidationError(RecoError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="validation_error", status_code=422, details=details)


class ConflictError(RecoError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="conflict", status_code=409, details=details)

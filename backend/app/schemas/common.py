from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str | None = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    database: str
    environment: str


def minor_to_major(amount_minor: int, currency: str = "USD") -> Decimal:
    """Convert minor units to major currency amount."""
    exponent = 3 if currency in {"BHD", "KWD", "OMR"} else 2
    divisor = Decimal(10) ** exponent
    return Decimal(amount_minor) / divisor


def major_to_minor(amount: Decimal | float, currency: str = "USD") -> int:
    exponent = 3 if currency in {"BHD", "KWD", "OMR"} else 2
    multiplier = Decimal(10) ** exponent
    return int(Decimal(str(amount)) * multiplier)

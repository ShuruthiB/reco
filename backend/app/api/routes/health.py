from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import resolve_merchant_id
from app.core.config import settings
from app.db.session import get_db_session
from app.schemas.api import (
    AuditEventResponse,
    BudgetResponse,
    DashboardMetricsResponse,
    DecisionPreviewRequest,
    DecisionPreviewResponse,
    DecisionResponse,
    ExperimentDetailResponse,
    ExperimentSummaryResponse,
    PaymentEventResponse,
    PolicyResponse,
    SimulationRequest,
    SimulationResponse,
    TransactionResponse,
)
from app.schemas.common import HealthResponse, PaginatedResponse
from app.services.domain_services import (
    AuditService,
    BudgetService,
    DashboardService,
    DecisionService,
    ExperimentService,
    PolicyService,
    SimulationService,
    TransactionService,
)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(session: AsyncSession = Depends(get_db_session)) -> HealthResponse:
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"
    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        environment=settings.app_env,
    )

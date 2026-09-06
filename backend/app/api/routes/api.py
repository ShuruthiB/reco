from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_merchant_id
from app.audit.module import AuditModule
from app.audit.writer import AuditWriter
from app.db.session import get_db_session
from app.schemas.api import (
    AuditEventResponse,
    BudgetResponse,
    DashboardMetricsResponse,
    DecisionPreviewRequest,
    DecisionPreviewResponse,
    DecisionResponse,
    ExperimentCreateRequest,
    ExperimentDetailResponse,
    ExperimentSummaryResponse,
    OptimizerRequest,
    OptimizerResponse,
    PaymentEventResponse,
    PolicyCreateRequest,
    PolicyResponse,
    SimulationRequest,
    SimulationResponse,
    TransactionResponse,
)
from app.schemas.common import PaginatedResponse
from app.services import (
    AuditService,
    BudgetService,
    DashboardService,
    DecisionService,
    ExperimentService,
    PolicyService,
    SimulationService,
    TransactionService,
)
from app.api.routes import webhooks

router = APIRouter(prefix="/api", tags=["api"])
router.include_router(webhooks.router, prefix="", tags=["webhooks"])


@router.get("/dashboard/metrics", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> DashboardMetricsResponse:
    return await DashboardService(session).get_metrics(merchant_id)


@router.get("/transactions", response_model=PaginatedResponse[TransactionResponse])
async def list_transactions(
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    status: str | None = Query(default=None),
    failure_reason: str | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> PaginatedResponse[TransactionResponse]:
    return await TransactionService(session).list_transactions(
        merchant_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        status=status,
        failure_reason=failure_reason,
        payment_method=payment_method,
        search=search,
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> TransactionResponse:
    return await TransactionService(session).get_transaction(merchant_id, transaction_id)


@router.get("/transactions/{transaction_id}/events", response_model=list[PaymentEventResponse])
async def get_transaction_events(
    transaction_id: UUID,
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> list[PaymentEventResponse]:
    return await TransactionService(session).get_events(merchant_id, transaction_id)


@router.get("/transactions/{transaction_id}/decisions", response_model=list[DecisionResponse])
async def get_transaction_decisions(
    transaction_id: UUID,
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> list[DecisionResponse]:
    return await DecisionService(session).list_decisions(merchant_id, transaction_id)


@router.get("/decisions", response_model=list[DecisionResponse])
async def get_recent_decisions(
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> list[DecisionResponse]:
    return await DecisionService(session).list_recent_decisions(merchant_id)


@router.post("/decisions/preview", response_model=DecisionPreviewResponse)
async def preview_decision(
    request: DecisionPreviewRequest,
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> DecisionPreviewResponse:
    result = await DecisionService(session).preview_decision(merchant_id, request)
    await AuditModule(AuditWriter(session)).record_preview(merchant_id, request.transaction_id)
    return result


@router.post("/simulations/run", response_model=SimulationResponse)
async def run_simulation(
    request: SimulationRequest,
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> SimulationResponse:
    result = await SimulationService(session).run_simulation(merchant_id, request)
    await AuditModule(AuditWriter(session)).record_simulation(merchant_id)
    return result


@router.post("/experiments", response_model=ExperimentDetailResponse)
async def create_experiment(
    request: ExperimentCreateRequest,
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentDetailResponse:
    return await ExperimentService(session).create_experiment(merchant_id, request)


@router.post("/optimizer/simulate", response_model=OptimizerResponse)
async def simulate_budget_optimizer(
    request: OptimizerRequest,
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> OptimizerResponse:
    from app.engine.optimizer import BudgetOptimizer, OptimizerConstraints
    from app.engine.decision_engine import DecisionEngine
    from app.schemas.api import OptimizerOpportunity
    
    # Get last 50 failed/pending transactions to optimize over
    tx_service = TransactionService(session)
    paginated_txs = await tx_service.list_transactions(merchant_id, page=1, page_size=50)
    
    # Format transactions for optimizer
    tx_list = []
    for tx in paginated_txs.items:
        tx_list.append({
            "transaction_id": str(tx.id),
            "amount": tx.amount,
            "metadata": {
                "risk_profile": tx.risk_level or "medium",
                "state_version": 1,
            }
        })
        
    engine = DecisionEngine(policies={}) # Use default heuristic math
    constraints = OptimizerConstraints(
        total_budget=request.total_budget,
        max_customer_incentive=request.max_customer_incentive,
        max_discount=request.max_discount,
        max_retries=request.max_retries,
        min_confidence=request.min_confidence,
        allowed_interventions=request.allowed_interventions,
    )
    
    optimizer = BudgetOptimizer(constraints, engine)
    result = optimizer.optimize(tx_list)
    
    # Map to schema
    return OptimizerResponse(
        total_budget=result["total_budget"],
        budget_allocated=result["budget_allocated"],
        budget_remaining=result["budget_remaining"],
        top_opportunities=[OptimizerOpportunity(**o.__dict__) for o in result["top_opportunities"]],
        rejected_opportunities=[OptimizerOpportunity(**o.__dict__) for o in result["rejected_opportunities"]],
    )


@router.get("/experiments", response_model=list[ExperimentSummaryResponse])
async def list_experiments(
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> list[ExperimentSummaryResponse]:
    return await ExperimentService(session).list_experiments(merchant_id)


@router.get("/experiments/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(
    experiment_id: UUID,
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> ExperimentDetailResponse:
    return await ExperimentService(session).get_experiment(merchant_id, experiment_id)


@router.get("/budgets", response_model=list[BudgetResponse])
async def list_budgets(
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> list[BudgetResponse]:
    return await BudgetService(session).list_budgets(merchant_id)


@router.get("/policies", response_model=list[PolicyResponse])
async def list_policies(
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> list[PolicyResponse]:
    return await PolicyService(session).list_policies(merchant_id)


@router.post("/policies", response_model=PolicyResponse)
async def create_policy(
    request: PolicyCreateRequest,
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
) -> PolicyResponse:
    return await PolicyService(session).create_policy(merchant_id, request)


@router.get("/audit", response_model=PaginatedResponse[AuditEventResponse])
async def list_audit_events(
    merchant_id: UUID = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
) -> PaginatedResponse[AuditEventResponse]:
    return await AuditService(session).list_audit_events(
        merchant_id,
        action=action,
        entity_type=entity_type,
        page=page,
        page_size=page_size,
        sort_order=sort_order,
    )

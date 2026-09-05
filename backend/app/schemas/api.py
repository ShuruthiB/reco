from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_transaction_id: str
    customer_name: str | None = None
    customer_email: str | None = None
    amount: Decimal
    currency: str
    status: str
    risk_level: str | None = None
    payment_method: str | None = None
    failure_reason: str | None = None
    provider: str = "razorpay"
    created_at: datetime
    last_attempt_at: datetime | None = None


class PaymentEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    amount: Decimal | None = None
    currency: str | None = None
    occurred_at: datetime
    normalized_payload: dict = Field(default_factory=dict)


class DecisionCandidateResponse(BaseModel):
    action: str
    predicted_uplift: Decimal
    expected_revenue: Decimal
    cost: Decimal
    net_contribution: Decimal
    policy_approved: bool
    reject_reason: str | None = None


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transaction_id: UUID
    amount: Decimal
    risk: str | None = None
    recommended_action: str
    confidence: Decimal | None = None
    rationale: str
    policy_version_label: str | None = None
    model_version: str | None = None
    executed: bool
    executed_at: datetime | None = None
    candidates: list[DecisionCandidateResponse] = Field(default_factory=list)


class DashboardMetricsResponse(BaseModel):
    revenue_at_risk: Decimal
    natural_recovery: Decimal
    ai_incremental_revenue: Decimal
    intervention_cost: Decimal
    net_incremental_revenue: Decimal
    recovery_rate: Decimal
    incremental_lift: Decimal
    active_experiments: int
    pending_escalations: int
    currency: str = "USD"


class DecisionPreviewRequest(BaseModel):
    transaction_id: UUID


class DecisionPreviewResponse(BaseModel):
    transaction_id: UUID
    amount: Decimal
    currency: str
    recommended_action: str
    confidence: Decimal
    rationale: str
    policy_version_label: str
    candidates: list[DecisionCandidateResponse]


class SimulationRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    risk_profile: str = Field(default="medium", pattern="^(low|medium|high)$")


class SimulationCandidateResponse(BaseModel):
    name: str
    uplift: Decimal
    cost: Decimal
    net: Decimal
    policy_approved: bool


class SimulationResponse(BaseModel):
    baseline: Decimal
    currency: str
    recommended_action: str
    candidates: list[SimulationCandidateResponse]


class ExperimentArmResponse(BaseModel):
    name: str
    traffic_share: Decimal
    incremental_uplift: Decimal


class ExperimentSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    status: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    arms: list[ExperimentArmResponse]
    total_transactions: int
    incremental_revenue: Decimal
    currency: str = "USD"


class ExperimentDetailResponse(ExperimentSummaryResponse):
    holdout_percentage: Decimal
    eligibility_rules: dict = Field(default_factory=dict)


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    period_type: str
    period_start: datetime
    period_end: datetime
    total_budget: Decimal
    consumed: Decimal
    reserved: Decimal
    remaining: Decimal
    percentage_used: Decimal
    currency: str
    status: str


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    status: str
    last_updated: datetime
    version_label: str | None = None
    rules: list[str] = Field(default_factory=list)


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timestamp: datetime
    type: str
    actor: str
    details: str
    entity_type: str | None = None
    entity_id: UUID | None = None

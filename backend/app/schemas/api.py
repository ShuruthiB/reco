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


class ExperimentCreateRequest(BaseModel):
    name: str
    hypothesis: str | None = None
    eligible_population_rules: dict = Field(default_factory=dict)
    control_percentage: Decimal = Field(ge=0, le=100)
    treatment_action: str
    duration_days: int = Field(gt=0)
    budget_minor: int = Field(ge=0)


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
    total_transactions: int
    control_recovery_rate: Decimal
    treatment_recovery_rate: Decimal
    estimated_lift_points: Decimal
    recovered_gross_value: Decimal
    intervention_cost: Decimal
    net_incremental_contribution: Decimal
    currency: str = "USD"
    has_statistical_significance: bool = False
    control_count: int = 0
    treatment_count: int = 0


class ExperimentDetailResponse(ExperimentSummaryResponse):
    holdout_percentage: Decimal
    eligibility_rules: dict = Field(default_factory=dict)
    arms: list[ExperimentArmResponse] = Field(default_factory=list)


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


class PolicyCreateRequest(BaseModel):
    name: str
    description: str | None = None
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


class OptimizerRequest(BaseModel):
    total_budget: Decimal
    max_customer_incentive: Decimal
    max_discount: Decimal
    max_retries: int
    min_confidence: Decimal
    allowed_interventions: list[str]


class OptimizerOpportunity(BaseModel):
    transaction_id: str
    amount: Decimal
    action: str
    predicted_uplift: Decimal
    expected_incremental_value: Decimal
    intervention_cost: Decimal
    net_incremental_value: Decimal
    roi: Decimal
    rejected: bool
    rejection_reason: str | None = None


class OptimizerResponse(BaseModel):
    total_budget: Decimal
    budget_allocated: Decimal
    budget_remaining: Decimal
    top_opportunities: list[OptimizerOpportunity]
    rejected_opportunities: list[OptimizerOpportunity]

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, default="Asia/Kolkata")
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    external_customer_id: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    consent_status: Mapped[str] = mapped_column(String, nullable=False)
    consent_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contact_count_30d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    external_order_id: Mapped[str] = mapped_column(Text, nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    line_items: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"))
    external_transaction_id: Mapped[str] = mapped_column(Text, nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(Text)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String)
    payment_method: Mapped[str | None] = mapped_column(String)
    state_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer: Mapped[Customer] = relationship("Customer", lazy="joined")


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    webhook_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    provider_event_id: Mapped[str | None] = mapped_column(Text)
    amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str | None] = mapped_column(String(3))
    normalized_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    webhook_event_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    signature_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    processing_status: Mapped[str] = mapped_column(String, nullable=False)
    processing_error: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, nullable=False)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("policy_versions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("policies.id"))
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_label: Mapped[str] = mapped_column(Text, nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    guardrails: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(Text)
    change_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InterventionCandidate(Base):
    __tablename__ = "intervention_candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    intervention_type: Mapped[str] = mapped_column(String, nullable=False)
    intervention_id: Mapped[str] = mapped_column(Text, nullable=False)
    action_id: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility_status: Mapped[str] = mapped_column(String, nullable=False)
    rejection_reasons: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    baseline_recovery_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 7))
    treatment_recovery_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 7))
    predicted_uplift: Mapped[Decimal | None] = mapped_column(Numeric(8, 7))
    expected_incremental_revenue_minor: Mapped[int | None] = mapped_column(BigInteger)
    intervention_cost_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    incentive_cost_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    operational_cost_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    expected_net_contribution_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    model_version: Mapped[str] = mapped_column(Text, nullable=False)
    feature_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    scoring_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    selected_candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("intervention_candidates.id"))
    model_version: Mapped[str] = mapped_column(Text, nullable=False)
    policy_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("policy_versions.id"))
    decision_trigger: Mapped[str] = mapped_column(Text, nullable=False)
    transaction_state_version: Mapped[int] = mapped_column(Integer, nullable=False)
    ranked_candidates: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    feature_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    scoring_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    rationale: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InterventionDecision(Base):
    __tablename__ = "intervention_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    agent_decision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_decisions.id"))
    intervention_candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("intervention_candidates.id"))
    policy_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("policy_versions.id"))
    policy_version_label: Mapped[str] = mapped_column(Text, nullable=False)
    selected_action: Mapped[str] = mapped_column(String, nullable=False)
    intervention_id: Mapped[str | None] = mapped_column(Text)
    action_id: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, nullable=False)
    execution_status: Mapped[str] = mapped_column(String, nullable=False)
    expected_net_contribution_minor: Mapped[int | None] = mapped_column(BigInteger)
    expected_incremental_revenue_minor: Mapped[int | None] = mapped_column(BigInteger)
    total_cost_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    decision_rationale: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    policy_evaluation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_reference: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    candidates: Mapped[list[InterventionCandidate]] = relationship(
        "InterventionCandidate",
        primaryjoin="InterventionDecision.transaction_id == foreign(InterventionCandidate.transaction_id)",
        lazy="selectin",
        viewonly=True,
    )


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, nullable=False)
    holdout_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    arms: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    eligibility_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    experiment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiments.id"))
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    arm_name: Mapped[str] = mapped_column(Text, nullable=False)
    is_holdout: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExperimentOutcome(Base):
    __tablename__ = "experiment_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    experiment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiments.id"))
    experiment_assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiment_assignments.id"))
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    outcome_type: Mapped[str] = mapped_column(String, nullable=False)
    recovered_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    intervention_cost_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    attributed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attribution_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecoveryBudget(Base):
    __tablename__ = "recovery_budgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    period_type: Mapped[str] = mapped_column(String, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    budget_limit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reserved_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    consumed_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    actor_type: Mapped[str] = mapped_column(String, nullable=False)
    actor_id: Mapped[str | None] = mapped_column(Text)
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domain.models import InterventionCandidate, InterventionDecision, Transaction
from app.policies.engine import PolicyEngine
from app.repositories.budget_repository import BudgetRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.mappers import (
    customer_display_name,
    derive_risk_level,
    map_intervention_to_action,
)
from app.schemas.api import (
    AuditEventResponse,
    BudgetResponse,
    DashboardMetricsResponse,
    DecisionCandidateResponse,
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
from app.schemas.common import PaginatedResponse, minor_to_major


def _derive_risk_level(transaction: Transaction) -> str:
    return derive_risk_level(transaction)


def _customer_display_name(customer_email: str | None, external_id: str) -> str:
    return customer_display_name(customer_email, external_id)


def _map_intervention_to_action(intervention_type: str) -> str:
    return map_intervention_to_action(intervention_type)


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TransactionRepository(session)

    def _to_response(self, tx: Transaction) -> TransactionResponse:
        customer = tx.customer
        email = customer.email if customer else None
        external_id = customer.external_customer_id if customer else "unknown"
        return TransactionResponse(
            id=tx.id,
            external_transaction_id=tx.external_transaction_id,
            customer_name=_customer_display_name(email, external_id),
            customer_email=email,
            amount=minor_to_major(tx.amount_minor, tx.currency),
            currency=tx.currency,
            status=tx.status,
            risk_level=_derive_risk_level(tx),
            payment_method=tx.payment_method,
            failure_reason=tx.failure_reason,
            created_at=tx.created_at,
            last_attempt_at=tx.failed_at or tx.updated_at,
        )

    async def list_transactions(
        self,
        merchant_id: UUID,
        **filters,
    ) -> PaginatedResponse[TransactionResponse]:
        page = filters.pop("page", 1)
        page_size = filters.pop("page_size", 20)
        rows, total = await self.repo.list_transactions(
            merchant_id, page=page, page_size=page_size, **filters
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=[self._to_response(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_transaction(self, merchant_id: UUID, transaction_id: UUID) -> TransactionResponse:
        tx = await self.repo.get_by_id(merchant_id, transaction_id)
        if tx is None:
            raise NotFoundError("Transaction not found.", details={"transaction_id": str(transaction_id)})
        return self._to_response(tx)

    async def get_events(self, merchant_id: UUID, transaction_id: UUID) -> list[PaymentEventResponse]:
        tx = await self.repo.get_by_id(merchant_id, transaction_id)
        if tx is None:
            raise NotFoundError("Transaction not found.", details={"transaction_id": str(transaction_id)})
        events = await self.repo.list_events(merchant_id, transaction_id)
        return [
            PaymentEventResponse(
                id=event.id,
                event_type=event.event_type,
                amount=minor_to_major(event.amount_minor, event.currency)
                if event.amount_minor is not None and event.currency
                else None,
                currency=event.currency,
                occurred_at=event.occurred_at,
                normalized_payload=event.normalized_payload,
            )
            for event in events
        ]


class DecisionService:
    def __init__(self, session: AsyncSession) -> None:
        self.tx_repo = TransactionRepository(session)
        self.policy_repo = PolicyRepository(session)
        self.policy_engine = PolicyEngine()

    def _candidate_response(self, candidate: InterventionCandidate) -> DecisionCandidateResponse:
        total_cost = (
            candidate.intervention_cost_minor
            + candidate.incentive_cost_minor
            + candidate.operational_cost_minor
        )
        return DecisionCandidateResponse(
            action=_map_intervention_to_action(candidate.intervention_type),
            predicted_uplift=Decimal(str(candidate.predicted_uplift or 0)),
            expected_revenue=minor_to_major(
                candidate.expected_incremental_revenue_minor or 0, candidate.currency
            ),
            cost=minor_to_major(total_cost, candidate.currency),
            net_contribution=minor_to_major(
                candidate.expected_net_contribution_minor or 0, candidate.currency
            ),
            policy_approved=candidate.eligibility_status == "eligible",
            reject_reason=(
                ", ".join(str(r) for r in candidate.rejection_reasons)
                if candidate.rejection_reasons
                else None
            ),
        )

    def _decision_response(
        self,
        decision: InterventionDecision,
        candidates: list[InterventionCandidate],
        tx: Transaction,
        model_version: str | None,
    ) -> DecisionResponse:
        rationale_text = decision.decision_rationale.get("summary")
        if not rationale_text:
            rationale_text = str(decision.decision_rationale) if decision.decision_rationale else ""
        return DecisionResponse(
            id=decision.id,
            transaction_id=decision.transaction_id,
            amount=minor_to_major(tx.amount_minor, tx.currency),
            risk=_derive_risk_level(tx),
            recommended_action=_map_intervention_to_action(decision.selected_action),
            confidence=Decimal(str(decision.decision_rationale.get("confidence", 0))),
            rationale=rationale_text,
            policy_version_label=decision.policy_version_label,
            model_version=model_version,
            executed=decision.execution_status == "succeeded",
            executed_at=decision.executed_at,
            candidates=[self._candidate_response(c) for c in candidates],
        )

    async def list_decisions(self, merchant_id: UUID, transaction_id: UUID) -> list[DecisionResponse]:
        tx = await self.tx_repo.get_by_id(merchant_id, transaction_id)
        if tx is None:
            raise NotFoundError("Transaction not found.", details={"transaction_id": str(transaction_id)})

        decisions, candidates, agent_decisions = await self.tx_repo.list_decisions(
            merchant_id, transaction_id
        )
        agent_by_tx = {ad.transaction_id: ad for ad in agent_decisions}
        return [
            self._decision_response(
                decision,
                candidates,
                tx,
                agent_by_tx.get(decision.transaction_id).model_version
                if agent_by_tx.get(decision.transaction_id)
                else None,
            )
            for decision in decisions
        ]

    async def preview_decision(
        self, merchant_id: UUID, request: DecisionPreviewRequest
    ) -> DecisionPreviewResponse:
        tx = await self.tx_repo.get_by_id(merchant_id, request.transaction_id)
        if tx is None:
            raise NotFoundError(
                "Transaction not found.", details={"transaction_id": str(request.transaction_id)}
            )

        _, candidates, agent_decisions = await self.tx_repo.list_decisions(
            merchant_id, request.transaction_id
        )
        policy_version = await self.policy_repo.get_active_policy_version(merchant_id)

        if candidates:
            preview_candidates = [self._candidate_response(c) for c in candidates]
            best = max(
                candidates,
                key=lambda c: c.expected_net_contribution_minor or 0,
            )
            recommended = _map_intervention_to_action(best.intervention_type)
            confidence = Decimal(str(best.treatment_recovery_probability or 0))
            rationale = (
                f"Preview based on stored candidates for transaction {tx.external_transaction_id}. "
                f"Highest net contribution: {recommended}."
            )
            policy_label = policy_version.version_label if policy_version else "unknown"
        else:
            preview_candidates, recommended, confidence, rationale, policy_label = (
                await self._build_heuristic_preview(tx, policy_version)
            )

        return DecisionPreviewResponse(
            transaction_id=tx.id,
            amount=minor_to_major(tx.amount_minor, tx.currency),
            currency=tx.currency,
            recommended_action=recommended,
            confidence=confidence,
            rationale=rationale,
            policy_version_label=policy_label,
            candidates=preview_candidates,
        )

    async def _build_heuristic_preview(self, tx: Transaction, policy_version):
        guardrails = policy_version.guardrails if policy_version else {}
        rules = policy_version.rules if policy_version else {}
        policy_label = policy_version.version_label if policy_version else "default-v0"

        risk = _derive_risk_level(tx)
        baseline = {"low": Decimal("0.20"), "medium": Decimal("0.12"), "high": Decimal("0.05")}[risk]

        action_specs = [
            ("do_nothing", "DO_NOTHING", Decimal("0"), 0, 0),
            ("retry_payment", "RETRY", Decimal("0.02"), 50, 0),
            ("send_reminder", "REMINDER_EMAIL", Decimal("0.08"), 1, 0),
            ("offer_incentive", "INCENTIVE_10", Decimal("0.25"), 0, int(tx.amount_minor * 0.10)),
        ]

        preview_candidates: list[DecisionCandidateResponse] = []
        best_action = "DO_NOTHING"
        best_net = Decimal("-1")
        best_confidence = baseline

        contact_count = tx.customer.contact_count_30d if tx.customer else 0
        for intervention_type, action_name, uplift, op_cost, incentive in action_specs:
            eval_result = self.policy_engine.evaluate_candidate(
                intervention_type=intervention_type,
                amount_minor=tx.amount_minor,
                incentive_cost_minor=incentive,
                guardrails=guardrails,
                contact_count_30d=contact_count,
            )
            expected_revenue_minor = int(Decimal(tx.amount_minor) * uplift)
            total_cost = op_cost + incentive
            net_minor = expected_revenue_minor - total_cost
            preview_candidates.append(
                DecisionCandidateResponse(
                    action=action_name,
                    predicted_uplift=uplift,
                    expected_revenue=minor_to_major(expected_revenue_minor, tx.currency),
                    cost=minor_to_major(total_cost, tx.currency),
                    net_contribution=minor_to_major(net_minor, tx.currency),
                    policy_approved=eval_result.approved,
                    reject_reason=eval_result.reject_reason,
                )
            )
            if eval_result.approved and minor_to_major(net_minor, tx.currency) > best_net:
                best_net = minor_to_major(net_minor, tx.currency)
                best_action = action_name
                best_confidence = baseline + uplift

        rationale = (
            f"Heuristic preview for {risk} risk transaction using policy {policy_label}. "
            f"No persisted candidates found; segment baseline recovery {baseline:.0%}."
        )
        _ = rules  # referenced for future enrichment
        return preview_candidates, best_action, best_confidence, rationale, policy_label


class SimulationService:
    def __init__(self, session: AsyncSession) -> None:
        self.policy_repo = PolicyRepository(session)
        self.policy_engine = PolicyEngine()

    async def run_simulation(
        self, merchant_id: UUID, request: SimulationRequest
    ) -> SimulationResponse:
        policy_version = await self.policy_repo.get_active_policy_version(merchant_id)
        guardrails = policy_version.guardrails if policy_version else {}

        historical = await self.policy_repo.get_segment_uplift_stats(
            merchant_id, request.risk_profile
        )

        baseline = Decimal("0.05") if request.risk_profile == "high" else Decimal("0.20")
        if request.risk_profile == "medium":
            baseline = Decimal("0.12")

        if historical:
            baselines = [
                Decimal(str(c.baseline_recovery_probability))
                for c in historical
                if c.baseline_recovery_probability is not None
            ]
            if baselines:
                baseline = sum(baselines) / Decimal(len(baselines))

        amount_minor = int(request.amount * 100)
        specs = [
            ("DO_NOTHING", "do_nothing", Decimal("0"), 0, 0),
            ("RETRY", "retry_payment", Decimal("0.02"), 50, 0),
            ("REMINDER_EMAIL", "send_reminder", Decimal("0.08"), 1, 0),
            ("INCENTIVE_10", "offer_incentive", Decimal("0.25"), 0, int(amount_minor * 0.10)),
            ("INCENTIVE_20", "offer_incentive", Decimal("0.35"), 0, int(amount_minor * 0.20)),
        ]

        if historical:
            uplift_by_type: dict[str, list[Decimal]] = {}
            for row in historical:
                uplift_by_type.setdefault(row.intervention_type, []).append(
                    Decimal(str(row.predicted_uplift or 0))
                )
            specs = [
                (
                    name,
                    it,
                    sum(vals) / Decimal(len(vals)) if (vals := uplift_by_type.get(it, [])) else uplift,
                    op_cost,
                    incentive,
                )
                for name, it, uplift, op_cost, incentive in specs
            ]

        candidates = []
        best_name = "DO_NOTHING"
        best_net = Decimal("-999999")

        for name, intervention_type, uplift, op_cost, incentive in specs:
            eval_result = self.policy_engine.evaluate_candidate(
                intervention_type=intervention_type,
                amount_minor=amount_minor,
                incentive_cost_minor=incentive,
                guardrails=guardrails,
            )
            net_minor = int(Decimal(amount_minor) * uplift) - (op_cost + incentive)
            net = minor_to_major(net_minor, request.currency)
            candidates.append(
                {
                    "name": name,
                    "uplift": uplift,
                    "cost": minor_to_major(op_cost + incentive, request.currency),
                    "net": net,
                    "policy_approved": eval_result.approved,
                }
            )
            if eval_result.approved and net > best_net:
                best_net = net
                best_name = name

        candidates.sort(key=lambda c: c["net"], reverse=True)
        from app.schemas.api import SimulationCandidateResponse

        return SimulationResponse(
            baseline=baseline,
            currency=request.currency,
            recommended_action=best_name,
            candidates=[
                SimulationCandidateResponse(
                    name=c["name"],
                    uplift=c["uplift"],
                    cost=c["cost"],
                    net=c["net"],
                    policy_approved=c["policy_approved"],
                )
                for c in candidates
            ],
        )


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = DashboardRepository(session)

    async def get_metrics(self, merchant_id: UUID) -> DashboardMetricsResponse:
        data = await self.repo.aggregate_metrics(merchant_id)
        currency = data["currency"]
        return DashboardMetricsResponse(
            revenue_at_risk=minor_to_major(data["revenue_at_risk"], currency),
            natural_recovery=minor_to_major(data["natural_recovery"], currency),
            ai_incremental_revenue=minor_to_major(data["ai_incremental_revenue"], currency),
            intervention_cost=minor_to_major(data["intervention_cost"], currency),
            net_incremental_revenue=minor_to_major(data["net_incremental_revenue"], currency),
            recovery_rate=Decimal(str(round(data["recovery_rate"], 4))),
            incremental_lift=Decimal(str(round(data["incremental_lift"], 4))),
            active_experiments=data["active_experiments"],
            pending_escalations=data["pending_escalations"],
            currency=currency,
        )


class ExperimentService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ExperimentRepository(session)

    async def list_experiments(self, merchant_id: UUID) -> list[ExperimentSummaryResponse]:
        experiments = await self.repo.list_experiments(merchant_id)
        results = []
        for exp in experiments:
            results.append(await self._to_summary(exp))
        return results

    async def get_experiment(self, merchant_id: UUID, experiment_id: UUID) -> ExperimentDetailResponse:
        exp = await self.repo.get_by_id(merchant_id, experiment_id)
        if exp is None:
            raise NotFoundError("Experiment not found.", details={"experiment_id": str(experiment_id)})
        summary = await self._to_summary(exp)
        return ExperimentDetailResponse(
            **summary.model_dump(),
            holdout_percentage=Decimal(str(exp.holdout_percentage)),
            eligibility_rules=exp.eligibility_rules or {},
        )

    async def create_experiment(self, merchant_id: UUID, request: 'ExperimentCreateRequest') -> ExperimentDetailResponse:
        from app.domain.models import Experiment
        import uuid
        from datetime import datetime, timezone
        from decimal import Decimal
        
        # Need to dynamically import to avoid circular dep if any
        exp = Experiment(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            name=request.name,
            description=request.hypothesis,
            status="active",
            holdout_percentage=request.control_percentage / Decimal('100.0'),
            arms=[{"name": request.treatment_action, "traffic_share": 1.0 - float(request.control_percentage)/100.0}],
            eligibility_rules=request.eligible_population_rules,
            started_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.repo.session.add(exp)
        await self.repo.session.commit()
        return await self.get_experiment(merchant_id, exp.id)

    async def _to_summary(self, exp) -> ExperimentSummaryResponse:
        from app.schemas.api import ExperimentArmResponse, ExperimentSummaryResponse
        from app.core.utils import minor_to_major
        from decimal import Decimal

        metrics = await self.repo.get_experiment_metrics(exp.id)
        
        control_count = metrics["control_count"]
        treatment_count = metrics["treatment_count"]
        
        control_rate = Decimal(metrics["control_recoveries"]) / Decimal(control_count) if control_count > 0 else Decimal("0")
        treatment_rate = Decimal(metrics["treatment_recoveries"]) / Decimal(treatment_count) if treatment_count > 0 else Decimal("0")
        
        lift = treatment_rate - control_rate
        
        treatment_gross = minor_to_major(metrics["treatment_recovered_amount"], "USD")
        treatment_cost = minor_to_major(metrics["treatment_cost"], "USD")
        
        # Incremental revenue = (Treatment Rate - Control Rate) * Treatment Count * Average Transaction Value
        # For simplicity in this demo, we assume the incremental value is just the lift applied to the gross.
        # A more precise way is taking the actual incremental amount.
        # If control rate was X, expected treatment natural recoveries = X * treatment_count
        # Expected natural gross = (X * treatment_count) * avg_order_value
        # Let's do a simple calculation:
        
        # If they recovered $1000 with a 20% rate, and control had 10% rate, 
        # then half of that $1000 is incremental.
        incremental_gross = treatment_gross * (lift / treatment_rate) if treatment_rate > 0 and lift > 0 else Decimal("0")
        net_contrib = incremental_gross - treatment_cost

        # Statistical significance heuristic (N > 100 per arm)
        has_stat_sig = control_count >= 100 and treatment_count >= 100

        return ExperimentSummaryResponse(
            id=exp.id,
            name=exp.name,
            description=exp.description,
            status="active" if exp.status in ["running", "active"] else exp.status,
            start_date=exp.started_at,
            end_date=exp.ended_at,
            total_transactions=metrics["total_transactions"],
            control_recovery_rate=control_rate,
            treatment_recovery_rate=treatment_rate,
            estimated_lift_points=lift * Decimal("100"), # as percentage points
            recovered_gross_value=treatment_gross,
            intervention_cost=treatment_cost,
            net_incremental_contribution=net_contrib,
            currency="USD",
            has_statistical_significance=has_stat_sig,
            control_count=control_count,
            treatment_count=treatment_count
        )


class BudgetService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = BudgetRepository(session)

    async def list_budgets(self, merchant_id: UUID) -> list[BudgetResponse]:
        budgets = await self.repo.list_budgets(merchant_id)
        responses = []
        for budget in budgets:
            remaining = budget.budget_limit_minor - budget.consumed_minor - budget.reserved_minor
            pct = (
                Decimal(budget.consumed_minor + budget.reserved_minor)
                / Decimal(budget.budget_limit_minor)
                * Decimal(100)
                if budget.budget_limit_minor
                else Decimal(0)
            )
            responses.append(
                BudgetResponse(
                    id=budget.id,
                    name=budget.name,
                    period_type=budget.period_type,
                    period_start=budget.period_start,
                    period_end=budget.period_end,
                    total_budget=minor_to_major(budget.budget_limit_minor, budget.currency),
                    consumed=minor_to_major(budget.consumed_minor, budget.currency),
                    reserved=minor_to_major(budget.reserved_minor, budget.currency),
                    remaining=minor_to_major(max(remaining, 0), budget.currency),
                    percentage_used=pct.quantize(Decimal("0.01")),
                    currency=budget.currency,
                    status=budget.status,
                )
            )
        return responses


class PolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = PolicyRepository(session)
        self.engine = PolicyEngine()

    async def list_policies(self, merchant_id: UUID) -> list[PolicyResponse]:
        rows = await self.repo.list_policies(merchant_id)
        responses = []
        for policy, version in rows:
            rules = self.engine.extract_rule_strings(version.rules if version else {})
            responses.append(
                PolicyResponse(
                    id=policy.id,
                    name=policy.name,
                    description=policy.description,
                    status="active" if policy.status == "active" else "inactive",
                    last_updated=policy.updated_at,
                    version_label=version.version_label if version else None,
                    rules=rules,
                )
            )
        return responses


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        from app.repositories.audit_repository import AuditRepository

        self.repo = AuditRepository(session)

    async def list_audit_events(
        self,
        merchant_id: UUID,
        *,
        action: str | None = None,
        entity_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ) -> PaginatedResponse[AuditEventResponse]:
        rows, total = await self.repo.list_events(
            merchant_id,
            action=action,
            entity_type=entity_type,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        items = [
            AuditEventResponse(
                id=row.id,
                timestamp=row.occurred_at,
                type=row.action,
                actor=f"{row.actor_type} ({row.actor_id or 'system'})",
                details=self._format_details(row),
                entity_type=row.entity_type,
                entity_id=row.entity_id,
            )
            for row in rows
        ]
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def _format_details(row) -> str:
        metadata = row.metadata_ or {}
        if "summary" in metadata:
            return str(metadata["summary"])
        if row.after_state:
            return str(row.after_state)
        return f"{row.action} on {row.entity_type}:{row.entity_id}"

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    Experiment,
    ExperimentAssignment,
    ExperimentOutcome,
    InterventionDecision,
    Transaction,
)


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def aggregate_metrics(self, merchant_id: UUID) -> dict:
        revenue_at_risk = (
            await self.session.execute(
                select(func.coalesce(func.sum(Transaction.amount_minor), 0)).where(
                    Transaction.merchant_id == merchant_id,
                    Transaction.status.in_(("failed", "recovering", "pending")),
                )
            )
        ).scalar_one()

        failed_total = (
            await self.session.execute(
                select(func.count()).select_from(Transaction).where(
                    Transaction.merchant_id == merchant_id,
                    Transaction.status == "failed",
                )
            )
        ).scalar_one()

        recovered_total = (
            await self.session.execute(
                select(func.count()).select_from(Transaction).where(
                    Transaction.merchant_id == merchant_id,
                    Transaction.status == "recovered",
                )
            )
        ).scalar_one()

        natural_recovery = (
            await self.session.execute(
                select(func.coalesce(func.sum(ExperimentOutcome.recovered_amount_minor), 0)).where(
                    ExperimentOutcome.merchant_id == merchant_id,
                    ExperimentOutcome.outcome_type == "natural_recovery",
                )
            )
        ).scalar_one()

        treated_recovery = (
            await self.session.execute(
                select(func.coalesce(func.sum(ExperimentOutcome.recovered_amount_minor), 0)).where(
                    ExperimentOutcome.merchant_id == merchant_id,
                    ExperimentOutcome.outcome_type == "treated_recovery",
                )
            )
        ).scalar_one()

        intervention_cost = (
            await self.session.execute(
                select(func.coalesce(func.sum(ExperimentOutcome.intervention_cost_minor), 0)).where(
                    ExperimentOutcome.merchant_id == merchant_id,
                    ExperimentOutcome.outcome_type == "treated_recovery",
                )
            )
        ).scalar_one()

        active_experiments = (
            await self.session.execute(
                select(func.count()).select_from(Experiment).where(
                    Experiment.merchant_id == merchant_id,
                    Experiment.status == "running",
                )
            )
        ).scalar_one()

        pending_escalations = (
            await self.session.execute(
                select(func.count()).select_from(InterventionDecision).where(
                    InterventionDecision.merchant_id == merchant_id,
                    InterventionDecision.status == "pending",
                )
            )
        ).scalar_one()

        total_attempted = failed_total + recovered_total
        recovery_rate = (recovered_total / total_attempted) if total_attempted else 0

        holdout_recovery = (
            await self.session.execute(
                select(func.coalesce(func.avg(ExperimentOutcome.recovered_amount_minor), 0))
                .select_from(ExperimentOutcome)
                .join(
                    ExperimentAssignment,
                    ExperimentAssignment.id == ExperimentOutcome.experiment_assignment_id,
                )
                .where(
                    ExperimentOutcome.merchant_id == merchant_id,
                    ExperimentAssignment.is_holdout.is_(True),
                )
            )
        ).scalar_one()

        treated_avg = (
            await self.session.execute(
                select(func.coalesce(func.avg(ExperimentOutcome.recovered_amount_minor), 0))
                .select_from(ExperimentOutcome)
                .join(
                    ExperimentAssignment,
                    ExperimentAssignment.id == ExperimentOutcome.experiment_assignment_id,
                )
                .where(
                    ExperimentOutcome.merchant_id == merchant_id,
                    ExperimentAssignment.is_holdout.is_(False),
                    ExperimentOutcome.outcome_type == "treated_recovery",
                )
            )
        ).scalar_one()

        incremental_lift = 0.0
        if holdout_recovery and float(holdout_recovery) > 0:
            incremental_lift = (float(treated_avg) - float(holdout_recovery)) / float(holdout_recovery)

        primary_currency = (
            await self.session.execute(
                select(Transaction.currency)
                .where(Transaction.merchant_id == merchant_id)
                .group_by(Transaction.currency)
                .order_by(func.count().desc())
                .limit(1)
            )
        ).scalar_one_or_none() or "USD"

        return {
            "revenue_at_risk": int(revenue_at_risk),
            "natural_recovery": int(natural_recovery),
            "ai_incremental_revenue": int(treated_recovery),
            "intervention_cost": int(intervention_cost),
            "net_incremental_revenue": int(treated_recovery) - int(intervention_cost),
            "recovery_rate": recovery_rate,
            "incremental_lift": incremental_lift,
            "active_experiments": int(active_experiments),
            "pending_escalations": int(pending_escalations),
            "currency": primary_currency,
        }

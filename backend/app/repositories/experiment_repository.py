from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Experiment, ExperimentAssignment, ExperimentOutcome


class ExperimentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_experiments(self, merchant_id: UUID) -> list[Experiment]:
        stmt = (
            select(Experiment)
            .where(Experiment.merchant_id == merchant_id)
            .order_by(Experiment.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_by_id(self, merchant_id: UUID, experiment_id: UUID) -> Experiment | None:
        stmt = select(Experiment).where(
            Experiment.merchant_id == merchant_id,
            Experiment.id == experiment_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def assignment_count(self, experiment_id: UUID) -> int:
        stmt = select(func.count()).select_from(ExperimentAssignment).where(
            ExperimentAssignment.experiment_id == experiment_id
        )
        return (await self.session.execute(stmt)).scalar_one()

    async def incremental_revenue(self, experiment_id: UUID) -> int:
        treated = (
            await self.session.execute(
                select(func.coalesce(func.sum(ExperimentOutcome.recovered_amount_minor), 0)).where(
                    ExperimentOutcome.experiment_id == experiment_id,
                    ExperimentOutcome.outcome_type == "treated_recovery",
                )
            )
        ).scalar_one()
        natural = (
            await self.session.execute(
                select(func.coalesce(func.sum(ExperimentOutcome.recovered_amount_minor), 0)).where(
                    ExperimentOutcome.experiment_id == experiment_id,
                    ExperimentOutcome.outcome_type == "natural_recovery",
                )
            )
        ).scalar_one()
        return int(treated) - int(natural)

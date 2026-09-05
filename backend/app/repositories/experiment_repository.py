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

    async def get_experiment_metrics(self, experiment_id: UUID) -> dict:
        # Get counts
        total_stmt = select(func.count()).select_from(ExperimentAssignment).where(ExperimentAssignment.experiment_id == experiment_id)
        control_stmt = select(func.count()).select_from(ExperimentAssignment).where(ExperimentAssignment.experiment_id == experiment_id, ExperimentAssignment.is_holdout == True)
        treatment_stmt = select(func.count()).select_from(ExperimentAssignment).where(ExperimentAssignment.experiment_id == experiment_id, ExperimentAssignment.is_holdout == False)
        
        total_tx = (await self.session.execute(total_stmt)).scalar_one()
        control_count = (await self.session.execute(control_stmt)).scalar_one()
        treatment_count = (await self.session.execute(treatment_stmt)).scalar_one()
        
        # Get recoveries
        stmt = (
            select(
                ExperimentAssignment.is_holdout,
                func.count(ExperimentOutcome.id).label('recovery_count'),
                func.sum(ExperimentOutcome.recovered_amount_minor).label('total_recovered'),
                func.sum(ExperimentOutcome.intervention_cost_minor).label('total_cost')
            )
            .select_from(ExperimentAssignment)
            .outerjoin(ExperimentOutcome, ExperimentOutcome.experiment_assignment_id == ExperimentAssignment.id)
            .where(ExperimentAssignment.experiment_id == experiment_id)
            .group_by(ExperimentAssignment.is_holdout)
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        metrics = {
            "total_transactions": total_tx,
            "control_count": control_count,
            "treatment_count": treatment_count,
            "control_recoveries": 0,
            "treatment_recoveries": 0,
            "treatment_recovered_amount": 0,
            "treatment_cost": 0,
        }
        
        for r in rows:
            if r.is_holdout:
                metrics["control_recoveries"] = r.recovery_count or 0
            else:
                metrics["treatment_recoveries"] = r.recovery_count or 0
                metrics["treatment_recovered_amount"] = r.total_recovered or 0
                metrics["treatment_cost"] = r.total_cost or 0
                
        return metrics

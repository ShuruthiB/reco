from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import RecoveryBudget


class BudgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_budgets(self, merchant_id: UUID) -> list[RecoveryBudget]:
        stmt = (
            select(RecoveryBudget)
            .where(RecoveryBudget.merchant_id == merchant_id)
            .order_by(RecoveryBudget.period_start.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.models import (
    AgentDecision,
    Customer,
    InterventionCandidate,
    InterventionDecision,
    PaymentEvent,
    Transaction,
)


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_transactions(
        self,
        merchant_id: UUID,
        *,
        status: str | None = None,
        failure_reason: str | None = None,
        payment_method: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Transaction], int]:
        filters = [Transaction.merchant_id == merchant_id]
        if status:
            filters.append(Transaction.status == status)
        if failure_reason:
            filters.append(Transaction.failure_reason == failure_reason)
        if payment_method:
            filters.append(Transaction.payment_method == payment_method)
        if search:
            pattern = f"%{search.lower()}%"
            filters.append(
                Transaction.external_transaction_id.ilike(pattern)
                | Customer.email.ilike(pattern)
                | Customer.external_customer_id.ilike(pattern)
            )

        count_stmt = (
            select(func.count())
            .select_from(Transaction)
            .join(Customer, Customer.id == Transaction.customer_id)
            .where(*filters)
        )
        total = (await self.session.execute(count_stmt)).scalar_one()

        sort_columns = {
            "created_at": Transaction.created_at,
            "amount_minor": Transaction.amount_minor,
            "status": Transaction.status,
            "failed_at": Transaction.failed_at,
        }
        sort_col = sort_columns.get(sort_by, Transaction.created_at)
        order = sort_col.desc() if sort_order == "desc" else sort_col.asc()

        stmt = (
            select(Transaction)
            .join(Customer, Customer.id == Transaction.customer_id)
            .options(joinedload(Transaction.customer))
            .where(*filters)
            .order_by(order)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).unique().scalars().all()
        return list(rows), total

    async def get_by_id(self, merchant_id: UUID, transaction_id: UUID) -> Transaction | None:
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.customer))
            .where(Transaction.merchant_id == merchant_id, Transaction.id == transaction_id)
        )
        return (await self.session.execute(stmt)).unique().scalar_one_or_none()

    async def list_events(self, merchant_id: UUID, transaction_id: UUID) -> list[PaymentEvent]:
        stmt = (
            select(PaymentEvent)
            .where(
                PaymentEvent.merchant_id == merchant_id,
                PaymentEvent.transaction_id == transaction_id,
            )
            .order_by(PaymentEvent.occurred_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_decisions(
        self, merchant_id: UUID, transaction_id: UUID
    ) -> tuple[list[InterventionDecision], list[InterventionCandidate], list[AgentDecision]]:
        decisions_stmt = (
            select(InterventionDecision)
            .where(
                InterventionDecision.merchant_id == merchant_id,
                InterventionDecision.transaction_id == transaction_id,
            )
            .order_by(InterventionDecision.created_at.desc())
        )
        decisions = list((await self.session.execute(decisions_stmt)).scalars().all())

        candidates_stmt = (
            select(InterventionCandidate)
            .where(
                InterventionCandidate.merchant_id == merchant_id,
                InterventionCandidate.transaction_id == transaction_id,
            )
            .order_by(InterventionCandidate.expected_net_contribution_minor.desc().nullslast())
        )
        candidates = list((await self.session.execute(candidates_stmt)).scalars().all())

        agent_stmt = (
            select(AgentDecision)
            .where(
                AgentDecision.merchant_id == merchant_id,
                AgentDecision.transaction_id == transaction_id,
            )
            .order_by(AgentDecision.created_at.desc())
        )
        agent_decisions = list((await self.session.execute(agent_stmt)).scalars().all())
        return decisions, candidates, agent_decisions

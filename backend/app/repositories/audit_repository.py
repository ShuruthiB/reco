from typing import Any
from uuid import UUID

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_events(
        self,
        merchant_id: UUID,
        *,
        action: str | None = None,
        entity_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ) -> tuple[list[AuditLog], int]:
        filters = [AuditLog.merchant_id == merchant_id]
        if action:
            filters.append(AuditLog.action == action)
        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)

        count_stmt = select(func.count()).select_from(AuditLog).where(*filters)
        total = (await self.session.execute(count_stmt)).scalar_one()

        order_col = AuditLog.occurred_at.desc() if sort_order == "desc" else AuditLog.occurred_at.asc()
        stmt = (
            select(AuditLog)
            .where(*filters)
            .order_by(order_col)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def append(
        self,
        *,
        merchant_id: UUID | None,
        entity_type: str,
        entity_id: UUID,
        action: str,
        actor_type: str = "system",
        actor_id: str | None = None,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self.session.execute(
            insert(AuditLog).values(
                merchant_id=merchant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                actor_type=actor_type,
                actor_id=actor_id,
                before_state=before_state,
                after_state=after_state,
                metadata=metadata or {},
            )
        )

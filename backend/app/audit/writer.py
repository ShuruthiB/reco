from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_repository import AuditRepository


class AuditWriter:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuditRepository(session)

    async def record(
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
        await self.repo.append(
            merchant_id=merchant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_type=actor_type,
            actor_id=actor_id,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata,
        )

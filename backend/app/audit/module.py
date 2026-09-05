from uuid import UUID

from app.audit.writer import AuditWriter


class AuditModule:
    def __init__(self, writer: AuditWriter) -> None:
        self.writer = writer

    async def record_preview(self, merchant_id: UUID, transaction_id: UUID) -> None:
        await self.writer.record(
            merchant_id=merchant_id,
            entity_type="transaction",
            entity_id=transaction_id,
            action="DECISION_PREVIEWED",
            actor_type="api",
            metadata={"summary": f"Decision preview requested for transaction {transaction_id}."},
        )

    async def record_simulation(self, merchant_id: UUID) -> None:
        await self.writer.record(
            merchant_id=merchant_id,
            entity_type="simulation",
            entity_id=merchant_id,
            action="SIMULATION_RUN",
            actor_type="api",
            metadata={"summary": "Intervention simulation executed."},
        )

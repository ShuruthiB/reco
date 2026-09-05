from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import InterventionCandidate, Policy, PolicyVersion


class PolicyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_policies(self, merchant_id: UUID) -> list[tuple[Policy, PolicyVersion | None]]:
        stmt = (
            select(Policy, PolicyVersion)
            .outerjoin(PolicyVersion, PolicyVersion.id == Policy.current_version_id)
            .where(Policy.merchant_id == merchant_id)
            .order_by(Policy.updated_at.desc())
        )
        return list((await self.session.execute(stmt)).all())

    async def get_active_policy_version(self, merchant_id: UUID) -> PolicyVersion | None:
        stmt = (
            select(PolicyVersion)
            .join(Policy, Policy.current_version_id == PolicyVersion.id)
            .where(
                Policy.merchant_id == merchant_id,
                Policy.status == "active",
            )
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_segment_uplift_stats(
        self, merchant_id: UUID, risk_profile: str
    ) -> list[InterventionCandidate]:
        stmt = (
            select(InterventionCandidate)
            .where(
                InterventionCandidate.merchant_id == merchant_id,
                InterventionCandidate.feature_snapshot["risk_profile"].astext == risk_profile,
            )
            .limit(500)
        )
        return list((await self.session.execute(stmt)).scalars().all())

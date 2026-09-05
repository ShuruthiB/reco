from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.db.session import get_db_session
from app.domain.models import Merchant


async def resolve_merchant_id(
    session: AsyncSession,
    header_merchant_id: str | None,
) -> UUID:
    merchant_id_str = header_merchant_id or settings.default_merchant_id
    if not merchant_id_str:
        raise ValidationError(
            "No merchant context available. Set DEFAULT_MERCHANT_ID or X-Merchant-ID header."
        )

    try:
        merchant_uuid = UUID(merchant_id_str)
    except ValueError as exc:
        raise ValidationError("Invalid merchant ID format.") from exc

    result = await session.execute(select(Merchant.id).where(Merchant.id == merchant_uuid))
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Merchant not found.", details={"merchant_id": merchant_id_str})
    return merchant_uuid


async def get_merchant_id(
    session: AsyncSession = Depends(get_db_session),
    x_merchant_id: str | None = Header(default=None, alias="X-Merchant-ID"),
) -> UUID:
    return await resolve_merchant_id(session, x_merchant_id)

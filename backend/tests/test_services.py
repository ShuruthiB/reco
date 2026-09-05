import os
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.domain.models import Merchant, Transaction
from app.schemas.api import DecisionPreviewRequest, SimulationRequest
from app.services.domain_services import (
    DashboardService,
    DecisionService,
    SimulationService,
    TransactionService,
)

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_DB_TESTS", "0") == "1",
    reason="Database tests disabled",
)


@pytest.mark.asyncio
async def test_dashboard_metrics_from_db(db_session):
    merchant = (
        await db_session.execute(select(Merchant).where(Merchant.status == "active").limit(1))
    ).scalar_one_or_none()
    if merchant is None:
        pytest.skip("No seeded merchant found")

    metrics = await DashboardService(db_session).get_metrics(merchant.id)
    assert metrics.currency
    assert metrics.active_experiments >= 0


@pytest.mark.asyncio
async def test_list_transactions_pagination(db_session):
    merchant = (
        await db_session.execute(select(Merchant).where(Merchant.status == "active").limit(1))
    ).scalar_one_or_none()
    if merchant is None:
        pytest.skip("No seeded merchant found")

    result = await TransactionService(db_session).list_transactions(
        merchant.id, page=1, page_size=5
    )
    assert result.page == 1
    assert result.page_size == 5
    assert len(result.items) <= 5


@pytest.mark.asyncio
async def test_transaction_not_found(db_session):
    merchant = (
        await db_session.execute(select(Merchant).where(Merchant.status == "active").limit(1))
    ).scalar_one_or_none()
    if merchant is None:
        pytest.skip("No seeded merchant found")

    with pytest.raises(NotFoundError):
        await TransactionService(db_session).get_transaction(merchant.id, uuid.uuid4())


@pytest.mark.asyncio
async def test_decision_preview_for_existing_transaction(db_session):
    merchant = (
        await db_session.execute(select(Merchant).where(Merchant.status == "active").limit(1))
    ).scalar_one_or_none()
    if merchant is None:
        pytest.skip("No seeded merchant found")

    tx = (
        await db_session.execute(
            select(Transaction).where(Transaction.merchant_id == merchant.id).limit(1)
        )
    ).scalar_one_or_none()
    if tx is None:
        pytest.skip("No seeded transactions found")

    preview = await DecisionService(db_session).preview_decision(
        merchant.id, DecisionPreviewRequest(transaction_id=tx.id)
    )
    assert preview.transaction_id == tx.id
    assert len(preview.candidates) >= 1


@pytest.mark.asyncio
async def test_simulation_run(db_session):
    merchant = (
        await db_session.execute(select(Merchant).where(Merchant.status == "active").limit(1))
    ).scalar_one_or_none()
    if merchant is None:
        pytest.skip("No seeded merchant found")

    result = await SimulationService(db_session).run_simulation(
        merchant.id,
        SimulationRequest(amount=Decimal("500"), currency="USD", risk_profile="high"),
    )
    assert result.baseline >= 0
    assert len(result.candidates) >= 1

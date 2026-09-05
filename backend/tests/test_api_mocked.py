import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.api import (
    TransactionResponse,
    PaymentEventResponse,
    DecisionResponse,
    DecisionPreviewResponse,
    ExperimentSummaryResponse,
    ExperimentDetailResponse,
    BudgetResponse,
)

from httpx import ASGITransport, AsyncClient
import pytest_asyncio
from app.main import app
from app.api.deps import get_merchant_id
from app.db.session import get_db_session

@pytest_asyncio.fixture
async def client_mocked():
    async def override_get_db():
        yield AsyncMock()
    async def override_merchant_id():
        return uuid.uuid4()
    
    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_merchant_id] = override_merchant_id
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.mark.asyncio
@patch("app.api.routes.api.TransactionService")
async def test_get_transaction(mock_service_cls, client_mocked):
    mock_service = mock_service_cls.return_value
    tx_id = uuid.uuid4()
    mock_service.get_transaction = AsyncMock(return_value=TransactionResponse(
        id=tx_id,
        external_transaction_id="ext-123",
        customer_name="John Doe",
        customer_email="john@example.com",
        amount=Decimal("100.00"),
        currency="USD",
        status="pending",
        risk_level="medium",
        payment_method="card",
        created_at="2026-09-05T00:00:00Z",
    ))
    
    response = await client_mocked.get(f"/api/transactions/{tx_id}")
    assert response.status_code == 200
    assert response.json()["external_transaction_id"] == "ext-123"


@pytest.mark.asyncio
@patch("app.api.routes.api.TransactionService")
async def test_get_transaction_events(mock_service_cls, client_mocked):
    mock_service = mock_service_cls.return_value
    tx_id = uuid.uuid4()
    mock_service.get_events = AsyncMock(return_value=[
        PaymentEventResponse(
            id=uuid.uuid4(),
            event_type="payment_failed",
            amount=Decimal("100.00"),
            currency="USD",
            occurred_at="2026-09-05T00:00:00Z",
            normalized_payload={}
        )
    ])
    
    response = await client_mocked.get(f"/api/transactions/{tx_id}/events")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
@patch("app.api.routes.api.DecisionService")
async def test_get_transaction_decisions(mock_service_cls, client_mocked):
    mock_service = mock_service_cls.return_value
    tx_id = uuid.uuid4()
    mock_service.list_decisions = AsyncMock(return_value=[
        DecisionResponse(
            id=uuid.uuid4(),
            transaction_id=tx_id,
            amount=Decimal("100.00"),
            risk="medium",
            recommended_action="RETRY",
            confidence=Decimal("0.85"),
            rationale="Test rationale",
            policy_version_label="v1",
            executed=True,
            candidates=[],
        )
    ])
    
    response = await client_mocked.get(f"/api/transactions/{tx_id}/decisions")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
@patch("app.api.routes.api.AuditModule")
@patch("app.api.routes.api.DecisionService")
async def test_preview_decision(mock_service_cls, mock_audit_module_cls, client_mocked):
    mock_service = mock_service_cls.return_value
    mock_audit = mock_audit_module_cls.return_value
    mock_audit.record_preview = AsyncMock()
    
    tx_id = uuid.uuid4()
    mock_service.preview_decision = AsyncMock(return_value=DecisionPreviewResponse(
        transaction_id=tx_id,
        amount=Decimal("100.00"),
        currency="USD",
        recommended_action="INCENTIVE_10",
        confidence=Decimal("0.9"),
        rationale="Preview logic",
        policy_version_label="v1",
        candidates=[],
    ))
    
    response = await client_mocked.post(
        "/api/decisions/preview",
        json={"transaction_id": str(tx_id)}
    )
    assert response.status_code == 200
    assert response.json()["recommended_action"] == "INCENTIVE_10"
    mock_audit.record_preview.assert_called_once()


@pytest.mark.asyncio
@patch("app.api.routes.api.ExperimentService")
async def test_list_experiments(mock_service_cls, client_mocked):
    mock_service = mock_service_cls.return_value
    mock_service.list_experiments = AsyncMock(return_value=[
        ExperimentSummaryResponse(
            id=uuid.uuid4(),
            name="Test Exp",
            description="Desc",
            status="active",
            start_date="2026-09-01T00:00:00Z",
            arms=[],
            total_transactions=1000,
            incremental_revenue=Decimal("5000.00"),
        )
    ])
    
    response = await client_mocked.get("/api/experiments")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
@patch("app.api.routes.api.ExperimentService")
async def test_get_experiment(mock_service_cls, client_mocked):
    mock_service = mock_service_cls.return_value
    exp_id = uuid.uuid4()
    mock_service.get_experiment = AsyncMock(return_value=ExperimentDetailResponse(
        id=exp_id,
        name="Test Exp",
        description="Desc",
        status="active",
        start_date="2026-09-01T00:00:00Z",
        arms=[],
        total_transactions=1000,
        incremental_revenue=Decimal("5000.00"),
        holdout_percentage=Decimal("0.10"),
        eligibility_rules={}
    ))
    
    response = await client_mocked.get(f"/api/experiments/{exp_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Exp"


@pytest.mark.asyncio
@patch("app.api.routes.api.BudgetService")
async def test_list_budgets(mock_service_cls, client_mocked):
    mock_service = mock_service_cls.return_value
    mock_service.list_budgets = AsyncMock(return_value=[
        BudgetResponse(
            id=uuid.uuid4(),
            name="Monthly Budget",
            period_type="monthly",
            period_start="2026-09-01T00:00:00Z",
            period_end="2026-09-30T23:59:59Z",
            total_budget=Decimal("10000.00"),
            consumed=Decimal("1000.00"),
            reserved=Decimal("500.00"),
            remaining=Decimal("8500.00"),
            percentage_used=Decimal("15.00"),
            currency="USD",
            status="active",
        )
    ])
    
    response = await client_mocked.get("/api/budgets")
    assert response.status_code == 200
    assert len(response.json()) == 1

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Experiment, RecoveryBudget, Policy, PolicyVersion, AuditLog
from datetime import datetime, timezone
from app.services.domain_services import (
    ExperimentService,
    BudgetService,
    PolicyService,
    AuditService,
)

@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.mark.asyncio
@patch("app.services.domain_services.ExperimentRepository")
async def test_experiment_service_list_experiments(mock_repo_cls, mock_session):
    mock_repo = mock_repo_cls.return_value
    merchant_id = uuid.uuid4()
    exp_id = uuid.uuid4()
    
    exp = Experiment(
        id=exp_id,
        merchant_id=merchant_id,
        name="Test Exp",
        description="Desc",
        status="running",
        arms=[{"name": "Control", "traffic_share": 0.5}],
    )
    
    mock_repo.list_experiments = AsyncMock(return_value=[exp])
    mock_repo.assignment_count = AsyncMock(return_value=100)
    mock_repo.incremental_revenue = AsyncMock(return_value=500000)
    
    service = ExperimentService(mock_session)
    result = await service.list_experiments(merchant_id)
    
    assert len(result) == 1
    assert result[0].name == "Test Exp"
    assert result[0].incremental_revenue == Decimal("5000.00")
    assert result[0].total_transactions == 100


@pytest.mark.asyncio
@patch("app.services.domain_services.ExperimentRepository")
async def test_experiment_service_get_experiment(mock_repo_cls, mock_session):
    mock_repo = mock_repo_cls.return_value
    merchant_id = uuid.uuid4()
    exp_id = uuid.uuid4()
    
    exp = Experiment(
        id=exp_id,
        merchant_id=merchant_id,
        name="Test Exp Detail",
        description="Desc",
        status="completed",
        holdout_percentage=0.10,
        arms=[],
        eligibility_rules={}
    )
    
    mock_repo.get_by_id = AsyncMock(return_value=exp)
    mock_repo.assignment_count = AsyncMock(return_value=200)
    mock_repo.incremental_revenue = AsyncMock(return_value=1000000)
    
    service = ExperimentService(mock_session)
    result = await service.get_experiment(merchant_id, exp_id)
    
    assert result.id == exp_id
    assert result.name == "Test Exp Detail"
    assert result.holdout_percentage == Decimal("0.10")


@pytest.mark.asyncio
@patch("app.services.domain_services.BudgetRepository")
async def test_budget_service_list_budgets(mock_repo_cls, mock_session):
    mock_repo = mock_repo_cls.return_value
    merchant_id = uuid.uuid4()
    
    budget = RecoveryBudget(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        name="Monthly Budget",
        period_type="monthly",
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc),
        budget_limit_minor=1000000,
        consumed_minor=100000,
        reserved_minor=50000,
        currency="USD",
        status="active"
    )
    
    mock_repo.list_budgets = AsyncMock(return_value=[budget])
    
    service = BudgetService(mock_session)
    result = await service.list_budgets(merchant_id)
    
    assert len(result) == 1
    assert result[0].name == "Monthly Budget"
    assert result[0].remaining == Decimal("8500.00")
    assert result[0].percentage_used == Decimal("15.00")


@pytest.mark.asyncio
@patch("app.services.domain_services.PolicyRepository")
async def test_policy_service_list_policies(mock_repo_cls, mock_session):
    mock_repo = mock_repo_cls.return_value
    merchant_id = uuid.uuid4()
    
    policy = Policy(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        name="Contact Limit",
        status="active",
        updated_at=datetime.now(timezone.utc),
    )
    version = PolicyVersion(
        id=uuid.uuid4(),
        policy_id=policy.id,
        version_label="v1.0",
        rules={"frequency_cap": {"max_contact_30d": 3}}
    )
    
    mock_repo.list_policies = AsyncMock(return_value=[(policy, version)])
    
    service = PolicyService(mock_session)
    result = await service.list_policies(merchant_id)
    
    assert len(result) == 1
    assert result[0].name == "Contact Limit"
    assert result[0].version_label == "v1.0"
    assert len(result[0].rules) > 0


@pytest.mark.asyncio
@patch("app.repositories.audit_repository.AuditRepository")
async def test_audit_service_list_audit_events(mock_repo_cls, mock_session):
    mock_repo = mock_repo_cls.return_value
    merchant_id = uuid.uuid4()
    
    event = AuditLog(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        action="DECISION_PREVIEWED",
        actor_type="user",
        actor_id="usr-123",
        entity_type="transaction",
        entity_id=str(uuid.uuid4()),
        occurred_at=datetime.now(timezone.utc),
        metadata_={"summary": "Previewed decision"}
    )
    
    mock_repo.list_events = AsyncMock(return_value=([event], 1))
    
    service = AuditService(mock_session)
    result = await service.list_audit_events(merchant_id, page=1, page_size=10)
    
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].type == "DECISION_PREVIEWED"
    assert result.items[0].details == "Previewed decision"

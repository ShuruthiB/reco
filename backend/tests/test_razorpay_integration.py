import pytest
import razorpay
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.services.razorpay_client import RazorpayTestClient
from app.services.action_executor import ActionExecutor

# Mock the environment to ensure safety
@pytest.fixture(autouse=True)
def safe_env(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "razorpay_key_id", "rzp_test_mocked_key")
    monkeypatch.setattr(settings, "razorpay_key_secret", "mocked_secret")

def test_razorpay_client_enforces_test_mode(monkeypatch):
    # Production is blocked
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(RuntimeError, match="CRITICAL SECURITY: Razorpay client cannot run in production mode."):
        RazorpayTestClient()
        
    # Live keys are blocked
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "razorpay_key_id", "rzp_live_mocked_key")
    with pytest.raises(ValueError, match="CRITICAL SECURITY: Only Razorpay test keys"):
        RazorpayTestClient()

@patch('razorpay.Client')
def test_action_executor_creates_order_and_audit_log(mock_razorpay_client_class):
    # Setup mock
    mock_client_instance = MagicMock()
    mock_razorpay_client_class.return_value = mock_client_instance
    
    mock_client_instance.order.create.return_value = {
        "id": "order_mock123",
        "entity": "order",
        "amount": 10000,
        "currency": "USD",
        "receipt": "rcpt_tx-123_dec-456",
        "status": "created"
    }

    # Execute
    client = RazorpayTestClient() # Uses the mocked razorpay.Client internally
    executor = ActionExecutor(razorpay_client=client)
    
    result = executor.execute_action(
        internal_decision_id="dec-456",
        transaction_id="tx-123",
        policy_version="v1.0.0",
        action="RETRY",
        amount_minor=10000,
        currency="USD",
        idempotency_key="idemp_123"
    )
    
    # Assert
    assert result["status"] == "succeeded"
    assert result["external_response"]["id"] == "order_mock123"
    
    # Assert Audit Log
    audit = result["audit_log"]
    assert audit["action"] == "ACTION_EXECUTED"
    assert audit["metadata"]["decision_id"] == "dec-456"
    assert audit["metadata"]["idempotency_key"] == "idemp_123"
    
    # Assert Payment Event
    event = result["payment_event"]
    assert event["event_type"] == "payment.order.created"
    assert event["provider_event_id"] == "order_mock123"
    assert event["amount_minor"] == 10000
    
    # Assert Razorpay was called correctly
    mock_client_instance.order.create.assert_called_once_with(data={
        "amount": 10000,
        "currency": "USD",
        "receipt": "rcpt_tx-123_dec-456",
        "payment_capture": 1
    })

@patch('razorpay.Client')
def test_action_executor_requires_idempotency(mock_razorpay_client_class):
    executor = ActionExecutor()
    with pytest.raises(ValueError, match="Idempotency key is strictly required"):
        executor.execute_action(
            internal_decision_id="dec-456",
            transaction_id="tx-123",
            policy_version="v1.0.0",
            action="RETRY",
            amount_minor=10000,
            currency="USD",
            idempotency_key=""
        )

@patch('razorpay.Client')
def test_action_executor_handles_external_failure_safely(mock_razorpay_client_class):
    mock_client_instance = MagicMock()
    mock_razorpay_client_class.return_value = mock_client_instance
    mock_client_instance.order.create.side_effect = Exception("Razorpay API down")
    
    client = RazorpayTestClient()
    executor = ActionExecutor(razorpay_client=client)
    
    result = executor.execute_action(
        internal_decision_id="dec-456",
        transaction_id="tx-123",
        policy_version="v1.0.0",
        action="RETRY",
        amount_minor=10000,
        currency="USD",
        idempotency_key="idemp_123"
    )
    
    # Should not crash, should return failed status and error
    assert result["status"] == "failed"
    assert result["external_response"]["error"] == "Razorpay API down"
    
    # Audit log should still be recorded!
    assert result["audit_log"]["metadata"]["status"] == "failed"

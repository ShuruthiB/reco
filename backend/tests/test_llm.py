import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch

from openai import APITimeoutError, APIConnectionError
from httpx import Request

from app.llm.explanation_service import ExplanationService, ExplanationContext, AlternativeActionContext

def get_dummy_context() -> ExplanationContext:
    return ExplanationContext(
        transaction_id="tx-123",
        selected_action="DO_NOTHING",
        amount_minor=10000,
        predicted_natural_recovery_prob=0.85,
        estimated_incremental_uplift=0.01,
        expected_incremental_revenue=1.00,
        intervention_cost=5.00,
        final_expected_net_contribution=-4.00,
        alternative_actions=[
            AlternativeActionContext(
                action="RETRY",
                expected_value=-4.00,
                is_valid=True,
                rejection_reasons=[]
            )
        ]
    )

@pytest.fixture
def mock_openai_success():
    mock_response = AsyncMock()
    mock_message = AsyncMock()
    mock_message.content = json.dumps({
        "merchant_facing_explanation": "Decision is DO_NOTHING because cost > revenue.",
        "rejected_alternative_explanation": "RETRY was rejected due to negative net contribution.",
        "customer_facing_message": "Hello customer.",
        "transaction_summary": "Summary.",
        "experiment_summary": "N/A"
    })
    mock_response.choices = [AsyncMock(message=mock_message)]
    
    with patch('app.llm.explanation_service.AsyncOpenAI') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        yield mock_client

@pytest.fixture
def mock_openai_malformed():
    mock_response = AsyncMock()
    mock_message = AsyncMock()
    # Missing required keys
    mock_message.content = json.dumps({"wrong_key": "data"})
    mock_response.choices = [AsyncMock(message=mock_message)]
    
    with patch('app.llm.explanation_service.AsyncOpenAI') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        yield mock_client

@pytest.fixture
def mock_openai_timeout():
    with patch('app.llm.explanation_service.AsyncOpenAI') as mock_client_cls:
        mock_client = mock_client_cls.return_value
        request = Request("POST", "http://test")
        mock_client.chat.completions.create = AsyncMock(side_effect=APITimeoutError(request=request))
        yield mock_client


@pytest.mark.asyncio
async def test_success_case(mock_openai_success):
    service = ExplanationService()
    ctx = get_dummy_context()
    
    response = await service.generate_explanation(ctx)
    
    assert response.merchant_facing_explanation == "Decision is DO_NOTHING because cost > revenue."
    assert response.customer_facing_message == "Hello customer."
    
    # Assert client was called once
    mock_openai_success.chat.completions.create.assert_called_once()
    
    # Verify strict data isolation (only JSON context was passed)
    call_args = mock_openai_success.chat.completions.create.call_args[1]
    messages = call_args["messages"]
    user_prompt = messages[1]["content"]
    assert "tx-123" in user_prompt
    assert "raw database dump" not in user_prompt

@pytest.mark.asyncio
async def test_malformed_response_triggers_retry_and_fallback(mock_openai_malformed):
    # Adjust tenacity settings to speed up tests by mocking sleep
    with patch("tenacity.nap.time.sleep"):
        service = ExplanationService()
        ctx = get_dummy_context()
        
        response = await service.generate_explanation(ctx)
        
        # Should have called it 3 times (initial + 2 retries)
        assert mock_openai_malformed.chat.completions.create.call_count == 3
        
        # Must fall back to safe explanation
        assert "DO_NOTHING" in response.merchant_facing_explanation
        assert "Alternatives were either blocked" in response.rejected_alternative_explanation

@pytest.mark.asyncio
async def test_service_unavailable_triggers_fallback(mock_openai_timeout):
    with patch("tenacity.nap.time.sleep"):
        service = ExplanationService()
        ctx = get_dummy_context()
        
        response = await service.generate_explanation(ctx)
        
        # Timeout should trigger retries, then fallback
        assert mock_openai_timeout.chat.completions.create.call_count == 3
        assert response.transaction_summary.startswith("Tx tx-123 selected DO_NOTHING")

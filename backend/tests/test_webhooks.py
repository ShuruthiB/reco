import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.services.webhook_processor import WebhookProcessor
from app.domain.models import WebhookEvent, Transaction

def test_verify_signature():
    processor = WebhookProcessor(AsyncMock())
    
    with patch("app.core.config.settings.razorpay_webhook_secret", "secret"):
        with patch("razorpay.utility.Utility.verify_webhook_signature") as mock_verify:
            # Valid
            assert processor._verify_signature(b"payload", "valid_sig") is True
            mock_verify.assert_called_with("payload", "valid_sig", "secret")
            
            # Invalid (simulating razorpay throwing SignatureVerificationError)
            import razorpay
            mock_verify.side_effect = razorpay.errors.SignatureVerificationError("Invalid", "sig")
            assert processor._verify_signature(b"payload", "invalid_sig") is False

@pytest.mark.asyncio
async def test_duplicate_delivery():
    mock_session = AsyncMock()
    mock_event = MagicMock(spec=WebhookEvent)
    mock_event.processing_status = "processed"
    
    processor = WebhookProcessor(mock_session)
    # Stub internal fetch
    processor._acquire_or_create_webhook_event = AsyncMock(return_value=mock_event)
    
    with patch.object(processor, '_verify_signature', return_value=True):
        result = await processor.process_razorpay_webhook(b'{"event": "payment.captured"}', "sig", "evt_123")
        
        assert result is True # Safe ignore returns True
        mock_session.commit.assert_not_called() # No DB modifications for duplicates

@pytest.mark.asyncio
async def test_out_of_order_events():
    mock_session = AsyncMock()
    
    mock_event = MagicMock(spec=WebhookEvent)
    mock_event.processing_status = "pending"
    
    processor = WebhookProcessor(mock_session)
    processor._acquire_or_create_webhook_event = AsyncMock(return_value=mock_event)
    
    # Mock finding a transaction that is ALREADY recovered
    mock_tx = MagicMock(spec=Transaction)
    mock_tx.status = "recovered"
    mock_tx.id = "tx-internal"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_tx
    mock_session.execute.return_value = mock_result
    
    with patch.object(processor, '_verify_signature', return_value=True):
        payload = json.dumps({
            "event": "payment.authorized", # An earlier event arriving late
            "payload": {
                "order": {"entity": {"receipt": "rcpt_internalId_decId"}},
                "payment": {"entity": {"id": "pay_123"}}
            }
        })
        
        result = await processor.process_razorpay_webhook(payload.encode(), "sig", "evt_123")
        
        assert result is True
        # Ensure transaction status wasn't modified backward
        assert mock_tx.status == "recovered"

@pytest.mark.asyncio
async def test_downstream_failure_updates_status():
    mock_session = AsyncMock()
    mock_event = MagicMock(spec=WebhookEvent)
    mock_event.processing_status = "pending"
    
    processor = WebhookProcessor(mock_session)
    processor._acquire_or_create_webhook_event = AsyncMock(return_value=mock_event)
    processor._record_failed_webhook = AsyncMock()
    
    # Force _apply_domain_logic to fail
    processor._apply_domain_logic = AsyncMock(side_effect=Exception("DB Deadlock"))
    
    with patch.object(processor, '_verify_signature', return_value=True):
        result = await processor.process_razorpay_webhook(b'{}', "sig", "evt_123")
        
        assert result is False
        mock_session.rollback.assert_called_once()
        processor._record_failed_webhook.assert_called_once_with("evt_123", None, "DB Deadlock")

@pytest.mark.asyncio
async def test_malformed_payload():
    mock_session = AsyncMock()
    processor = WebhookProcessor(mock_session)
    processor._record_failed_webhook = AsyncMock()
    
    with patch.object(processor, '_verify_signature', return_value=True):
        result = await processor.process_razorpay_webhook(b'NOT JSON', "sig", "evt_123")
        
        assert result is False
        processor._record_failed_webhook.assert_called_once_with("evt_123", "{}", "Malformed JSON payload")

import json
import logging
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import razorpay
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.domain.models import WebhookEvent, Transaction, PaymentEvent

logger = logging.getLogger(__name__)

class WebhookProcessor:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _verify_signature(self, raw_body: bytes, signature: str) -> bool:
        if not signature or not settings.razorpay_webhook_secret:
            return False
        
        try:
            client = razorpay.Client(auth=("dummy", "dummy")) # Just for utility access
            # The utility verifies the signature mathematically
            client.utility.verify_webhook_signature(
                raw_body.decode('utf-8'),
                signature,
                settings.razorpay_webhook_secret
            )
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
            
    async def process_razorpay_webhook(self, raw_body: bytes, signature: str, event_id: str) -> bool:
        """
        Main entry point for webhook processing. 
        Returns True if successful or safely ignored (e.g. duplicate).
        Raises ValueError for bad signatures.
        """
        logger.info(f"Received Razorpay webhook event {event_id}")
        
        if not self._verify_signature(raw_body, signature):
            logger.error(f"Invalid Razorpay signature for event {event_id}")
            raise ValueError("Invalid webhook signature")
            
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.error(f"Malformed JSON in webhook event {event_id}")
            # Still attempt to record the bad payload event if we can't parse it
            await self._record_failed_webhook(event_id, "{}", "Malformed JSON payload")
            return False
            
        # 1. Idempotency Check & Atomic Storage
        event = await self._acquire_or_create_webhook_event(event_id, payload, raw_body)
        
        if event.processing_status == "processed":
            logger.info(f"Webhook {event_id} already processed. Ignoring duplicate delivery.")
            return True
            
        if event.processing_status == "processing":
            logger.warning(f"Webhook {event_id} is currently being processed by another worker or failed mid-flight.")
            # Depending on infrastructure, we might return 429 or simply wait. For now, we abort and let Razorpay retry.
            return False

        # Mark as processing
        event.processing_status = "processing"
        await self.session.commit()
        
        # 2. Process Downstream Domain State
        try:
            await self._apply_domain_logic(payload)
            event.processing_status = "processed"
            event.processed_at = datetime.now(timezone.utc)
            event.processing_error = None
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to process webhook {event_id} downstream: {str(e)}")
            await self.session.rollback() # Rollback domain changes
            
            # Re-fetch event and mark failed so it can be retried safely
            await self._record_failed_webhook(event_id, None, str(e))
            return False
            
    async def _acquire_or_create_webhook_event(self, event_id: str, payload: dict, raw_body: bytes) -> WebhookEvent:
        payload_hash = hashlib.sha256(raw_body).hexdigest()
        
        # Try to fetch existing
        stmt = select(WebhookEvent).where(WebhookEvent.webhook_event_id == event_id).with_for_update()
        result = await self.session.execute(stmt)
        event = result.scalar_one_or_none()
        
        if event:
            return event
            
        # Create new
        event = WebhookEvent(
            id=uuid.uuid4(),
            merchant_id=settings.default_merchant_id or uuid.uuid4(), # Using dummy or default for now
            webhook_event_id=event_id,
            provider="razorpay",
            event_type=payload.get("event", "unknown"),
            payload_hash=payload_hash,
            raw_payload=payload,
            signature_verified=True,
            processing_status="pending",
            received_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.session.add(event)
        try:
            await self.session.commit()
        except IntegrityError:
            # Race condition: another worker inserted it. Fetch it.
            await self.session.rollback()
            result = await self.session.execute(stmt)
            event = result.scalar_one_or_none()
            
        return event
        
    async def _record_failed_webhook(self, event_id: str, raw_str: Optional[str], error_msg: str):
        stmt = select(WebhookEvent).where(WebhookEvent.webhook_event_id == event_id)
        result = await self.session.execute(stmt)
        event = result.scalar_one_or_none()
        
        if not event:
             event = WebhookEvent(
                id=uuid.uuid4(),
                merchant_id=uuid.uuid4(),
                webhook_event_id=event_id,
                provider="razorpay",
                event_type="unknown",
                payload_hash="unknown",
                raw_payload={"raw": raw_str} if raw_str else {},
                signature_verified=False,
                processing_status="failed",
                processing_error=error_msg,
                received_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
             self.session.add(event)
        else:
            event.processing_status = "failed"
            event.processing_error = error_msg
            event.updated_at = datetime.now(timezone.utc)
            
        await self.session.commit()
        
    async def _apply_domain_logic(self, payload: dict):
        event_type = payload.get("event")
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})
        
        provider_payment_id = payment_entity.get("id")
        receipt = order_entity.get("receipt") # e.g. rcpt_tx-123_dec-456
        
        if not receipt:
            # Cannot link back to internal transaction
            return
            
        # Parse receipt for internal transaction ID
        parts = receipt.split("_")
        if len(parts) >= 2:
            internal_tx_id = parts[1]
        else:
            return
            
        # Fetch target transaction
        stmt = select(Transaction).where(Transaction.external_transaction_id == internal_tx_id).with_for_update()
        result = await self.session.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            logger.warning(f"Transaction {internal_tx_id} not found for webhook {payload.get('event')}")
            return
            
        # 3. Handle Out-Of-Order Events
        terminal_states = ["recovered", "abandoned"]
        if transaction.status in terminal_states:
            logger.info(f"Transaction {transaction.id} already in terminal state {transaction.status}. Ignoring non-terminal webhook {event_type}.")
            # Important: We do not throw an error. We want the webhook marked as processed so Razorpay stops retrying.
            return
            
        # 4. State Transitions (Idempotent)
        if event_type == "payment.captured" or event_type == "payment.authorized":
            transaction.status = "recovered"
            transaction.recovered_at = datetime.now(timezone.utc)
            transaction.provider_payment_id = provider_payment_id
        elif event_type == "payment.failed":
            # Just record failure, do not transition status out of recovering yet unless policy dictates
            transaction.failure_reason = payment_entity.get("error_description", "Unknown error")
            
        transaction.updated_at = datetime.now(timezone.utc)
        
        # 5. Record Payment Event
        payment_event = PaymentEvent(
            id=uuid.uuid4(),
            merchant_id=transaction.merchant_id,
            transaction_id=transaction.id,
            event_type=event_type,
            provider_event_id=provider_payment_id,
            amount_minor=payment_entity.get("amount", 0),
            currency=payment_entity.get("currency", "USD"),
            normalized_payload=payload,
            occurred_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.session.add(payment_event)

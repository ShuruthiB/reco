import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.services.razorpay_client import RazorpayTestClient

logger = logging.getLogger(__name__)

class ActionExecutor:
    """
    The sole authority for executing external actions.
    The LLM is strictly prohibited from executing actions.
    """
    def __init__(self, razorpay_client: Optional[RazorpayTestClient] = None):
        self.razorpay_client = razorpay_client or RazorpayTestClient()
        # In a real app, we would inject a database session / repository here to save logs.
        # For this integration, we will return the generated internal events.
        
    def execute_action(
        self,
        internal_decision_id: str,
        transaction_id: str,
        policy_version: str,
        action: str,
        amount_minor: int,
        currency: str,
        idempotency_key: str
    ) -> Dict[str, Any]:
        """
        Executes an approved action securely.
        """
        logger.info(f"Executing action {action} for tx {transaction_id} (Decision: {internal_decision_id})")
        
        # 1. Ensure idempotency (Mock check - assume not executed if we reach here)
        if not idempotency_key:
            raise ValueError("Idempotency key is strictly required for external execution.")
            
        external_response = None
        status = "failed"
        
        # 2. Execute via Razorpay Service
        try:
            if action in ["RETRY", "ALTERNATIVE_METHOD", "INCENTIVE"]:
                # E.g. We generate a new order for the customer to pay against
                receipt = f"rcpt_{transaction_id[:8]}_{internal_decision_id[:8]}"
                
                # Deduct incentive from amount if applicable
                if action == "INCENTIVE":
                    amount_minor = int(amount_minor * 0.90) # 10% discount example
                    
                external_response = self.razorpay_client.create_test_order(
                    amount_minor=amount_minor, 
                    currency=currency, 
                    receipt_id=receipt
                )
                status = "succeeded"
            elif action == "DO_NOTHING":
                status = "succeeded"
            else:
                status = "ignored" # Unsupported action for external exec
        except Exception as e:
            logger.error(f"External execution failed for {transaction_id}: {str(e)}")
            status = "failed"
            external_response = {"error": str(e)}

        # 3. Create Audit Log
        audit_log = {
            "id": str(uuid.uuid4()),
            "entity_type": "transaction",
            "entity_id": transaction_id,
            "action": "ACTION_EXECUTED",
            "actor_type": "system",
            "metadata": {
                "decision_id": internal_decision_id,
                "policy_version": policy_version,
                "executed_action": action,
                "idempotency_key": idempotency_key,
                "status": status
            },
            "occurred_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 4. Create Internal Payment Event
        payment_event = {
            "id": str(uuid.uuid4()),
            "transaction_id": transaction_id,
            "event_type": "payment.order.created" if status == "succeeded" and external_response else "payment.failed",
            "provider_event_id": external_response.get("id") if external_response else None,
            "amount_minor": amount_minor,
            "currency": currency,
            "occurred_at": datetime.now(timezone.utc).isoformat()
        }
        
        return {
            "status": status,
            "external_response": external_response,
            "audit_log": audit_log,
            "payment_event": payment_event
        }

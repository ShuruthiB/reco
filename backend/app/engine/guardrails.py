from typing import Any, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class GuardrailResult:
    is_valid: bool
    rejection_reason: str | None = None


class GuardrailsEvaluator:
    def __init__(self, policies: Dict[str, Any]):
        """
        Initialize with merchant specific policy configuration.
        Expected policies schema:
        {
            "max_retries": int,
            "max_incentive_pct": float,
            "allow_incentives": bool,
            "blocked_actions": list[str],
            "fraud_score_threshold": float,
            "min_confidence": float
        }
        """
        self.max_retries = policies.get("max_retries", 3)
        self.max_incentive_pct = policies.get("max_incentive_pct", 20.0)
        self.allow_incentives = policies.get("allow_incentives", True)
        self.blocked_actions = set(policies.get("blocked_actions", []))
        self.fraud_score_threshold = policies.get("fraud_score_threshold", 0.8)
        self.min_confidence = policies.get("min_confidence", 0.5)

    def evaluate(self, candidate_action: str, transaction_metadata: Dict[str, Any], incentive_pct: float = 0.0, confidence: float = 1.0) -> GuardrailResult:
        if candidate_action == "DO_NOTHING":
            return GuardrailResult(is_valid=True)

        # 1. Suspicious/fraud-risk block
        fraud_score = transaction_metadata.get("fraud_score", 0.0)
        if fraud_score > self.fraud_score_threshold:
            return GuardrailResult(is_valid=False, rejection_reason="Transaction blocked due to high fraud risk.")

        # 2. Customer opt-out check
        opt_out = transaction_metadata.get("customer_opt_out", False)
        if opt_out and candidate_action in ["REMINDER", "INCENTIVE"]:
            return GuardrailResult(is_valid=False, rejection_reason="Customer opted out of communications.")

        # 3. Blocked actions check
        if candidate_action in self.blocked_actions:
            return GuardrailResult(is_valid=False, rejection_reason=f"Action '{candidate_action}' is globally blocked.")

        # 4. Repeated failure block / Maximum retries
        retry_count = transaction_metadata.get("retry_count", 0)
        if candidate_action == "RETRY" and retry_count >= self.max_retries:
            return GuardrailResult(is_valid=False, rejection_reason=f"Maximum retries ({self.max_retries}) exceeded.")

        # 5. Maximum incentive / discount percentage check
        if candidate_action == "INCENTIVE":
            if not self.allow_incentives:
                return GuardrailResult(is_valid=False, rejection_reason="Incentives are currently disabled.")
            if incentive_pct > self.max_incentive_pct:
                return GuardrailResult(is_valid=False, rejection_reason=f"Incentive {incentive_pct}% exceeds maximum {self.max_incentive_pct}%.")

        # 6. Low-confidence escalation (If action is anything but ESCALATE, and confidence is low, we might block it or prefer ESCALATE)
        if candidate_action != "ESCALATE" and confidence < self.min_confidence:
            return GuardrailResult(is_valid=False, rejection_reason=f"Confidence {confidence:.2f} is below minimum {self.min_confidence} for automated action.")

        # 7. Transaction state validation
        tx_status = transaction_metadata.get("status", "failed")
        if tx_status in ["recovered", "success"]:
            return GuardrailResult(is_valid=False, rejection_reason="Transaction is already successful or recovered.")

        return GuardrailResult(is_valid=True)

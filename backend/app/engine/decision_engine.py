import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List
from dataclasses import dataclass, field

from app.engine.guardrails import GuardrailsEvaluator


@dataclass
class ActionCandidate:
    action: str
    predicted_uplift: Decimal
    intervention_cost: Decimal
    confidence: Decimal
    expected_value: Decimal = Decimal('0.0')
    is_valid: bool = True
    rejection_reasons: List[str] = field(default_factory=list)


@dataclass
class EngineDecision:
    transaction_id: str
    selected_action: str
    expected_value: Decimal
    predicted_uplift: Decimal
    intervention_cost: Decimal
    confidence: Decimal
    model_version: str
    policy_version: str
    alternative_actions: List[Dict[str, Any]]
    rejection_reasons: List[str]
    created_at: str


# Mathematical Formulas
def natural_recovery_value(amount: Decimal, risk_profile: str, state_version: int) -> Decimal:
    """Calculates the probability of natural recovery without intervention."""
    base_prob = {
        "low": Decimal("0.20"),
        "medium": Decimal("0.10"),
        "high": Decimal("0.02")
    }.get(risk_profile, Decimal("0.05"))
    
    # Degrades over state_version (e.g. number of failures)
    degradation = Decimal("0.8") ** (state_version - 1)
    prob = base_prob * degradation
    return amount * prob


def incremental_recovery_value(amount: Decimal, predicted_uplift: Decimal) -> Decimal:
    """Calculates the gross incremental revenue from an intervention."""
    return amount * predicted_uplift


def intervention_cost(action_type: str, amount: Decimal, discount_pct: float) -> Decimal:
    """Calculates the total cost (operational + incentive) of an intervention."""
    base_op_cost = {
        "RETRY": Decimal("0.50"),
        "ALTERNATIVE_METHOD": Decimal("0.50"),
        "REMINDER": Decimal("0.05"),
        "INCENTIVE": Decimal("0.20"),
        "ESCALATE": Decimal("5.00"),
        "DO_NOTHING": Decimal("0.00")
    }.get(action_type, Decimal("0.00"))
    
    incentive_cost = Decimal("0.00")
    if action_type == "INCENTIVE":
        incentive_cost = amount * (Decimal(str(discount_pct)) / Decimal("100.0"))
        
    return base_op_cost + incentive_cost


def expected_incremental_revenue(incremental_recovery: Decimal, risk_adj: Decimal) -> Decimal:
    """Calculates expected revenue adjusted for risk."""
    return incremental_recovery * risk_adj


def expected_net_contribution(expected_revenue: Decimal, cost: Decimal) -> Decimal:
    """Calculates final net contribution after costs."""
    return expected_revenue - cost


def risk_adjustment(risk_level: str, fraud_score: float) -> Decimal:
    """Calculates a multiplier based on risk level and fraud probability."""
    risk_factor = {
        "low": Decimal("1.0"),
        "medium": Decimal("0.9"),
        "high": Decimal("0.6")
    }.get(risk_level, Decimal("0.5"))
    
    fraud_factor = Decimal("1.0") - Decimal(str(fraud_score))
    return risk_factor * fraud_factor


def confidence_adjustment(base_confidence: float, data_quality_score: float) -> Decimal:
    """Calculates final confidence score based on data quality."""
    return Decimal(str(base_confidence)) * Decimal(str(data_quality_score))


class DecisionEngine:
    def __init__(self, policies: Dict[str, Any], model_version: str = "heuristic-v1.0", policy_version: str = "default-v1"):
        self.policies = policies
        self.model_version = model_version
        self.policy_version = policy_version
        self.guardrails = GuardrailsEvaluator(policies)

    def generate_candidate_interventions(self) -> List[Dict[str, Any]]:
        # Hardcoded heuristic uplifts for candidates, optionally override via policies
        return [
            {"action": "RETRY", "uplift": 0.05, "confidence": 0.90, "discount_pct": 0.0},
            {"action": "REMINDER", "uplift": 0.08, "confidence": 0.85, "discount_pct": 0.0},
            {"action": "INCENTIVE", "uplift": 0.25, "confidence": 0.80, "discount_pct": 10.0},
            {"action": "ALTERNATIVE_METHOD", "uplift": 0.12, "confidence": 0.70, "discount_pct": 0.0},
            {"action": "ESCALATE", "uplift": 0.30, "confidence": 0.95, "discount_pct": 0.0},
            {"action": "DO_NOTHING", "uplift": 0.0, "confidence": 1.00, "discount_pct": 0.0},
        ]

    def assign_to_experiment(self, transaction_id: str, active_experiment: Dict[str, Any] = None) -> str:
        """
        Deterministically assign a transaction to an experiment arm based on holdout percentage.
        Returns 'treatment' or 'control'.
        """
        if not active_experiment:
            return "treatment" # Default to policy if no experiment

        holdout_pct = float(active_experiment.get("holdout_percentage", 0.1))
        
        # Simple deterministic hash for assignment
        import hashlib
        hash_val = int(hashlib.md5(transaction_id.encode('utf-8')).hexdigest()[:8], 16)
        
        # 0xFFFFFFFF is max for 8 hex chars
        threshold = int(0xFFFFFFFF * holdout_pct)
        
        if hash_val < threshold:
            return "control"
        return "treatment"

    def make_decision(self, transaction_id: str, amount_minor: int, currency: str, transaction_metadata: Dict[str, Any], active_experiment: Dict[str, Any] = None) -> EngineDecision:
        amount = Decimal(amount_minor) / Decimal("100.0")
        risk_profile = transaction_metadata.get("risk_profile", "medium")
        state_version = transaction_metadata.get("state_version", 1)
        fraud_score = transaction_metadata.get("fraud_score", 0.0)
        data_quality_score = transaction_metadata.get("data_quality_score", 1.0)
        
        # 1. Calculate revenue-at-risk
        revenue_at_risk = amount
        
        # 2. Obtain natural recovery probability / value
        natural_rec = natural_recovery_value(amount, risk_profile, state_version)
        
        # Calculate risk and confidence factors
        risk_adj = risk_adjustment(risk_profile, fraud_score)
        
        # 3. Generate candidate interventions
        raw_candidates = self.generate_candidate_interventions()
        evaluated_candidates: List[ActionCandidate] = []
        
        for c in raw_candidates:
            action = c["action"]
            
            # 4. Obtain estimated uplift for each candidate
            predicted_uplift = Decimal(str(c["uplift"]))
            
            # Confidence adjustment
            confidence = confidence_adjustment(c["confidence"], data_quality_score)
            
            # 5. Calculate expected incremental revenue
            inc_rec = incremental_recovery_value(amount, predicted_uplift)
            expected_rev = expected_incremental_revenue(inc_rec, risk_adj)
            
            # 6. Calculate intervention cost
            cost = intervention_cost(action, amount, c["discount_pct"])
            
            # 7. Calculate expected net contribution
            net_contrib = expected_net_contribution(expected_rev, cost)
            
            # 8. Apply policy constraints (Guardrails)
            guardrail_res = self.guardrails.evaluate(action, transaction_metadata, c["discount_pct"], float(confidence))
            
            evaluated_candidates.append(ActionCandidate(
                action=action,
                predicted_uplift=predicted_uplift,
                intervention_cost=cost,
                confidence=confidence,
                expected_value=net_contrib,
                is_valid=guardrail_res.is_valid,
                rejection_reasons=[guardrail_res.rejection_reason] if guardrail_res.rejection_reason else []
            ))

        # 9. Rank valid interventions
        valid_candidates = [c for c in evaluated_candidates if c.is_valid]
        
        # Sort by expected value (descending)
        valid_candidates.sort(key=lambda c: c.expected_value, reverse=True)
        
        # 10. Allow DO NOTHING (fallback)
        best_candidate = next((c for c in valid_candidates), None)
        if not best_candidate or best_candidate.expected_value <= Decimal("0.0"):
            do_nothing = next((c for c in evaluated_candidates if c.action == "DO_NOTHING"), None)
            if do_nothing and do_nothing.is_valid:
                best_candidate = do_nothing
        
        if not best_candidate:
            # Absolute fallback if somehow DO_NOTHING is invalid
            best_candidate = ActionCandidate(
                action="DO_NOTHING",
                predicted_uplift=Decimal('0'),
                intervention_cost=Decimal('0'),
                confidence=Decimal('1'),
                expected_value=Decimal('0'),
                is_valid=True
            )

        alternative_actions = [
            {
                "action": c.action,
                "expected_value": c.expected_value,
                "is_valid": c.is_valid,
                "rejection_reasons": c.rejection_reasons
            }
            for c in evaluated_candidates if c.action != best_candidate.action
        ]
        
        # 11. Produce a final decision object
        
        # Apply experiment assignment
        assignment = self.assign_to_experiment(transaction_id, active_experiment)
        if assignment == "control":
            # If in control, force DO_NOTHING to measure natural recovery
            best_candidate = next((c for c in evaluated_candidates if c.action == "DO_NOTHING"), best_candidate)

        return EngineDecision(
            transaction_id=transaction_id,
            selected_action=best_candidate.action,
            expected_value=best_candidate.expected_value,
            predicted_uplift=best_candidate.predicted_uplift,
            intervention_cost=best_candidate.intervention_cost,
            confidence=best_candidate.confidence,
            model_version=self.model_version,
            policy_version=self.policy_version,
            alternative_actions=alternative_actions,
            rejection_reasons=best_candidate.rejection_reasons,
            created_at=datetime.now(timezone.utc).isoformat()
        )

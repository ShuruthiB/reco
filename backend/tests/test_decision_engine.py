import pytest
from decimal import Decimal
from typing import Any, Dict

from app.engine.decision_engine import DecisionEngine


def get_base_policies() -> Dict[str, Any]:
    return {
        "max_retries": 3,
        "max_incentive_pct": 20.0,
        "allow_incentives": True,
        "blocked_actions": [],
        "fraud_score_threshold": 0.8,
        "min_confidence": 0.6
    }

def get_base_transaction_meta() -> Dict[str, Any]:
    return {
        "risk_profile": "medium",
        "state_version": 1,
        "fraud_score": 0.1,
        "data_quality_score": 1.0,
        "retry_count": 0,
        "customer_opt_out": False,
        "status": "failed"
    }

def test_obvious_retry():
    # Retry is cheap and usually gives a decent uplift.
    engine = DecisionEngine(get_base_policies())
    
    # Let's adjust the generation to make retry the clear winner
    engine.generate_candidate_interventions = lambda: [
        {"action": "RETRY", "uplift": 0.20, "confidence": 0.90, "discount_pct": 0.0},
        {"action": "REMINDER", "uplift": 0.01, "confidence": 0.90, "discount_pct": 0.0},
        {"action": "DO_NOTHING", "uplift": 0.0, "confidence": 1.00, "discount_pct": 0.0},
    ]
    
    decision = engine.make_decision("tx-1", 10000, "USD", get_base_transaction_meta())
    assert decision.selected_action == "RETRY"
    assert decision.expected_value > 0

def test_obvious_reminder():
    # Reminder gives good uplift with no discount cost.
    engine = DecisionEngine(get_base_policies())
    
    engine.generate_candidate_interventions = lambda: [
        {"action": "RETRY", "uplift": 0.01, "confidence": 0.90, "discount_pct": 0.0},
        {"action": "REMINDER", "uplift": 0.25, "confidence": 0.90, "discount_pct": 0.0},
        {"action": "DO_NOTHING", "uplift": 0.0, "confidence": 1.00, "discount_pct": 0.0},
    ]
    
    decision = engine.make_decision("tx-2", 10000, "USD", get_base_transaction_meta())
    assert decision.selected_action == "REMINDER"
    assert decision.expected_value > 0

def test_attractive_discount_but_poor_net_value():
    # Discount has huge uplift but the cost of the discount outweighs the revenue
    engine = DecisionEngine(get_base_policies())
    
    engine.generate_candidate_interventions = lambda: [
        {"action": "INCENTIVE", "uplift": 0.05, "confidence": 0.90, "discount_pct": 10.0}, # Cost is 10% of amount! Uplift is only 5%
        {"action": "DO_NOTHING", "uplift": 0.0, "confidence": 1.00, "discount_pct": 0.0},
    ]
    
    decision = engine.make_decision("tx-3", 10000, "USD", get_base_transaction_meta())
    assert decision.selected_action == "DO_NOTHING"
    
    # Verify incentive was negative expected value
    alt = next(a for a in decision.alternative_actions if a["action"] == "INCENTIVE")
    assert alt["expected_value"] < 0

def test_high_natural_recovery():
    # High natural recovery means low uplift potential, DO_NOTHING wins due to costs
    engine = DecisionEngine(get_base_policies())
    meta = get_base_transaction_meta()
    meta["risk_profile"] = "low" # High natural recovery
    
    engine.generate_candidate_interventions = lambda: [
        {"action": "RETRY", "uplift": 0.001, "confidence": 0.90, "discount_pct": 0.0}, # Very low uplift, cost 0.50
        {"action": "DO_NOTHING", "uplift": 0.0, "confidence": 1.00, "discount_pct": 0.0},
    ]
    
    decision = engine.make_decision("tx-4", 1000, "USD", meta)
    assert decision.selected_action == "DO_NOTHING"

def test_low_confidence():
    # Data quality is terrible, resulting in low confidence -> ESCALATE
    engine = DecisionEngine(get_base_policies())
    meta = get_base_transaction_meta()
    meta["data_quality_score"] = 0.2  # Drops all confidence below 0.6 threshold
    
    decision = engine.make_decision("tx-5", 10000, "USD", meta)
    assert decision.selected_action == "ESCALATE"

def test_policy_violation():
    # Action is blocked globally
    policies = get_base_policies()
    policies["blocked_actions"] = ["RETRY", "REMINDER"]
    engine = DecisionEngine(policies)
    
    engine.generate_candidate_interventions = lambda: [
        {"action": "RETRY", "uplift": 0.90, "confidence": 0.90, "discount_pct": 0.0},
        {"action": "DO_NOTHING", "uplift": 0.0, "confidence": 1.00, "discount_pct": 0.0},
    ]
    
    decision = engine.make_decision("tx-6", 10000, "USD", get_base_transaction_meta())
    assert decision.selected_action == "DO_NOTHING"
    
    alt = next(a for a in decision.alternative_actions if a["action"] == "RETRY")
    assert alt["is_valid"] is False
    assert "blocked" in alt["rejection_reasons"][0]

def test_exhausted_retry_count():
    engine = DecisionEngine(get_base_policies())
    meta = get_base_transaction_meta()
    meta["retry_count"] = 3 # Max is 3
    
    engine.generate_candidate_interventions = lambda: [
        {"action": "RETRY", "uplift": 0.90, "confidence": 0.90, "discount_pct": 0.0},
        {"action": "DO_NOTHING", "uplift": 0.0, "confidence": 1.00, "discount_pct": 0.0},
    ]
    
    decision = engine.make_decision("tx-7", 10000, "USD", meta)
    assert decision.selected_action == "DO_NOTHING"
    
    alt = next(a for a in decision.alternative_actions if a["action"] == "RETRY")
    assert alt["is_valid"] is False
    assert "Maximum retries" in alt["rejection_reasons"][0]

def test_suspicious_transaction():
    engine = DecisionEngine(get_base_policies())
    meta = get_base_transaction_meta()
    meta["fraud_score"] = 0.95 # Above 0.8
    
    decision = engine.make_decision("tx-8", 10000, "USD", meta)
    assert decision.selected_action == "DO_NOTHING"
    
    for alt in decision.alternative_actions:
        assert alt["is_valid"] is False
        assert "fraud" in alt["rejection_reasons"][0].lower()

def test_no_profitable_intervention():
    # If every action costs more than it brings in, select DO_NOTHING
    engine = DecisionEngine(get_base_policies())
    
    engine.generate_candidate_interventions = lambda: [
        {"action": "RETRY", "uplift": 0.0, "confidence": 0.90, "discount_pct": 0.0}, # cost 0.50, 0 uplift
        {"action": "REMINDER", "uplift": 0.0, "confidence": 0.90, "discount_pct": 0.0}, # cost 0.05, 0 uplift
        {"action": "ESCALATE", "uplift": 0.0, "confidence": 0.90, "discount_pct": 0.0}, # cost 5.0, 0 uplift
        {"action": "DO_NOTHING", "uplift": 0.0, "confidence": 1.00, "discount_pct": 0.0},
    ]
    
    decision = engine.make_decision("tx-9", 1000, "USD", get_base_transaction_meta())
    assert decision.selected_action == "DO_NOTHING"

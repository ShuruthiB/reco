import pytest
from decimal import Decimal
from app.engine.decision_engine import DecisionEngine

def test_demo_hero_scenarios():
    policies_config = {
        "max_retries": 3,
        "max_incentive_pct": 20.0,
        "allow_incentives": True,
        "blocked_actions": ["ALTERNATIVE_METHOD"],
        "fraud_score_threshold": 0.8,
        "min_confidence": 0.5
    }
    engine = DecisionEngine(policies_config, model_version="demo-v1", policy_version="hero-v1")
    
    # SCENARIO A: RETRY optimal
    decision_a = engine.make_decision(
        transaction_id="tx_A",
        amount_minor=1500,
        currency="USD",
        transaction_metadata={"risk_profile": "low", "customer_opt_out": True}
    )
    assert decision_a.selected_action == "RETRY"
    assert decision_a.expected_value == Decimal("0.25")
    
    # SCENARIO B: INCENTIVE attractive but becomes inferior after cost
    decision_b = engine.make_decision(
        transaction_id="tx_B",
        amount_minor=200,
        currency="USD",
        transaction_metadata={"risk_profile": "low"}
    )
    assert decision_b.selected_action == "REMINDER"
    assert decision_b.expected_value == Decimal("0.11")
    
    # Verify INCENTIVE was considered but lost
    incentive_candidate = next((c for c in decision_b.alternative_actions if c["action"] == "INCENTIVE"), None)
    assert incentive_candidate is not None
    assert incentive_candidate["expected_value"] < decision_b.expected_value
    
    # SCENARIO C: DO_NOTHING optimal
    decision_c = engine.make_decision(
        transaction_id="tx_C",
        amount_minor=50,
        currency="USD",
        transaction_metadata={"risk_profile": "low"}
    )
    assert decision_c.selected_action == "DO_NOTHING"
    assert decision_c.expected_value == Decimal("0.00")
    
    # SCENARIO D: Blocked by guardrail and escalated
    decision_d = engine.make_decision(
        transaction_id="tx_D",
        amount_minor=50000,
        currency="USD",
        transaction_metadata={"risk_profile": "medium", "data_quality_score": 0.4}
    )
    assert decision_d.selected_action == "ESCALATE"
    assert decision_d.expected_value == Decimal("130.00")
    
    # SCENARIO E: Standard Incentive success
    decision_e = engine.make_decision(
        transaction_id="tx_E",
        amount_minor=2500,
        currency="USD",
        transaction_metadata={"risk_profile": "medium", "fraud_score": 0.1}
    )
    assert decision_e.selected_action == "INCENTIVE"
    assert decision_e.expected_value > Decimal("0.0")

import pytest
from decimal import Decimal
from app.engine.decision_engine import DecisionEngine
from app.engine.optimizer import BudgetOptimizer, OptimizerConstraints

def test_budget_optimizer_knapsack():
    engine = DecisionEngine(policies={})
    constraints = OptimizerConstraints(
        total_budget=Decimal("5.00"),
        max_customer_incentive=Decimal("100.00"),
        max_discount=Decimal("20.0"),
        max_retries=3,
        min_confidence=Decimal("0.5"),
        allowed_interventions=["RETRY", "REMINDER", "INCENTIVE", "ESCALATE"]
    )
    
    optimizer = BudgetOptimizer(constraints, engine)
    
    # We provide a bunch of transactions with varying amounts.
    # INCENTIVE 10% on $1000 = $100 cost. This will exceed the $5.00 total budget.
    # INCENTIVE 10% on $40 = $4 cost. Expected rev = $40 * 0.25 (uplift) * 0.9 (risk) = $9. Net = $5. ROI = 1.25.
    # ESCALATE always costs $5.00.
    
    transactions = [
        {"transaction_id": "tx-1", "amount": 1000, "metadata": {"risk_profile": "low"}},
        {"transaction_id": "tx-2", "amount": 40, "metadata": {"risk_profile": "low"}},
        {"transaction_id": "tx-3", "amount": 20, "metadata": {"risk_profile": "low"}},
    ]
    
    result = optimizer.optimize(transactions)
    
    # Total budget is $5.00. 
    assert result["budget_allocated"] <= Decimal("5.00")
    assert result["budget_remaining"] >= Decimal("0.00")
    assert result["total_budget"] == Decimal("5.00")
    
    # tx-1 incentive cost is too high, should be rejected due to budget.
    rejected_ids = [o.transaction_id for o in result["rejected_opportunities"]]
    assert "tx-1" in rejected_ids or result["budget_allocated"] < 5

def test_budget_optimizer_policy_filter():
    engine = DecisionEngine(policies={})
    constraints = OptimizerConstraints(
        total_budget=Decimal("100.00"),
        max_customer_incentive=Decimal("10.00"),
        max_discount=Decimal("5.0"), # strict max discount filter
        max_retries=3,
        min_confidence=Decimal("0.9"), # strict confidence filter
        allowed_interventions=["RETRY"] # Only retry allowed
    )
    
    optimizer = BudgetOptimizer(constraints, engine)
    
    transactions = [
        {"transaction_id": "tx-1", "amount": 100, "metadata": {"risk_profile": "low", "state_version": 4}}, # Max retries exceeded
    ]
    
    result = optimizer.optimize(transactions)
    assert len(result["top_opportunities"]) == 0
    assert len(result["rejected_opportunities"]) == 1
    assert result["rejected_opportunities"][0].rejection_reason == "Max retries exceeded"

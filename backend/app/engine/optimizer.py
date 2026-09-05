from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.engine.decision_engine import DecisionEngine, ActionCandidate

@dataclass
class OptimizerConstraints:
    total_budget: Decimal
    max_customer_incentive: Decimal
    max_discount: Decimal
    max_retries: int
    min_confidence: Decimal
    allowed_interventions: List[str]

@dataclass
class OptimizedOpportunity:
    transaction_id: str
    amount: Decimal
    action: str
    predicted_uplift: Decimal
    expected_incremental_value: Decimal
    intervention_cost: Decimal
    net_incremental_value: Decimal
    roi: Decimal
    rejected: bool = False
    rejection_reason: Optional[str] = None

class BudgetOptimizer:
    def __init__(self, constraints: OptimizerConstraints, engine: DecisionEngine):
        self.constraints = constraints
        self.engine = engine
        
    def evaluate_candidates(self, transaction_id: str, amount: Decimal, metadata: Dict[str, Any]) -> List[OptimizedOpportunity]:
        # Engine produces all candidates
        # We temporarily inject policy limits into the guardrails evaluating context just by using the math in engine
        raw_candidates = self.engine.generate_candidate_interventions()
        
        # We manually process them here to expose the exact math requested
        from app.engine.decision_engine import (
            natural_recovery_value, incremental_recovery_value, intervention_cost, 
            expected_incremental_revenue, expected_net_contribution, risk_adjustment, confidence_adjustment
        )
        
        risk_profile = metadata.get("risk_profile", "medium")
        fraud_score = metadata.get("fraud_score", 0.0)
        data_quality = metadata.get("data_quality_score", 1.0)
        state_version = metadata.get("state_version", 1)
        
        risk_adj = risk_adjustment(risk_profile, fraud_score)
        
        opportunities = []
        for c in raw_candidates:
            action = c["action"]
            
            # Policy Filtering
            if action not in self.constraints.allowed_interventions and action != "DO_NOTHING":
                continue
                
            predicted_uplift = Decimal(str(c["uplift"]))
            confidence = confidence_adjustment(c["confidence"], data_quality)
            
            discount_pct = Decimal(str(c["discount_pct"]))
            
            # Math
            inc_rec = incremental_recovery_value(amount, predicted_uplift)
            expected_rev = expected_incremental_revenue(inc_rec, risk_adj)
            cost = intervention_cost(action, amount, c["discount_pct"])
            net_contrib = expected_net_contribution(expected_rev, cost)
            
            roi = Decimal("0")
            if cost > 0:
                roi = net_contrib / cost
            elif net_contrib > 0:
                roi = Decimal("999999") # Arbitrarily high for zero cost positive return
                
            opp = OptimizedOpportunity(
                transaction_id=transaction_id,
                amount=amount,
                action=action,
                predicted_uplift=predicted_uplift,
                expected_incremental_value=expected_rev,
                intervention_cost=cost,
                net_incremental_value=net_contrib,
                roi=roi,
                rejected=False
            )
            
            # Hard policy filters
            if action == "RETRY" and state_version > self.constraints.max_retries:
                opp.rejected = True
                opp.rejection_reason = "Max retries exceeded"
            elif confidence < self.constraints.min_confidence:
                opp.rejected = True
                opp.rejection_reason = "Below minimum confidence"
            elif discount_pct > self.constraints.max_discount:
                opp.rejected = True
                opp.rejection_reason = "Exceeds max discount %"
            elif cost > self.constraints.max_customer_incentive and action == "INCENTIVE":
                opp.rejected = True
                opp.rejection_reason = "Exceeds max customer incentive"
            elif net_contrib <= 0 and action != "DO_NOTHING":
                opp.rejected = True
                opp.rejection_reason = "Negative net contribution"
                
            opportunities.append(opp)
            
        return opportunities

    def optimize(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_opportunities = []
        for tx in transactions:
            tx_id = tx["transaction_id"]
            amount = Decimal(str(tx["amount"]))
            metadata = tx.get("metadata", {})
            
            opps = self.evaluate_candidates(tx_id, amount, metadata)
            # Find the best valid non-DO_NOTHING opportunity
            valid_opps = [o for o in opps if not o.rejected and o.action != "DO_NOTHING"]
            valid_opps.sort(key=lambda x: x.roi, reverse=True)
            
            if valid_opps:
                all_opportunities.append(valid_opps[0]) # take the best one
            else:
                rejected_opps = [o for o in opps if o.action != "DO_NOTHING"]
                if rejected_opps:
                    # Sort by best ROI even if rejected, so we show the "closest" opportunity
                    rejected_opps.sort(key=lambda x: x.roi, reverse=True)
                    all_opportunities.append(rejected_opps[0])
                else:
                    # If no valid interventions, implicitly defaults to DO_NOTHING.
                    do_nothing = next((o for o in opps if o.action == "DO_NOTHING"), None)
                    if do_nothing:
                        do_nothing.rejected = True
                        do_nothing.rejection_reason = "No valid interventions found"
                        all_opportunities.append(do_nothing)

        # Separate into lists
        valid_candidates = [o for o in all_opportunities if not o.rejected]
        rejected_list = [o for o in all_opportunities if o.rejected]
        
        # Sort valid by ROI descending (Knapsack greedy approach)
        valid_candidates.sort(key=lambda x: x.roi, reverse=True)
        
        budget_remaining = self.constraints.total_budget
        funded = []
        
        for opp in valid_candidates:
            if opp.intervention_cost <= budget_remaining:
                budget_remaining -= opp.intervention_cost
                funded.append(opp)
            else:
                opp.rejected = True
                opp.rejection_reason = "Insufficient budget remaining"
                rejected_list.append(opp)
                
        budget_allocated = self.constraints.total_budget - budget_remaining
        
        return {
            "total_budget": self.constraints.total_budget,
            "budget_allocated": budget_allocated,
            "budget_remaining": budget_remaining,
            "top_opportunities": funded,
            "rejected_opportunities": rejected_list
        }

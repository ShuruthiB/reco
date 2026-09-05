from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from typing import Dict, Any

from app.domain.models import Merchant, Transaction, InterventionDecision, AgentDecision

router = APIRouter(prefix="/demo", tags=["demo"])
engine = create_engine('sqlite:///ml/datasets/synthetic_competition.db')

@router.get("/report")
def get_demo_report() -> Dict[str, Any]:
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        demo_slug = "reco-hero-demo"
        merchant = db.query(Merchant).filter(Merchant.slug == demo_slug).first()
        
        if not merchant:
            return {"error": "Demo merchant not found. Please run demo_reset.py first."}
            
        merchant_id = merchant.id
        
        # 1. Total Transactions
        transactions = db.query(Transaction).filter(Transaction.merchant_id == merchant_id).all()
        
        # 2. Financial Metrics
        gross_recovery_minor = 0
        natural_recovery_minor = 0
        intervention_cost_minor = 0
        net_incremental_contribution_minor = 0
        
        for t in transactions:
            if t.status in ["recovered", "success"]:
                gross_recovery_minor += t.amount_minor
                
        decisions = db.query(InterventionDecision).filter(InterventionDecision.merchant_id == merchant_id).all()
        
        actions_taken = []
        blocked_actions = 0
        escalations = 0
        do_nothing_decisions = 0
        
        for d in decisions:
            intervention_cost_minor += d.total_cost_minor
            if d.expected_net_contribution_minor:
                net_incremental_contribution_minor += d.expected_net_contribution_minor
                
            actions_taken.append(d.selected_action)
            
            if d.selected_action == "DO_NOTHING":
                do_nothing_decisions += 1
            if d.selected_action == "ESCALATE":
                escalations += 1
                
        # Check agent decisions for blocked actions logic
        agent_decisions = db.query(AgentDecision).filter(AgentDecision.merchant_id == merchant_id).all()
        for ad in agent_decisions:
            rationale = ad.rationale or {}
            if rationale.get("reasons") or rationale.get("blocked"):
                blocked_actions += 1
                
        # Calculate incremental recovery
        incremental_recovery_minor = net_incremental_contribution_minor + intervention_cost_minor

        return {
            "gross_recovery": gross_recovery_minor / 100.0,
            "natural_recovery": (gross_recovery_minor - incremental_recovery_minor) / 100.0,
            "incremental_recovery": incremental_recovery_minor / 100.0,
            "intervention_cost": intervention_cost_minor / 100.0,
            "net_incremental_contribution": net_incremental_contribution_minor / 100.0,
            "actions_taken": actions_taken,
            "do_nothing_decisions": do_nothing_decisions,
            "escalations": escalations,
            "blocked_actions": blocked_actions
        }
    finally:
        db.close()

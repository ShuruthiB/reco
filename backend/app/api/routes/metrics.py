from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any

from app.api.deps import get_db_session, get_merchant_id
from app.domain.models import Transaction, InterventionDecision, AgentDecision

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("/competition")
async def get_competition_metrics(
    merchant_id: str = Depends(get_merchant_id),
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    
    # 1. Transactions & Revenue at Risk
    stmt_tx = select(Transaction).where(Transaction.merchant_id == merchant_id)
    result_tx = await session.execute(stmt_tx)
    transactions = result_tx.scalars().all()
    
    total_transactions = len(transactions)
    revenue_at_risk_minor = sum(t.amount_minor for t in transactions)
    
    gross_recovered_minor = 0
    for t in transactions:
        if t.status in ["recovered", "success"]:
            gross_recovered_minor += t.amount_minor
            
    # 2. Decisions & Interventions
    stmt_dec = select(InterventionDecision).where(InterventionDecision.merchant_id == merchant_id)
    result_dec = await session.execute(stmt_dec)
    decisions = result_dec.scalars().all()
    
    intervention_cost_minor = 0
    net_incremental_contribution_minor = 0
    
    interventions_executed = 0
    do_nothing_decisions = 0
    escalations = 0
    
    for d in decisions:
        intervention_cost_minor += d.total_cost_minor
        if d.expected_net_contribution_minor:
            net_incremental_contribution_minor += d.expected_net_contribution_minor
            
        if d.selected_action == "DO_NOTHING":
            do_nothing_decisions += 1
        elif d.selected_action == "ESCALATE":
            escalations += 1
            interventions_executed += 1
        else:
            interventions_executed += 1

    # 3. Blocked Actions
    stmt_agent = select(AgentDecision).where(AgentDecision.merchant_id == merchant_id)
    result_agent = await session.execute(stmt_agent)
    agent_decisions = result_agent.scalars().all()
    
    blocked_actions = 0
    for ad in agent_decisions:
        rationale = ad.rationale or {}
        if rationale.get("reasons") or rationale.get("blocked"):
            blocked_actions += 1

    # 4. Math 
    # Incremental Recovery = Net Contribution + Cost
    incremental_recovery_minor = net_incremental_contribution_minor + intervention_cost_minor
    # Natural Recovery = Gross - Incremental
    natural_recovery_minor = gross_recovered_minor - incremental_recovery_minor
    
    recovery_rate = 0.0
    if total_transactions > 0:
        recovery_rate = sum(1 for t in transactions if t.status in ["recovered", "success"]) / total_transactions
        
    incremental_lift = 0.0
    if revenue_at_risk_minor > 0:
        incremental_lift = incremental_recovery_minor / revenue_at_risk_minor

    return {
        "total_transactions": total_transactions,
        "revenue_at_risk": revenue_at_risk_minor / 100.0,
        "natural_recovery": natural_recovery_minor / 100.0,
        "gross_recovered": gross_recovered_minor / 100.0,
        "incremental_recovery": incremental_recovery_minor / 100.0,
        "intervention_cost": intervention_cost_minor / 100.0,
        "net_incremental_contribution": net_incremental_contribution_minor / 100.0,
        "recovery_rate": round(recovery_rate * 100, 2), # percentage
        "incremental_lift": round(incremental_lift * 100, 2), # percentage
        "interventions_executed": interventions_executed,
        "do_nothing_decisions": do_nothing_decisions,
        "escalations": escalations,
        "blocked_actions": blocked_actions
    }

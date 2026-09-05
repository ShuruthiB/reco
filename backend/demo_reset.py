import asyncio
import uuid
import json
from decimal import Decimal
from datetime import datetime, timezone
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.models import (
    Base, Merchant, Customer, Order, Transaction, 
    PaymentEvent, InterventionCandidate, InterventionDecision, AgentDecision,
    Policy, PolicyVersion
)
from app.engine.decision_engine import DecisionEngine

def reset_and_seed_demo(db_path="ml/datasets/synthetic_competition.db"):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Clean previous demo merchant
    demo_slug = "reco-hero-demo"
    demo_merchant = session.query(Merchant).filter_by(slug=demo_slug).first()
    if demo_merchant:
        print("Clearing existing demo data...")
        # Since this is sqlite, cascading deletes can be tricky if not configured. 
        # I will just create a new unique merchant or clean up properly.
        session.query(InterventionDecision).filter(InterventionDecision.merchant_id == demo_merchant.id).delete(synchronize_session=False)
        session.query(AgentDecision).filter(AgentDecision.merchant_id == demo_merchant.id).delete(synchronize_session=False)
        session.query(InterventionCandidate).filter(InterventionCandidate.merchant_id == demo_merchant.id).delete(synchronize_session=False)
        session.query(PaymentEvent).filter(PaymentEvent.merchant_id == demo_merchant.id).delete(synchronize_session=False)
        session.query(Transaction).filter(Transaction.merchant_id == demo_merchant.id).delete(synchronize_session=False)
        session.query(Order).filter(Order.merchant_id == demo_merchant.id).delete(synchronize_session=False)
        session.query(Customer).filter(Customer.merchant_id == demo_merchant.id).delete(synchronize_session=False)
        session.query(PolicyVersion).filter(PolicyVersion.merchant_id == demo_merchant.id).delete(synchronize_session=False)
        session.query(Policy).filter(Policy.merchant_id == demo_merchant.id).delete(synchronize_session=False)
        session.query(Merchant).filter_by(id=demo_merchant.id).delete(synchronize_session=False)
        session.commit()
    
    print("Seeding Hero Demo scenarios...")
    
    merchant_id = uuid.uuid4()
    merchant = Merchant(
        id=merchant_id,
        name="RECO Hero Demo",
        slug=demo_slug,
        status="active",
        timezone="UTC",
        settings={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    session.add(merchant)
    
    policy_id = uuid.uuid4()
    policy_version_id = uuid.uuid4()
    policy = Policy(
        id=policy_id, merchant_id=merchant_id, name="Hero Policies", status="active",
        current_version_id=policy_version_id, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    
    policies_config = {
        "max_retries": 3,
        "max_incentive_pct": 20.0,
        "allow_incentives": True,
        "blocked_actions": ["ALTERNATIVE_METHOD"], # Blocked to allow RETRY to win in Scenario A
        "fraud_score_threshold": 0.8,
        "min_confidence": 0.5
    }
    
    policy_version = PolicyVersion(
        id=policy_version_id, policy_id=policy_id, merchant_id=merchant_id,
        version_number=1, version_label="hero-v1", rules=policies_config, guardrails={},
        effective_from=datetime.now(timezone.utc), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    
    session.add(policy)
    session.add(policy_version)
    session.commit()
    
    engine_runner = DecisionEngine(policies_config, model_version="demo-v1", policy_version="hero-v1")
    
    scenarios = [
        # Scenario A: RETRY optimal. (Amount $15. Block REMINDER/INCENTIVE via opt_out. ESCALATE is too expensive).
        {"scenario": "A", "amount": 1500, "meta": {"risk_profile": "low", "customer_opt_out": True}},
        
        # Scenario B: INCENTIVE attractive but becomes inferior after accounting for incentive cost. 
        # (Amount $2.00. INCENTIVE gross is high, but net is $0.10. REMINDER net is $0.11, so REMINDER wins).
        {"scenario": "B", "amount": 200, "meta": {"risk_profile": "low"}}, 
        
        # Scenario C: DO_NOTHING optimal because natural recovery is high (and amount is too small for any intervention cost).
        # (Amount $0.50)
        {"scenario": "C", "amount": 50, "meta": {"risk_profile": "low"}},
        
        # Scenario D: Blocked by guardrail and escalated. 
        # (Low data quality drops confidence < 0.5, blocking normal actions except ESCALATE).
        {"scenario": "D", "amount": 50000, "meta": {"risk_profile": "medium", "data_quality_score": 0.4}},
        
        # Scenario E: Duplicate webhook safely ignored.
        {"scenario": "E", "amount": 2500, "meta": {"risk_profile": "medium", "fraud_score": 0.1}}
    ]
    
    for s in scenarios:
        cust_id = uuid.uuid4()
        customer = Customer(
            id=cust_id, merchant_id=merchant_id, external_customer_id=f"hero_cust_{s['scenario']}",
            consent_status="granted", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )
        order_id = uuid.uuid4()
        order = Order(
            id=order_id, merchant_id=merchant_id, customer_id=cust_id, external_order_id=f"hero_ord_{s['scenario']}",
            amount_minor=s['amount'], currency="USD", status="pending", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )
        txn_id = uuid.uuid4()
        txn = Transaction(
            id=txn_id, merchant_id=merchant_id, customer_id=cust_id, order_id=order_id,
            external_transaction_id=f"hero_txn_{s['scenario']}", amount_minor=s['amount'], currency="USD",
            status="failed", state_version=1, failed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )
        
        session.add(customer)
        session.add(order)
        session.add(txn)
        
        decision = engine_runner.make_decision(
            transaction_id=str(txn_id),
            amount_minor=s['amount'],
            currency="USD",
            transaction_metadata=s['meta']
        )
        
        agent_decision = AgentDecision(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            transaction_id=txn_id,
            model_version=decision.model_version,
            policy_version_id=policy_version_id,
            decision_trigger="webhook",
            transaction_state_version=1,
            ranked_candidates=[],
            feature_snapshot=s['meta'],
            scoring_metadata={},
            rationale={"selected": decision.selected_action, "expected_value": str(decision.expected_value)},
            idempotency_key=f"demo_{s['scenario']}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(agent_decision)
        
        int_dec = InterventionDecision(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            transaction_id=txn_id,
            agent_decision_id=agent_decision.id,
            policy_version_id=policy_version_id,
            policy_version_label="hero-v1",
            selected_action=decision.selected_action,
            status="executed",
            execution_status="success" if decision.selected_action != "DO_NOTHING" else "skipped",
            expected_net_contribution_minor=int(decision.expected_value * 100),
            expected_incremental_revenue_minor=int(decision.predicted_uplift * Decimal(s['amount'])),
            total_cost_minor=int(decision.intervention_cost * 100),
            currency="USD",
            decision_rationale={"reasons": decision.rejection_reasons},
            idempotency_key=f"int_demo_{s['scenario']}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(int_dec)
        
        print(f"Scenario {s['scenario']} -> Engine Selected: {decision.selected_action}, Value: ${decision.expected_value:.2f}")

    session.commit()
    print("\n[SUCCESS] Demo seeded successfully. Use GET /api/demo/report to view results.")

if __name__ == "__main__":
    reset_and_seed_demo()

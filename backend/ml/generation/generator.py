import argparse
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from app.domain.models import (
    Base, Merchant, Customer, Order, Transaction, 
    PaymentEvent, InterventionCandidate, InterventionDecision, 
    Experiment, ExperimentAssignment, ExperimentOutcome
)

def set_seed(seed):
    random.seed(seed)

def generate_random_email():
    domains = ["example.com", "test.org", "mail.com"]
    return f"user_{random.randint(1000, 99999)}@{random.choice(domains)}"

def generate_merchant():
    return Merchant(
        id=uuid.uuid4(),
        name="Synthetic Merchant",
        slug="synth-merchant",
        status="active",
        timezone="UTC",
        settings={},
        created_at=datetime.now(timezone.utc) - timedelta(days=365),
        updated_at=datetime.now(timezone.utc) - timedelta(days=365)
    )

def generate_customers(merchant_id, count=5000):
    customers = []
    for i in range(count):
        customers.append(Customer(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            external_customer_id=f"ext_cust_{i}",
            email=generate_random_email(),
            phone=f"+1555{random.randint(1000000, 9999999)}",
            consent_status="granted",
            contact_count_30d=random.randint(0, 5),
            metadata_={"ltv": random.randint(100, 5000)},
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(10, 300)),
            updated_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10))
        ))
    return customers

def generate_dataset(db_path, size=10000, seed=42):
    set_seed(seed)
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    print(f"Generating exactly {size} transactions with seed {seed} into {db_path}...")
    
    merchant = generate_merchant()
    session.add(merchant)
    
    experiment = Experiment(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        name="Phase 19 Synthetic Competition",
        description="A/B Test of multiple interventions",
        status="active",
        holdout_percentage=Decimal("0.5"),
        arms=[{"name": "control"}, {"name": "treatment"}],
        eligibility_rules={},
        started_at=datetime.now(timezone.utc) - timedelta(days=90),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    session.add(experiment)
    
    customers = generate_customers(merchant.id, count=int(size * 0.5))
    session.bulk_save_objects(customers)
    
    orders = []
    transactions = []
    intervention_candidates = []
    intervention_decisions = []
    experiment_assignments = []
    experiment_outcomes = []
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=90)
    
    interventions = [
        ("RETRY", 0, Decimal("0.02")),
        ("REMINDER", 50, Decimal("0.05")), # 0.50 cost
        ("ALTERNATIVE_METHOD", 0, Decimal("0.10")),
        ("INCENTIVE", 1000, Decimal("0.20")), # 10.00 cost
        ("ESCALATE", 200, Decimal("0.15")) # 2.00 cost
    ]
    
    for i in range(size):
        customer = random.choice(customers)
        txn_date = start_date + timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds())))
        
        amount = random.randint(1000, 50000) # $10 to $500
        
        order = Order(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            customer_id=customer.id,
            external_order_id=f"ext_ord_{i}",
            amount_minor=amount,
            currency="USD",
            status="pending",
            line_items=[],
            metadata_={},
            created_at=txn_date,
            updated_at=txn_date
        )
        orders.append(order)
        
        is_success = random.random() < 0.70 # ~70% success rate
        
        txn = Transaction(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            customer_id=customer.id,
            order_id=order.id,
            external_transaction_id=f"ext_txn_{i}",
            amount_minor=amount,
            currency="USD",
            status="success" if is_success else "failed",
            payment_method=random.choice(["card", "upi", "netbanking"]),
            state_version=1,
            failed_at=None if is_success else txn_date,
            created_at=txn_date,
            updated_at=txn_date
        )
        transactions.append(txn)
        
        if not is_success:
            if random.random() < 0.2:
                txn.status = "abandoned"
                
            is_treatment = random.random() < 0.5
            arm_name = "treatment" if is_treatment else "control"
            
            assignment = ExperimentAssignment(
                id=uuid.uuid4(),
                experiment_id=experiment.id,
                merchant_id=merchant.id,
                transaction_id=txn.id,
                arm_name=arm_name,
                is_holdout=not is_treatment,
                assigned_at=txn_date,
                created_at=txn_date,
                updated_at=txn_date
            )
            experiment_assignments.append(assignment)
            
            baseline_prob = Decimal(str(random.uniform(0.01, 0.15)))
            recovers_naturally = random.random() < float(baseline_prob)
            
            if not is_treatment:
                if recovers_naturally:
                    txn.status = "recovered"
                    txn.recovered_at = txn_date + timedelta(hours=random.randint(1, 24))
                    
                    experiment_outcomes.append(ExperimentOutcome(
                        id=uuid.uuid4(),
                        experiment_id=experiment.id,
                        experiment_assignment_id=assignment.id,
                        merchant_id=merchant.id,
                        transaction_id=txn.id,
                        outcome_type="natural_recovery",
                        recovered_amount_minor=amount,
                        intervention_cost_minor=0,
                        currency="USD",
                        attributed_at=txn.recovered_at,
                        created_at=txn.recovered_at,
                        updated_at=txn.recovered_at
                    ))
            else:
                action, cost_minor, uplift = random.choice(interventions)
                treatment_prob = baseline_prob + uplift
                recovers_via_treatment = random.random() < float(treatment_prob)
                
                candidate = InterventionCandidate(
                    id=uuid.uuid4(),
                    merchant_id=merchant.id,
                    transaction_id=txn.id,
                    intervention_type="financial",
                    intervention_id="int_synth",
                    action_id=action,
                    eligibility_status="eligible",
                    baseline_recovery_probability=baseline_prob,
                    treatment_recovery_probability=treatment_prob,
                    predicted_uplift=uplift,
                    expected_incremental_revenue_minor=int(float(uplift) * amount),
                    intervention_cost_minor=cost_minor,
                    incentive_cost_minor=cost_minor if "INCENTIVE" in action else 0,
                    operational_cost_minor=cost_minor if "INCENTIVE" not in action else 0,
                    expected_net_contribution_minor=int(float(uplift) * amount) - cost_minor,
                    currency="USD",
                    model_version="synth_v1",
                    created_at=txn_date,
                    updated_at=txn_date
                )
                intervention_candidates.append(candidate)
                
                decision = InterventionDecision(
                    id=uuid.uuid4(),
                    merchant_id=merchant.id,
                    transaction_id=txn.id,
                    intervention_candidate_id=candidate.id,
                    policy_version_id=uuid.uuid4(),
                    policy_version_label="synth_policy",
                    selected_action=action,
                    status="executed",
                    execution_status="success",
                    expected_net_contribution_minor=candidate.expected_net_contribution_minor,
                    expected_incremental_revenue_minor=candidate.expected_incremental_revenue_minor,
                    total_cost_minor=cost_minor,
                    currency="USD",
                    idempotency_key=f"idemp_{txn.id}",
                    executed_at=txn_date + timedelta(minutes=random.randint(1, 60)),
                    created_at=txn_date,
                    updated_at=txn_date
                )
                intervention_decisions.append(decision)
                
                if recovers_via_treatment:
                    txn.status = "recovered"
                    txn.recovered_at = decision.executed_at + timedelta(minutes=random.randint(1, 120))
                    experiment_outcomes.append(ExperimentOutcome(
                        id=uuid.uuid4(),
                        experiment_id=experiment.id,
                        experiment_assignment_id=assignment.id,
                        merchant_id=merchant.id,
                        transaction_id=txn.id,
                        outcome_type="intervention_recovery",
                        recovered_amount_minor=amount,
                        intervention_cost_minor=cost_minor,
                        currency="USD",
                        attributed_at=txn.recovered_at,
                        created_at=txn.recovered_at,
                        updated_at=txn.recovered_at
                    ))
    
    session.bulk_save_objects(orders)
    session.bulk_save_objects(transactions)
    session.bulk_save_objects(experiment_assignments)
    session.bulk_save_objects(intervention_candidates)
    session.bulk_save_objects(intervention_decisions)
    session.bulk_save_objects(experiment_outcomes)
    
    session.commit()
    print(f"Successfully generated database at {db_path} with exactly {size} transactions.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="ml/datasets/synthetic_competition.db")
    args = parser.parse_args()
    
    generate_dataset(args.out, size=args.size, seed=args.seed)

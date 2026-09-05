import argparse
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.domain.models import (
    Base, Merchant, Customer, Order, Transaction, 
    PaymentEvent, InterventionCandidate, InterventionDecision, Experiment
)

def run_validation_and_report(db_path):
    print(f"Validating database at {db_path}...\n")
    engine = create_engine(f'sqlite:///{db_path}')
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # 1. Total Customers
    total_customers = session.query(Customer).count()
    
    # 2. Total Orders
    total_orders = session.query(Order).count()
    
    # 3. Total Transactions
    total_transactions = session.query(Transaction).count()
    assert total_transactions > 0, "Dataset contains no transactions."
    
    # Validation constraints checks
    assert total_orders <= total_transactions, "More orders than transactions doesn't align with our generation logic."
    assert session.query(Transaction).filter(Transaction.customer_id == None).count() == 0, "Orphaned transactions found."
    
    # 4. Status Breakdown
    successful_payments = session.query(Transaction).filter(Transaction.status == "success").count()
    failed_payments = session.query(Transaction).filter(Transaction.status == "failed").count()
    abandoned_payments = session.query(Transaction).filter(Transaction.status == "abandoned").count()
    recovered_payments = session.query(Transaction).filter(Transaction.status == "recovered").count()
    
    assert successful_payments + failed_payments + abandoned_payments + recovered_payments == total_transactions, "Mismatched transaction status distribution."
    
    # Distinguish Natural vs Intervention Recoveries
    # If a transaction is recovered and has an executed InterventionDecision, it's an intervention recovery.
    intervention_recoveries = session.query(Transaction).join(
        InterventionDecision, Transaction.id == InterventionDecision.transaction_id
    ).filter(Transaction.status == "recovered").count()
    
    naturally_recovered = recovered_payments - intervention_recoveries
    
    # Financial Aggregates
    # Total gross value of successful + recovered
    total_gross_value = session.query(func.sum(Transaction.amount_minor)).filter(
        Transaction.status.in_(["success", "recovered"])
    ).scalar() or 0
    total_gross_value = total_gross_value / 100.0
    
    # Total naturally recovered value
    # Recovered transactions WITHOUT an intervention decision
    naturally_recovered_amount = session.query(func.sum(Transaction.amount_minor)).filter(
        Transaction.status == "recovered"
    ).filter(
        ~Transaction.id.in_(session.query(InterventionDecision.transaction_id))
    ).scalar() or 0
    naturally_recovered_amount = naturally_recovered_amount / 100.0
    
    # Total intervention cost
    total_intervention_cost = session.query(func.sum(InterventionDecision.total_cost_minor)).scalar() or 0
    total_intervention_cost = total_intervention_cost / 100.0
    
    # Total incremental value (Value of intervention recoveries - intervention cost)
    intervention_recovered_amount = session.query(func.sum(Transaction.amount_minor)).join(
        InterventionDecision, Transaction.id == InterventionDecision.transaction_id
    ).filter(Transaction.status == "recovered").scalar() or 0
    intervention_recovered_amount = intervention_recovered_amount / 100.0
    
    total_incremental_value = intervention_recovered_amount - total_intervention_cost
    
    print("=== SYNTHETIC DATASET REPORT ===")
    print(f"Total Customers: {total_customers}")
    print(f"Total Orders: {total_orders}")
    print(f"Total Transactions: {total_transactions}")
    print(f"Successful Payments: {successful_payments}")
    print(f"Failed Payments: {failed_payments}")
    print(f"Abandoned Payments: {abandoned_payments}")
    print(f"Naturally Recovered Transactions: {naturally_recovered}")
    print(f"Intervention Recoveries: {intervention_recoveries}")
    print("--------------------------------")
    print(f"Total Gross Value: ${total_gross_value:,.2f}")
    print(f"Total Naturally Recovered Value: ${naturally_recovered_amount:,.2f}")
    print(f"Total Intervention Cost: ${total_intervention_cost:,.2f}")
    print(f"Total Incremental Value: ${total_incremental_value:,.2f}")
    print("================================")
    
    print("\n[SUCCESS] All validations passed! Dataset referential integrity and distributions are sound.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=str, default="ml/datasets/synthetic_competition.db")
    args = parser.parse_args()
    
    run_validation_and_report(args.db)

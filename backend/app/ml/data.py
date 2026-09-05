import numpy as np
import pandas as pd
import uuid

def extract_data(n_samples: int = 5000) -> pd.DataFrame:
    """
    Programmatically generates a synthetic dataset matching the database schema
    for the ML pipeline. This ensures reproducibility without relying on a live DB connection.
    """
    np.random.seed(42)
    
    # Generate random features
    data = []
    
    risk_levels = ["low", "medium", "high"]
    payment_methods = ["card", "upi", "netbanking", "wallet", "emi"]
    actions = ["DO_NOTHING", "RETRY", "REMINDER", "INCENTIVE", "ALTERNATIVE_METHOD"]
    
    for i in range(n_samples):
        amount = np.random.lognormal(mean=7.0, sigma=1.5)  # Amount in minor units roughly
        risk = np.random.choice(risk_levels, p=[0.5, 0.3, 0.2])
        method = np.random.choice(payment_methods)
        state_version = np.random.randint(1, 4)
        fraud_score = np.random.uniform(0.0, 0.9) if risk == "high" else np.random.uniform(0.0, 0.2)
        
        # Interventions
        action = np.random.choice(actions, p=[0.2, 0.3, 0.2, 0.2, 0.1])
        
        # Determine natural recovery prob (if DO_NOTHING)
        base_recovery_prob = 0.20 if risk == "low" else (0.10 if risk == "medium" else 0.05)
        
        # Uplift from action
        uplift_prob = 0.0
        if action == "RETRY": uplift_prob = 0.05
        elif action == "REMINDER": uplift_prob = 0.08
        elif action == "INCENTIVE": uplift_prob = 0.25
        elif action == "ALTERNATIVE_METHOD": uplift_prob = 0.12
        
        total_prob = min(base_recovery_prob + uplift_prob, 1.0)
        
        # Outcome
        recovered = np.random.rand() < total_prob
        
        data.append({
            "transaction_id": str(uuid.uuid4()),
            "amount_minor": amount,
            "risk_profile": risk,
            "payment_method": method,
            "state_version": state_version,
            "fraud_score": fraud_score,
            "action": action,
            "recovered": int(recovered)
        })
        
    return pd.DataFrame(data)

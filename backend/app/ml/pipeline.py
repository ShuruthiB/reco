import os
import argparse
from sklearn.model_selection import train_test_split
from app.ml.data import extract_data
from app.ml.features import FeatureEngineer
from app.ml.model import BaselineRecoveryModel, UpliftModel
from app.ml.evaluation import evaluate_model, save_metrics

def main(n_samples: int = 5000):
    print(f"Extracting {n_samples} synthetic samples...")
    df = extract_data(n_samples=n_samples)
    
    # Train / Val / Test Split
    train_df, temp_df = train_test_split(df, test_size=0.3, random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)
    
    print("Fitting FeatureEngineer...")
    fe = FeatureEngineer()
    
    # Fit features on train data ONLY
    X_train_raw = train_df.drop(columns=["transaction_id", "action", "recovered"])
    X_train = fe.fit_transform(X_train_raw)
    
    # 1. Baseline Model (DO_NOTHING subset)
    print("Training Baseline Recovery Model...")
    baseline_train_mask = train_df["action"] == "DO_NOTHING"
    X_baseline_train = X_train[baseline_train_mask]
    y_baseline_train = train_df.loc[baseline_train_mask, "recovered"]
    
    baseline_model = BaselineRecoveryModel()
    baseline_model.fit(X_baseline_train, y_baseline_train)
    
    # 2. Uplift Model
    print("Training Uplift Model (T-Learner)...")
    uplift_model = UpliftModel()
    import numpy as np # Ensure numpy is available for uplift model fit
    uplift_model.fit(X_train, train_df["action"], train_df["recovered"])
    
    # 3. Evaluation on Validation Set
    print("Evaluating models...")
    X_val = fe.transform(val_df.drop(columns=["transaction_id", "action", "recovered"]))
    
    # Baseline eval
    baseline_val_mask = val_df["action"] == "DO_NOTHING"
    X_baseline_val = X_val[baseline_val_mask]
    y_baseline_val = val_df.loc[baseline_val_mask, "recovered"]
    
    y_pred_proba_base = baseline_model.predict_proba(X_baseline_val)
    base_metrics = evaluate_model(y_baseline_val, y_pred_proba_base)
    
    metrics = {
        "baseline_model": base_metrics
    }
    
    print(f"Baseline Validation ROC-AUC: {base_metrics.get('roc_auc', 0):.4f}")
    
    # 4. Serialization
    print("Serializing models...")
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)
    
    fe.save(os.path.join(models_dir, "feature_engineer.joblib"))
    baseline_model.save(os.path.join(models_dir, "baseline_model.joblib"))
    uplift_model.save(os.path.join(models_dir, "uplift_model.joblib"))
    
    # Save metrics artifact to project root or ML directory
    save_metrics(metrics, os.path.join(models_dir, "metrics.json"))
    
    print("ML Pipeline completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=5000)
    args = parser.parse_args()
    main(n_samples=args.samples)

from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score
import pandas as pd
import json

def evaluate_model(y_true: pd.Series, y_pred_proba: pd.Series, threshold: float = 0.5) -> dict:
    if len(y_true.unique()) < 2:
        return {"error": "Only one class present in y_true."}
        
    y_pred = (y_pred_proba >= threshold).astype(int)
    
    return {
        "roc_auc": float(roc_auc_score(y_true, y_pred_proba)),
        "pr_auc": float(average_precision_score(y_true, y_pred_proba)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0))
    }

def save_metrics(metrics: dict, filepath: str):
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=4)

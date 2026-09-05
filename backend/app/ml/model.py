import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression

class BaselineRecoveryModel:
    """Predicts natural recovery probability (DO_NOTHING arm)."""
    def __init__(self):
        # Use logistic regression for a simple, explainable baseline
        self.model = LogisticRegression(max_iter=1000, random_state=42)
        
    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.model.fit(X, y)
        
    def predict_proba(self, X: pd.DataFrame) -> pd.Series:
        # Returns probability of class 1 (recovered)
        return pd.Series(self.model.predict_proba(X)[:, 1], index=X.index)
        
    def save(self, filepath: str):
        joblib.dump(self.model, filepath)
        
    def load(self, filepath: str):
        self.model = joblib.load(filepath)


class UpliftModel:
    """Estimates incremental recovery caused by an intervention compared to no-intervention."""
    def __init__(self):
        # We will use separate models (T-Learner approach) for each action
        # mapping action -> LogisticRegression
        self.models = {}
        
    def fit(self, X: pd.DataFrame, action: pd.Series, y: pd.Series):
        actions = action.unique()
        for act in actions:
            if act == "DO_NOTHING":
                continue
            mask = action == act
            X_act = X[mask]
            y_act = y[mask]
            
            if len(np.unique(y_act)) > 1:
                model = LogisticRegression(max_iter=1000, random_state=42)
                model.fit(X_act, y_act)
                self.models[act] = model
            else:
                self.models[act] = None # Edge case: only one class present
                
    def predict_proba_treatment(self, X: pd.DataFrame, action_name: str) -> pd.Series:
        model = self.models.get(action_name)
        if model is None:
            return pd.Series(0.0, index=X.index)
        return pd.Series(model.predict_proba(X)[:, 1], index=X.index)
        
    def save(self, filepath: str):
        joblib.dump(self.models, filepath)
        
    def load(self, filepath: str):
        self.models = joblib.load(filepath)

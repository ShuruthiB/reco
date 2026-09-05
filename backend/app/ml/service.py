import os
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

from app.ml.features import FeatureEngineer
from app.ml.model import BaselineRecoveryModel, UpliftModel

class PredictionService:
    def __init__(self, models_dir: str | None = None):
        self.fe = FeatureEngineer()
        self.baseline_model = BaselineRecoveryModel()
        self.uplift_model = UpliftModel()
        self.is_loaded = False
        
        self.model_version = "ml-v1.0"
        self.feature_version = "fe-v1.0"
        
        if models_dir is None:
            self.models_dir = os.path.join(os.path.dirname(__file__), "models")
        else:
            self.models_dir = models_dir
            
    def load_models(self):
        try:
            self.fe.load(os.path.join(self.models_dir, "feature_engineer.joblib"))
            self.baseline_model.load(os.path.join(self.models_dir, "baseline_model.joblib"))
            self.uplift_model.load(os.path.join(self.models_dir, "uplift_model.joblib"))
            self.is_loaded = True
        except FileNotFoundError as e:
            raise RuntimeError(f"Could not load ML models. Has the pipeline been run? Error: {e}")

    def _prepare_features(self, transaction: Dict[str, Any]) -> pd.DataFrame:
        df = pd.DataFrame([transaction])
        # Ensure schema matches what FeatureEngineer expects
        expected_cols = ["amount_minor", "state_version", "fraud_score", "risk_profile", "payment_method"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None # Let imputer handle it
        return self.fe.transform(df)

    def predict_natural_recovery(self, transaction: Dict[str, Any]) -> Tuple[float, float, dict]:
        """
        Returns:
            probability (float)
            confidence (float)
            metadata (dict)
        """
        if not self.is_loaded:
            self.load_models()
            
        X = self._prepare_features(transaction)
        prob = self.baseline_model.predict_proba(X).iloc[0]
        
        # Simple confidence metric based on distance from 0.5 (further = more confident)
        confidence = abs(prob - 0.5) * 2.0 
        
        metadata = {
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "estimated baseline"
        }
        
        return float(prob), float(confidence), metadata

    def predict_uplift(self, transaction: Dict[str, Any], action: str) -> Tuple[float, float, dict]:
        """
        Estimates the incremental uplift caused by an intervention vs no intervention.
        Returns:
            estimated_uplift (float)
            confidence (float)
            metadata (dict)
        """
        if not self.is_loaded:
            self.load_models()
            
        if action == "DO_NOTHING":
            return 0.0, 1.0, {"note": "exact baseline"}
            
        X = self._prepare_features(transaction)
        
        # Base probability without intervention
        base_prob = self.baseline_model.predict_proba(X).iloc[0]
        
        # Treatment probability with intervention
        treat_prob = self.uplift_model.predict_proba_treatment(X, action).iloc[0]
        
        uplift = max(0.0, treat_prob - base_prob) # Clip at 0
        
        # Simple confidence heuristic
        confidence = abs(treat_prob - 0.5) * 2.0
        
        metadata = {
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
            "note": f"estimated uplift for {action}"
        }
        
        return float(uplift), float(confidence), metadata

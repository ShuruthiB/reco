import pytest
import pandas as pd
import numpy as np
import os
import shutil

from app.ml.features import FeatureEngineer
from app.ml.service import PredictionService
from app.ml.pipeline import main as run_pipeline

# Ensure models are trained for tests
@pytest.fixture(scope="session", autouse=True)
def setup_models():
    # Run the pipeline with a small sample size just for testing
    # It will create models in app/ml/models
    run_pipeline(n_samples=500)
    yield
    # We can optionally cleanup but we probably want them for the app

def test_feature_generation():
    df = pd.DataFrame([{
        "amount_minor": 10000,
        "state_version": 1,
        "fraud_score": 0.1,
        "risk_profile": "medium",
        "payment_method": "card"
    }])
    
    fe = FeatureEngineer()
    # Mock fit just for testing dimensions
    fe.fit(df)
    transformed = fe.transform(df)
    
    # Should scale numeric and one-hot encode categorical
    assert "amount_minor" in transformed.columns
    assert "risk_profile_medium" in transformed.columns
    assert "payment_method_card" in transformed.columns
    assert len(transformed.columns) > 3

def test_missing_values_and_unknown_categories():
    df_train = pd.DataFrame([{
        "amount_minor": 10000,
        "state_version": 1,
        "fraud_score": 0.1,
        "risk_profile": "medium",
        "payment_method": "card"
    }])
    
    df_test = pd.DataFrame([{
        "amount_minor": None, # Missing numeric
        "state_version": 1,
        "fraud_score": 0.1,
        "risk_profile": "ALIEN_RISK", # Unknown category
        "payment_method": None # Missing categorical
    }])
    
    fe = FeatureEngineer()
    fe.fit(df_train)
    transformed = fe.transform(df_test)
    
    # Missing numeric should be median imputed (here 10000)
    # The scaler will center it to 0.0 because mean is 10000 and std is 0 (in training)
    assert not transformed.isnull().any().any()
    
    # Unknown categories should be ignored (all OHE columns for this feature will be 0)
    assert transformed["risk_profile_medium"].iloc[0] == 0.0
    assert transformed["payment_method_card"].iloc[0] == 0.0

def test_prediction_schema():
    service = PredictionService()
    service.load_models()
    
    tx = {
        "amount_minor": 15000,
        "state_version": 2,
        "fraud_score": 0.5,
        "risk_profile": "high",
        "payment_method": "upi"
    }
    
    prob, conf, meta = service.predict_natural_recovery(tx)
    assert isinstance(prob, float)
    assert isinstance(conf, float)
    assert "model_version" in meta
    assert "prediction_timestamp" in meta
    
    uplift, conf_uplift, meta_uplift = service.predict_uplift(tx, "INCENTIVE")
    assert isinstance(uplift, float)
    assert isinstance(conf_uplift, float)
    assert "model_version" in meta_uplift

def test_deterministic_behavior():
    service = PredictionService()
    service.load_models()
    
    tx = {
        "amount_minor": 20000,
        "state_version": 1,
        "fraud_score": 0.2,
        "risk_profile": "low",
        "payment_method": "wallet"
    }
    
    prob1, _, _ = service.predict_natural_recovery(tx)
    prob2, _, _ = service.predict_natural_recovery(tx)
    
    assert prob1 == prob2 # Should be perfectly deterministic

def test_model_loading_error():
    service = PredictionService(models_dir="/tmp/nonexistent_models_12345")
    with pytest.raises(RuntimeError) as exc:
        service.load_models()
    assert "Could not load ML models" in str(exc.value)

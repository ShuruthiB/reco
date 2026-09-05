import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib

class FeatureEngineer:
    def __init__(self):
        self.numeric_features = ["amount_minor", "state_version", "fraud_score"]
        self.categorical_features = ["risk_profile", "payment_method"]
        
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, self.numeric_features),
                ('cat', categorical_transformer, self.categorical_features)
            ]
        )
        
        self.is_fitted = False
        
    def fit(self, X: pd.DataFrame):
        self.preprocessor.fit(X)
        self.is_fitted = True
        
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.is_fitted:
            raise ValueError("FeatureEngineer is not fitted yet.")
            
        transformed_array = self.preprocessor.transform(X)
        
        # Reconstruct DataFrame with feature names
        num_cols = self.numeric_features
        cat_cols = self.preprocessor.named_transformers_['cat'].named_steps['onehot'].get_feature_names_out(self.categorical_features)
        feature_names = list(num_cols) + list(cat_cols)
        
        return pd.DataFrame(transformed_array, columns=feature_names, index=X.index)

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self.fit(X)
        return self.transform(X)

    def save(self, filepath: str):
        joblib.dump(self.preprocessor, filepath)

    def load(self, filepath: str):
        self.preprocessor = joblib.load(filepath)
        self.is_fitted = True

"""
return_predictor.py — XGBoost model to predict next-quarter asset class returns

Features engineered from the monthly return series:
  - Rolling 3-month, 6-month, 12-month mean return (momentum)
  - Rolling 3-month, 6-month volatility (risk)
  - Return-to-risk ratio (Sharpe-like)

Target: actual return in the following month (1-step-ahead prediction)

The trained model is serialized to portfolio_optimizer/models/return_predictor.pkl
and metadata (RMSE, R², feature importance) to model_metadata.json.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    from sklearn.ensemble import GradientBoostingRegressor  # fallback

MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "return_predictor.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
METADATA_PATH = MODELS_DIR / "model_metadata.json"

ASSET_NAMES = [
    "Equity_LargeCap",
    "Equity_MidCap",
    "Debt_ShortTerm",
    "Gold",
    "Fixed_Deposit",
]


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build feature matrix from monthly return series.

    For each asset class, compute rolling momentum and vol features,
    then create a flat feature vector per month.
    """
    features = pd.DataFrame(index=df.index)

    for asset in df.columns:
        s = df[asset]
        features[f"{asset}_ret3m"]  = s.rolling(3).mean()
        features[f"{asset}_ret6m"]  = s.rolling(6).mean()
        features[f"{asset}_ret12m"] = s.rolling(12).mean()
        features[f"{asset}_vol3m"]  = s.rolling(3).std()
        features[f"{asset}_vol6m"]  = s.rolling(6).std()
        features[f"{asset}_sharpe3m"] = (
            s.rolling(3).mean() / (s.rolling(3).std() + 1e-8)
        )

    # Drop rows with NaN (first 12 months used for window)
    features = features.dropna()
    return features


def _build_targets(df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """
    Build target matrix: next-month return for each asset.
    Aligns with the feature index (shifted by 1).
    """
    # Shift returns back by 1 to get "next month" return
    targets = df.shift(-1).reindex(features.index).dropna()
    features = features.reindex(targets.index)
    return features, targets


def train(df: pd.DataFrame) -> Dict:
    """
    Train one XGBoost regressor per asset class using TimeSeriesSplit CV.

    Returns:
        dict with per-asset metrics (R², RMSE) and overall feature importance
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    features = _build_features(df)
    features, targets = _build_targets(df, features)

    scaler = StandardScaler()
    X = scaler.fit_transform(features)
    feature_names = list(features.columns)

    models: Dict[str, object] = {}
    metrics: Dict[str, dict] = {}
    importances_all: Dict[str, list] = {}

    tscv = TimeSeriesSplit(n_splits=5)

    for asset in ASSET_NAMES:
        y = targets[asset].values

        # Collect OOF predictions
        oof_preds = np.zeros(len(y))
        for train_idx, val_idx in tscv.split(X):
            if XGB_AVAILABLE:
                model = xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbosity=0,
                )
            else:
                model = GradientBoostingRegressor(
                    n_estimators=200, max_depth=4, learning_rate=0.05,
                    subsample=0.8, random_state=42
                )
            model.fit(X[train_idx], y[train_idx])
            oof_preds[val_idx] = model.predict(X[val_idx])

        # Refit on full data for the final model
        if XGB_AVAILABLE:
            final_model = xgb.XGBRegressor(
                n_estimators=200, max_depth=4, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0
            )
        else:
            final_model = GradientBoostingRegressor(
                n_estimators=200, max_depth=4, learning_rate=0.05,
                subsample=0.8, random_state=42
            )
        final_model.fit(X, y)
        models[asset] = final_model

        # Metrics
        r2  = float(r2_score(y, oof_preds))
        rmse = float(np.sqrt(mean_squared_error(y, oof_preds)))
        metrics[asset] = {
            "r2": round(r2, 4),
            "rmse_monthly": round(rmse, 6),
            "rmse_annual_pct": round(rmse * np.sqrt(12) * 100, 3),
        }

        # Feature importance (normalised)
        imp = final_model.feature_importances_
        imp_norm = (imp / imp.sum()).tolist()
        importances_all[asset] = dict(zip(feature_names, imp_norm))

    # Save
    joblib.dump({"models": models, "feature_names": feature_names}, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    # Top-10 features across all assets (averaged)
    avg_imp: Dict[str, float] = {}
    for feat in feature_names:
        avg_imp[feat] = float(
            np.mean([importances_all[a].get(feat, 0) for a in ASSET_NAMES])
        )
    top10 = sorted(avg_imp.items(), key=lambda x: x[1], reverse=True)[:10]

    metadata = {
        "algorithm": "XGBoost" if XGB_AVAILABLE else "GradientBoosting",
        "n_assets": len(ASSET_NAMES),
        "asset_names": ASSET_NAMES,
        "cv_strategy": "TimeSeriesSplit(n_splits=5)",
        "per_asset_metrics": metrics,
        "top_features": [{"feature": f, "importance": round(i, 4)} for f, i in top10],
        "overall_r2": round(float(np.mean([m["r2"] for m in metrics.values()])), 4),
        "overall_rmse_annual_pct": round(
            float(np.mean([m["rmse_annual_pct"] for m in metrics.values()])), 3
        ),
    }

    with open(METADATA_PATH, "w") as fh:
        json.dump(metadata, fh, indent=2)

    print(f"✅ Model trained. Overall R²={metadata['overall_r2']:.4f}")
    return metadata


def predict(df_recent: pd.DataFrame) -> Dict[str, float]:
    """
    Predict next-month returns for all asset classes.

    Args:
        df_recent: DataFrame with at least 12 months of returns (all 5 assets)

    Returns:
        dict mapping asset_name → predicted monthly return (float)
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model not trained yet. Run portfolio_optimizer/train_model.py first."
        )

    artifact = joblib.load(MODEL_PATH)
    scaler: StandardScaler = joblib.load(SCALER_PATH)
    models: Dict = artifact["models"]
    feature_names: list = artifact["feature_names"]

    features = _build_features(df_recent)
    if features.empty:
        raise ValueError("Not enough return history to compute features (need ≥12 months).")

    # Use the most recent row
    last_row = features.iloc[[-1]][feature_names]
    X = scaler.transform(last_row)

    predictions = {}
    for asset in ASSET_NAMES:
        predictions[asset] = float(models[asset].predict(X)[0])

    return predictions


def get_metadata() -> Dict:
    """Load and return saved model metadata."""
    if not METADATA_PATH.exists():
        return {}
    with open(METADATA_PATH) as fh:
        return json.load(fh)

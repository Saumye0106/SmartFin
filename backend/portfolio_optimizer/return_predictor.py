"""
return_predictor.py — XGBoost model to predict next-month asset class returns

Each asset's model is trained independently on that asset's OWN return
history (own rolling momentum/vol features -> its own next-month return),
rather than one shared row-aligned matrix across all assets. This matters
because the 9-asset universe now spans real market data with very
different listing dates (Nifty 50 since 2007 vs. a Mid-Cap ETF since
2024) — a shared matrix would drop every row where ANY asset lacks a full
12-month trailing window, which was measured to leave only ~15 usable
rows total (see AGENTS.md). Training per-asset lets Nifty 50 / Gold /
Debt use ~200 real months while newer assets use whatever they actually
have, each asset's model reflecting only its own real availability.

Features (computed from an asset's own monthly return series):
  - Rolling 3-month, 6-month, 12-month mean return (momentum)
  - Rolling 3-month, 6-month volatility (risk)
  - Return-to-risk ratio (Sharpe-like)

Target: actual return in the following month (1-step-ahead prediction)

Assets without enough real history to train reliably (fewer than
MIN_TRAIN_ROWS observations after feature/target construction) are
skipped for training; predict() falls back to that asset's own simple
historical mean return instead of a trained model, and this is recorded
in metadata as `status: insufficient_data` rather than silently omitted.

The trained models are serialized to portfolio_optimizer/models/return_predictor.pkl
and metadata (RMSE, R², feature importance, per-asset training window) to
model_metadata.json.
"""

from __future__ import annotations

import json
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
METADATA_PATH = MODELS_DIR / "model_metadata.json"

ASSET_NAMES = [
    "Equity_LargeCap",
    "Equity_MidCap",
    "Equity_SmallCap",
    "International_Equity",
    "Debt_ShortTerm",
    "Gold",
    "Silver",
    "REIT",
    "Fixed_Deposit",
]

FEATURE_COLUMNS = ["ret3m", "ret6m", "ret12m", "vol3m", "vol6m", "sharpe3m"]

# Need enough rows for TimeSeriesSplit to produce meaningful (non-degenerate)
# folds. Below this, we skip training and fall back to the historical mean.
MIN_TRAIN_ROWS = 20


def _build_asset_features(series: pd.Series) -> pd.DataFrame:
    """Build rolling momentum/vol features from a single asset's own return series."""
    features = pd.DataFrame(index=series.index)
    features["ret3m"] = series.rolling(3).mean()
    features["ret6m"] = series.rolling(6).mean()
    features["ret12m"] = series.rolling(12).mean()
    features["vol3m"] = series.rolling(3).std()
    features["vol6m"] = series.rolling(6).std()
    features["sharpe3m"] = features["ret3m"] / (features["vol3m"] + 1e-8)
    return features.dropna()


def _build_asset_target(series: pd.Series, features: pd.DataFrame) -> pd.Series:
    """Next-month return, aligned to the feature index (shifted by 1)."""
    target = series.shift(-1).reindex(features.index).dropna()
    return target


def _make_model():
    if XGB_AVAILABLE:
        return xgb.XGBRegressor(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0,
        )
    return GradientBoostingRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42,
    )


def train(df: pd.DataFrame) -> Dict:
    """
    Train one XGBoost regressor per asset class, each on that asset's own
    available real history, using TimeSeriesSplit CV.

    Returns:
        dict with per-asset metrics (R², RMSE, training window) and overall
        feature importance across the assets that had enough data to train.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    models: Dict[str, object] = {}
    scalers: Dict[str, StandardScaler] = {}
    fallback_means: Dict[str, float] = {}
    metrics: Dict[str, dict] = {}
    importances_all: Dict[str, list] = {}

    for asset in ASSET_NAMES:
        if asset not in df.columns:
            continue

        series = df[asset].dropna()
        fallback_means[asset] = float(series.mean()) if len(series) else 0.0

        features = _build_asset_features(series)
        target = _build_asset_target(series, features)
        features = features.reindex(target.index)

        if len(target) < MIN_TRAIN_ROWS:
            metrics[asset] = {
                "status": "insufficient_data",
                "months_available": int(len(series)),
                "usable_rows": int(len(target)),
                "min_required": MIN_TRAIN_ROWS,
            }
            continue

        if float(np.std(target.values)) < 1e-9:
            # Constant target (e.g. Fixed_Deposit's flat assumed rate) — nothing
            # for a model to learn; predict() will use the (equally constant)
            # historical mean, which is exactly this flat rate.
            metrics[asset] = {"status": "constant_target", "months_available": int(len(series))}
            continue

        scaler = StandardScaler()
        X = scaler.fit_transform(features[FEATURE_COLUMNS])
        y = target.values

        n_splits = min(5, max(2, len(y) // 6))
        tscv = TimeSeriesSplit(n_splits=n_splits)

        oof_preds = np.zeros(len(y))
        for train_idx, val_idx in tscv.split(X):
            model = _make_model()
            model.fit(X[train_idx], y[train_idx])
            oof_preds[val_idx] = model.predict(X[val_idx])

        final_model = _make_model()
        final_model.fit(X, y)
        models[asset] = final_model
        scalers[asset] = scaler

        r2 = float(r2_score(y, oof_preds))
        rmse = float(np.sqrt(mean_squared_error(y, oof_preds)))
        metrics[asset] = {
            "status": "trained",
            "r2": round(r2, 4),
            "rmse_monthly": round(rmse, 6),
            "rmse_annual_pct": round(rmse * np.sqrt(12) * 100, 3),
            "training_window": {
                "start": target.index[0].strftime("%Y-%m-%d"),
                "end": target.index[-1].strftime("%Y-%m-%d"),
                "usable_rows": int(len(target)),
            },
            "cv_splits": n_splits,
        }

        imp = final_model.feature_importances_
        imp_norm = (imp / imp.sum()).tolist()
        importances_all[asset] = dict(zip(FEATURE_COLUMNS, imp_norm))

    joblib.dump({
        "models": models,
        "scalers": scalers,
        "fallback_means": fallback_means,
        "feature_columns": FEATURE_COLUMNS,
    }, MODEL_PATH)

    trained_assets = [a for a in ASSET_NAMES if metrics.get(a, {}).get("status") == "trained"]

    avg_imp: Dict[str, float] = {}
    for feat in FEATURE_COLUMNS:
        vals = [importances_all[a].get(feat, 0) for a in trained_assets]
        avg_imp[feat] = float(np.mean(vals)) if vals else 0.0
    top_features = sorted(avg_imp.items(), key=lambda x: x[1], reverse=True)

    r2_values = [metrics[a]["r2"] for a in trained_assets]
    rmse_values = [metrics[a]["rmse_annual_pct"] for a in trained_assets]

    metadata = {
        "algorithm": "XGBoost" if XGB_AVAILABLE else "GradientBoosting",
        "n_assets": len(ASSET_NAMES),
        "asset_names": ASSET_NAMES,
        "trained_assets": trained_assets,
        "skipped_assets": [a for a in ASSET_NAMES if a not in trained_assets],
        "cv_strategy": "TimeSeriesSplit, per-asset n_splits (2-5, scaled to available rows)",
        "per_asset_metrics": metrics,
        "top_features": [{"feature": f, "importance": round(i, 4)} for f, i in top_features],
        "overall_r2": round(float(np.mean(r2_values)), 4) if r2_values else None,
        "overall_rmse_annual_pct": round(float(np.mean(rmse_values)), 3) if rmse_values else None,
    }

    with open(METADATA_PATH, "w") as fh:
        json.dump(metadata, fh, indent=2)

    r2_display = f"{metadata['overall_r2']:.4f}" if metadata["overall_r2"] is not None else "n/a"
    print(f"Model trained on {len(trained_assets)}/{len(ASSET_NAMES)} assets. Overall R²={r2_display}")
    if metadata["skipped_assets"]:
        print(f"Skipped (insufficient real history): {', '.join(metadata['skipped_assets'])}")
    return metadata


def predict(df_recent: pd.DataFrame) -> Dict[str, float]:
    """
    Predict next-month returns for all asset classes.

    Assets with a trained model use it; assets skipped during training
    (insufficient real history) fall back to their own historical mean
    monthly return rather than failing the whole prediction.

    Args:
        df_recent: DataFrame of monthly returns, columns = asset names.

    Returns:
        dict mapping asset_name -> predicted monthly return (float)
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Model not trained yet. Run portfolio_optimizer/train_model.py first."
        )

    artifact = joblib.load(MODEL_PATH)
    models: Dict = artifact["models"]
    scalers: Dict = artifact["scalers"]
    fallback_means: Dict = artifact["fallback_means"]
    feature_columns: list = artifact["feature_columns"]

    predictions: Dict[str, float] = {}
    for asset in ASSET_NAMES:
        if asset not in df_recent.columns:
            predictions[asset] = fallback_means.get(asset, 0.0)
            continue

        if asset in models:
            series = df_recent[asset].dropna()
            features = _build_asset_features(series)
            if not features.empty:
                last_row = features.iloc[[-1]][feature_columns]
                X = scalers[asset].transform(last_row)
                predictions[asset] = float(models[asset].predict(X)[0])
                continue

        # Fall back to this asset's own historical mean (still real data,
        # just not enough of it to justify a trained per-month model).
        predictions[asset] = fallback_means.get(asset, 0.0)

    return predictions


def get_metadata() -> Dict:
    """Load and return saved model metadata."""
    if not METADATA_PATH.exists():
        return {}
    with open(METADATA_PATH) as fh:
        return json.load(fh)

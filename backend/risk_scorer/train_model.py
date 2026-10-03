"""
Train the financial-distress risk model and write an honest report of how good it is.

    python -X utf8 risk_scorer/train_model.py                 # from backend/
    python -X utf8 risk_scorer/train_model.py --refresh-data  # download the data first

What it does:
  1. 5-fold stratified cross-validation, out-of-fold predictions only, for
     a logistic-regression baseline and the XGBoost model.
  2. Scores the XGBoost model twice per fold: with credit-card utilization
     and with it hidden, because SmartFin users without a card have none.
     Half of each training fold has utilization hidden so one model learns both cases.
  3. Checks calibration (predicted vs observed distress rate per decile).
  4. Fits the final model on all rows and saves it with its metadata.

Outputs: models/risk_model.json (XGBoost native format, not a pickle, so it
doesn't break across library versions) and models/model_metadata.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from risk_scorer.features import AGE_BANDS, FEATURES, MONOTONE, age_band, prepare_training_frame  # noqa: E402
from risk_scorer.fetch_data import DATA_PATH, SOURCE, fetch_and_save  # noqa: E402

MODEL_DIR = Path(__file__).parent / "models"
SEED = 42
N_SPLITS = 5
HIDE_UTILIZATION_SHARE = 0.5

XGB_PARAMS = dict(
    n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
    min_child_weight=20, tree_method="hist", n_jobs=4, random_state=SEED,
    monotone_constraints=tuple(MONOTONE[f] for f in FEATURES),
)


def _log1p_clip(a):
    return np.log1p(np.clip(a, 0, None))


def make_baseline():
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True),
                         FunctionTransformer(_log1p_clip), StandardScaler(),
                         LogisticRegression(max_iter=2000))


def hide_utilization(X: pd.DataFrame, share: float, rng: np.random.Generator) -> pd.DataFrame:
    X = X.copy()
    X.loc[rng.random(len(X)) < share, "utilization"] = np.nan
    return X


def metrics(y, p) -> dict:
    return {"auc": round(float(roc_auc_score(y, p)), 4),
            "pr_auc": round(float(average_precision_score(y, p)), 4),
            "brier": round(float(brier_score_loss(y, p)), 5)}


def calibration_table(y, p, bins: int = 10) -> list[dict]:
    order = np.argsort(p)
    out = []
    for chunk in np.array_split(order, bins):
        out.append({"predicted": round(float(p[chunk].mean()), 4), "observed": round(float(y[chunk].mean()), 4),
                    "n": int(len(chunk))})
    return out


def train(refresh_data: bool = False) -> dict:
    if refresh_data or not DATA_PATH.exists():
        print("Downloading training data from OpenML ...")
        fetch_and_save()
    X, y = prepare_training_frame(pd.read_csv(DATA_PATH))
    print(f"{len(y):,} borrowers, {int(y.sum()):,} in distress ({y.mean():.2%})")

    rng = np.random.default_rng(SEED)
    no_util = X.assign(utilization=np.nan)
    oof = {k: np.zeros(len(y)) for k in ("baseline", "baseline_no_util", "xgb", "xgb_no_util")}
    for fold, (tr, te) in enumerate(StratifiedKFold(N_SPLITS, shuffle=True, random_state=SEED).split(X, y), 1):
        base = make_baseline().fit(X.iloc[tr], y[tr])
        oof["baseline"][te] = base.predict_proba(X.iloc[te])[:, 1]
        base_nu = make_baseline().fit(X.iloc[tr].drop(columns="utilization"), y[tr])
        oof["baseline_no_util"][te] = base_nu.predict_proba(X.iloc[te].drop(columns="utilization"))[:, 1]

        model = xgb.XGBClassifier(**XGB_PARAMS).fit(hide_utilization(X.iloc[tr], HIDE_UTILIZATION_SHARE, rng), y[tr])
        oof["xgb"][te] = model.predict_proba(X.iloc[te])[:, 1]
        oof["xgb_no_util"][te] = model.predict_proba(no_util.iloc[te])[:, 1]
        print(f"  fold {fold}: xgb AUC {roc_auc_score(y[te], oof['xgb'][te]):.4f}"
              f" (utilization hidden: {roc_auc_score(y[te], oof['xgb_no_util'][te]):.4f})")

    results = {k: metrics(y, p) for k, p in oof.items()}
    base_rate = float(y.mean())
    results["always_base_rate"] = {"auc": 0.5, "pr_auc": round(base_rate, 4), "brier": round(base_rate * (1 - base_rate), 5)}
    print(f"\n{'model':38} {'AUC':>7} {'PR-AUC':>7} {'Brier':>8}")
    for name, key in (("always predict the base rate", "always_base_rate"),
                      ("logistic regression", "baseline"), ("XGBoost", "xgb"),
                      ("logistic regression, no utilization", "baseline_no_util"),
                      ("XGBoost, utilization hidden", "xgb_no_util")):
        r = results[key]
        print(f"{name:38} {r['auc']:7.4f} {r['pr_auc']:7.4f} {r['brier']:8.5f}")

    calib = {"with_utilization": calibration_table(y, oof["xgb"]),
             "without_utilization": calibration_table(y, oof["xgb_no_util"])}
    print("\nCalibration, XGBoost with utilization (deciles of predicted risk):")
    for row in calib["with_utilization"]:
        print(f"  predicted {row['predicted']:.3f}   observed {row['observed']:.3f}")

    final = xgb.XGBClassifier(**XGB_PARAMS).fit(hide_utilization(X, HIDE_UTILIZATION_SHARE, rng), y)
    gain = final.get_booster().get_score(importance_type="total_gain")
    total = sum(gain.values()) or 1.0

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    final.get_booster().save_model(str(MODEL_DIR / "risk_model.json"))
    # Out-of-fold risk quantiles of the reference borrowers, per age band and per
    # "is utilization known", so a user is ranked against like-for-like predictions.
    bands = X["age"].map(age_band)
    grid = np.linspace(0, 1, 201)
    quantiles = {
        arm: {band: [round(float(q), 6) for q in np.quantile(oof[key][(bands == band).to_numpy()], grid)]
              for band in sorted(bands.unique())}
        for arm, key in (("with_utilization", "xgb"), ("without_utilization", "xgb_no_util"))
    }
    band_stats = {band: {"n": int((bands == band).sum()), "distress_rate": round(float(y[(bands == band).to_numpy()].mean()), 4)}
                  for band in sorted(bands.unique())}
    print("\nAge bands:", band_stats)
    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model_type": "XGBoost classifier (monotone-constrained)",
        "xgboost_version": xgb.__version__,
        "data_source": SOURCE,
        "n_rows": int(len(y)),
        "n_positive": int(y.sum()),
        "base_rate": round(base_rate, 4),
        "features": FEATURES,
        "monotone_constraints": MONOTONE,
        "validation": f"{N_SPLITS}-fold stratified cross-validation, out-of-fold predictions",
        "metrics": results,
        "calibration": calib,
        "feature_importance": {f: round(gain.get(f, 0.0) / total, 4) for f in FEATURES},
        "age_bands": list(AGE_BANDS),
        "age_band_stats": band_stats,
        "risk_quantiles": quantiles,
        "caveats": [
            "Trained on US consumer borrowers (2011 data), not Indian users: the ranking of risk factors "
            "transfers better than the absolute probabilities.",
            "The label is 90+ days past due within 2 years, i.e. credit distress, not overall financial wellbeing.",
            "A user with no loan history and no credit card is scored on age and debt ratio alone, where the model is weak.",
        ],
    }
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\nSaved {MODEL_DIR / 'risk_model.json'} and model_metadata.json")
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh-data", action="store_true", help="download the dataset again before training")
    train(ap.parse_args().refresh_data)

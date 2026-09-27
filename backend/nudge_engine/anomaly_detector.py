"""
anomaly_detector.py — Per-user Isolation Forest for spending anomaly detection.

Design:
- One Isolation Forest model is trained per user from their own historical data.
  This makes it personalized — what's "anomalous" is relative to that user's
  own baseline, not a global population.
- Models are cached in memory (per-user dict) and retrained when stale or missing.
- Anomaly scores are mapped to a 0–1 scale (higher = more anomalous).
- The detector also runs a simple "budget-bust predictor" using a Random Forest
  classifier when enough data is available (≥12 weeks).
"""

from __future__ import annotations

import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    """
    Trains and runs a per-user Isolation Forest on weekly expense features.
    """

    def __init__(self, contamination: float = 0.15):
        """
        Args:
            contamination: Expected fraction of anomalous weeks in the data.
                           0.15 = assume ~15% of weeks are unusual.
        """
        self.contamination = contamination
        self._models: Dict[int, Dict] = {}  # user_id → {model, scaler, trained_at}

    def _train(self, feature_df: pd.DataFrame, user_id: int) -> Dict:
        """Train Isolation Forest on user's feature matrix."""
        X = feature_df.values.astype(float)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            iso = IsolationForest(
                n_estimators=200,
                contamination=self.contamination,
                max_samples="auto",
                random_state=42,
            )
            iso.fit(X_scaled)

        # Budget-bust classifier (optional, needs ≥12 rows)
        bb_classifier = None
        if len(feature_df) >= 12:
            # Label weeks where ANY category exceeds 2x its rolling average
            ratio_cols = [c for c in feature_df.columns if c.endswith("_ratio")]
            if ratio_cols:
                labels = (feature_df[ratio_cols].max(axis=1) > 1.8).astype(int)
                if labels.sum() >= 2:  # At least 2 positive examples
                    try:
                        rf = RandomForestClassifier(
                            n_estimators=100, max_depth=4, random_state=42
                        )
                        rf.fit(X_scaled, labels.values)
                        bb_classifier = rf
                    except Exception:
                        pass

        model_dict = {
            "iso": iso,
            "scaler": scaler,
            "feature_names": list(feature_df.columns),
            "bb_classifier": bb_classifier,
        }
        self._models[user_id] = model_dict
        return model_dict

    def score(
        self,
        feature_df: pd.DataFrame,
        user_id: int,
    ) -> Tuple[pd.Series, Optional[float]]:
        """
        Compute anomaly scores for all weeks in feature_df.

        Returns:
            (anomaly_scores, budget_bust_probability)
              anomaly_scores: pd.Series indexed like feature_df, values in [0, 1]
                              (higher = more anomalous)
              budget_bust_probability: float 0–1 or None if classifier unavailable
        """
        if user_id not in self._models:
            self._train(feature_df, user_id)

        m = self._models[user_id]
        X = feature_df.reindex(columns=m["feature_names"], fill_value=0).values.astype(float)
        X_scaled = m["scaler"].transform(X)

        # Isolation Forest: decision_function returns negative = anomaly
        raw_scores = m["iso"].decision_function(X_scaled)
        # Map to [0, 1]: lower decision_function → higher anomaly score
        anomaly_scores = 1 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-8)
        anomaly_series = pd.Series(anomaly_scores, index=feature_df.index)

        # Budget-bust probability for the most recent week
        bb_prob = None
        if m["bb_classifier"] is not None:
            try:
                last_X = X_scaled[[-1]]
                bb_prob = float(m["bb_classifier"].predict_proba(last_X)[0, 1])
            except Exception:
                pass

        return anomaly_series, bb_prob

    def get_top_anomalous_weeks(
        self,
        feature_df: pd.DataFrame,
        anomaly_scores: pd.Series,
        top_n: int = 3,
    ) -> List[Dict]:
        """
        Return the top-N most anomalous weeks with per-category breakdown.

        Returns:
            List of dicts: {week, anomaly_score, top_categories}
        """
        top_idx = anomaly_scores.nlargest(top_n).index
        results = []

        # Ratio columns tell us *which* categories are unusual
        ratio_cols = {c: c.replace("_ratio", "") for c in feature_df.columns if c.endswith("_ratio")}

        for week in top_idx:
            row = feature_df.loc[week]
            score = float(anomaly_scores[week])

            cat_signals = []
            for ratio_col, slug in ratio_cols.items():
                if ratio_col in row.index:
                    ratio = float(row[ratio_col])
                    raw_val = float(row.get(slug, 0))
                    if ratio > 1.2:  # Spending > 120% of rolling average
                        cat_signals.append({
                            "category": slug,
                            "ratio_vs_avg": round(ratio, 2),
                            "normalised_spend": round(raw_val, 4),
                        })

            cat_signals.sort(key=lambda x: x["ratio_vs_avg"], reverse=True)

            results.append({
                "week_start": week.isoformat() if hasattr(week, "isoformat") else str(week),
                "anomaly_score": round(score, 3),
                "severity": _severity(score),
                "top_categories": cat_signals[:3],
            })

        return results

    def get_patterns(self, feature_df: pd.DataFrame, user_id: int) -> List[Dict]:
        """
        Identify recurring spending patterns (e.g., shopping spike in week 1).

        Returns:
            List of pattern dicts: {category, pattern_description, avg_ratio_week1}
        """
        if "week_of_month" not in feature_df.columns:
            return []

        patterns = []
        ratio_cols = {c: c.replace("_ratio", "") for c in feature_df.columns if c.endswith("_ratio")}

        for ratio_col, slug in ratio_cols.items():
            if ratio_col not in feature_df.columns:
                continue
            # Week-1 vs other weeks average
            week1_mask = feature_df["week_of_month"] == 1
            if week1_mask.sum() < 2:
                continue
            avg_week1 = feature_df.loc[week1_mask, ratio_col].mean()
            avg_other = feature_df.loc[~week1_mask, ratio_col].mean()

            if avg_week1 > 1.3 and avg_week1 > avg_other * 1.2:
                patterns.append({
                    "category": slug,
                    "display_category": slug.replace("_", " ").title(),
                    "pattern": "week1_spike",
                    "description": (
                        f"You typically spend {avg_week1:.1f}x your usual amount on "
                        f"{slug.replace('_', ' ').title()} in the first week of the month."
                    ),
                    "avg_ratio_week1": round(float(avg_week1), 2),
                    "avg_ratio_other": round(float(avg_other), 2),
                })

        return patterns


def _severity(score: float) -> str:
    if score >= 0.75:
        return "high"
    elif score >= 0.50:
        return "medium"
    else:
        return "low"

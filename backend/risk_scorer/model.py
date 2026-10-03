"""
Serve the financial-distress risk model: probability, 0-100 score, and what drives it.

score = share of reference borrowers in the user's own age band who are riskier
        than this user (percentile of predicted risk, flipped so higher is better).
drivers = the model's own per-feature contributions (TreeSHAP via XGBoost's
          pred_contribs), in log-odds, so the explanation is what the model
          actually computed rather than a separate rule.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import xgboost as xgb

from risk_scorer.features import ACTIONABLE, DEFAULT_AGE, FEATURES, LABELS, age_band

MODEL_DIR = Path(__file__).parent / "models"


class RiskModel:
    def __init__(self, model_dir: Path = MODEL_DIR):
        self.booster = xgb.Booster()
        self.booster.load_model(str(model_dir / "risk_model.json"))
        self.metadata = json.loads((model_dir / "model_metadata.json").read_text(encoding="utf-8"))
        self._quantiles = {arm: {band: np.asarray(q) for band, q in bands.items()}
                           for arm, bands in self.metadata["risk_quantiles"].items()}

    def _matrix(self, features: dict) -> xgb.DMatrix:
        row = np.array([[features.get(f, np.nan) for f in FEATURES]], dtype=float)
        return xgb.DMatrix(row, feature_names=FEATURES, missing=np.nan)

    def probability(self, features: dict) -> float:
        return float(self.booster.predict(self._matrix(features))[0])

    def score(self, p: float, features: dict) -> float:
        """0-100: share of same-age reference borrowers with a higher predicted risk."""
        arm = "without_utilization" if np.isnan(features.get("utilization", np.nan)) else "with_utilization"
        q = self._quantiles[arm][age_band(features.get("age") or DEFAULT_AGE)]
        # Midpoint of the tied range, so the large group with identical clean records isn't ranked at its edge.
        rank = (np.searchsorted(q, p, side="left") + np.searchsorted(q, p, side="right")) / 2 / len(q)
        return round(100.0 * float(np.clip(1.0 - rank, 0.0, 1.0)), 1)

    def drivers(self, features: dict) -> list[dict]:
        """Per-feature push on the risk, largest first. impact > 0 raises risk."""
        contribs = self.booster.predict(self._matrix(features), pred_contribs=True)[0]
        out = []
        for name, c in zip(FEATURES, contribs[:-1]):  # last entry is the bias term
            value = features.get(name, np.nan)
            out.append({
                "feature": name,
                "label": LABELS[name],
                "value": None if value is None or np.isnan(value) else round(float(value), 4),
                "impact": round(float(c), 4),
                "direction": "raises risk" if c > 0.02 else "lowers risk" if c < -0.02 else "neutral",
                "actionable": name in ACTIONABLE,
            })
        return sorted(out, key=lambda d: -abs(d["impact"]))

    def assess(self, features: dict) -> dict:
        p = self.probability(features)
        return {
            "risk_probability": round(p, 4),
            "score": self.score(p, features),
            "age_band": age_band(features.get("age") or DEFAULT_AGE),
            "average_risk": self.metadata["base_rate"],
            "drivers": self.drivers(features),
            "inputs_missing": [f for f in FEATURES if np.isnan(features.get(f, np.nan))],
        }


@lru_cache(maxsize=1)
def get_model() -> RiskModel:
    return RiskModel()

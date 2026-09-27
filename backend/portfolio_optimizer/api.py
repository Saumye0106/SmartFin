"""
portfolio_optimizer/api.py — Flask Blueprint for portfolio optimization endpoints

Endpoints:
  POST /api/portfolio/optimize   — Compute personalized optimal portfolio
  GET  /api/portfolio/frontier   — Return efficient frontier data for charting
  GET  /api/portfolio/model-info — Model metadata (accuracy, feature importance)
  POST /api/portfolio/whatif     — Compare portfolios across risk scenarios
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from portfolio_optimizer.data_loader import load_or_generate_data, get_asset_summary
from portfolio_optimizer.return_predictor import predict as predict_returns, get_metadata, MODEL_PATH
from portfolio_optimizer.markowitz_engine import MarkowitzEngine
from portfolio_optimizer.personalizer import Personalizer

portfolio_bp = Blueprint("portfolio", __name__, url_prefix="/api/portfolio")

# ── Shared state (loaded once at import time) ────────────────────────────────

_df_cache = None
_engine_cache = None


def _get_engine() -> MarkowitzEngine:
    """Load return data and build Markowitz engine (cached)."""
    global _df_cache, _engine_cache
    if _engine_cache is None:
        _df_cache = load_or_generate_data()
        _engine_cache = MarkowitzEngine.from_return_series(_df_cache)
    return _engine_cache


def _get_predicted_mu() -> np.ndarray | None:
    """Try to get ML-predicted expected returns (falls back to historical if model missing)."""
    if not MODEL_PATH.exists():
        return None
    try:
        df = load_or_generate_data()
        preds = predict_returns(df)  # dict: asset → monthly return
        from portfolio_optimizer.data_loader import ASSET_NAMES
        return np.array([preds[a] * 12 for a in ASSET_NAMES])  # annualise
    except Exception:
        return None


# ── Endpoints ────────────────────────────────────────────────────────────────

@portfolio_bp.route("/optimize", methods=["POST"])
@jwt_required()
def optimize():
    """
    Compute the personalized optimal portfolio for the authenticated user.

    Request body:
    {
      "risk_score": 6,           // 1-10, required (from RiskAssessment)
      "investable_amount": 50000 // INR, optional (default 10000)
    }

    Response:
    {
      "success": true,
      "portfolio": { ... },      // allocations, weights, projections
      "engine": "ml_predicted|historical",
      "model_metadata": { ... }  // XGBoost stats
    }
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    risk_score = data.get("risk_score")
    if risk_score is None:
        return jsonify({"success": False, "error": "risk_score is required (1-10)"}), 400
    try:
        risk_score = int(risk_score)
        if not 1 <= risk_score <= 10:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "risk_score must be an integer between 1 and 10"}), 400

    investable_amount = float(data.get("investable_amount", 10000))
    if investable_amount <= 0:
        return jsonify({"success": False, "error": "investable_amount must be positive"}), 400

    try:
        # Build engine — prefer ML-predicted returns, fall back to historical
        df = load_or_generate_data()
        predicted_mu = _get_predicted_mu()

        if predicted_mu is not None:
            cov_annual = df.cov().values * 12
            engine = MarkowitzEngine(mu_annual=predicted_mu, cov_annual=cov_annual)
            engine_type = "ml_predicted"
        else:
            engine = MarkowitzEngine.from_return_series(df)
            engine_type = "historical"

        # Get optimal portfolio
        portfolio = engine.optimal_for_risk_score(risk_score)

        # Apply user-context personalisation
        personalizer = Personalizer(db_path=_db_path())
        portfolio = personalizer.adjust(portfolio, user_id=int(user_id),
                                        investable_amount=investable_amount)

        # Attach asset class summary for info panel
        summary = get_asset_summary(df)

        return jsonify({
            "success": True,
            "risk_score": risk_score,
            "investable_amount": investable_amount,
            "portfolio": portfolio,
            "engine": engine_type,
            "asset_summary": {
                "mean_annual": {k: round(v * 100, 2) for k, v in summary["mean_annual"].items()},
                "vol_annual":  {k: round(v * 100, 2) for k, v in summary["vol_annual"].items()},
            },
            "model_metadata": get_metadata(),
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@portfolio_bp.route("/frontier", methods=["GET"])
@jwt_required()
def frontier():
    """
    Return the efficient frontier data points for chart visualisation.

    Response: { "success": true, "frontier": [{return, risk, sharpe, weights}, ...] }
    """
    try:
        df = load_or_generate_data()
        predicted_mu = _get_predicted_mu()

        if predicted_mu is not None:
            cov_annual = df.cov().values * 12
            engine = MarkowitzEngine(mu_annual=predicted_mu, cov_annual=cov_annual)
        else:
            engine = MarkowitzEngine.from_return_series(df)

        frontier_pts = engine.efficient_frontier(n_points=60)

        # Also include GMV and Max-Sharpe as special points
        gmv = engine.gmv_portfolio()
        max_sharpe = engine.max_sharpe_portfolio()

        return jsonify({
            "success": True,
            "frontier": frontier_pts,
            "special_portfolios": {
                "gmv": {
                    "return": gmv["expected_return_annual"],
                    "risk": gmv["risk_annual"],
                    "sharpe": gmv["sharpe_ratio"],
                    "label": "Min Risk",
                },
                "max_sharpe": {
                    "return": max_sharpe["expected_return_annual"],
                    "risk": max_sharpe["risk_annual"],
                    "sharpe": max_sharpe["sharpe_ratio"],
                    "label": "Best Sharpe",
                },
            },
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@portfolio_bp.route("/model-info", methods=["GET"])
@jwt_required()
def model_info():
    """Return XGBoost model metadata and training statistics."""
    metadata = get_metadata()
    if not metadata:
        return jsonify({
            "success": False,
            "message": "Model not trained yet. Run portfolio_optimizer/train_model.py",
        }), 404

    return jsonify({"success": True, "metadata": metadata})


@portfolio_bp.route("/whatif", methods=["POST"])
@jwt_required()
def whatif():
    """
    Compare portfolio allocations across multiple risk scenarios.

    Request body:
    {
      "base_risk_score": 5,
      "investable_amount": 50000,
      "scenarios": [
        { "name": "Conservative", "risk_score": 3 },
        { "name": "Moderate",     "risk_score": 5 },
        { "name": "Aggressive",   "risk_score": 8 }
      ]
    }
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    investable_amount = float(data.get("investable_amount", 10000))
    scenarios = data.get("scenarios", [
        {"name": "Conservative", "risk_score": 3},
        {"name": "Moderate",     "risk_score": 5},
        {"name": "Aggressive",   "risk_score": 8},
    ])

    if not scenarios:
        return jsonify({"success": False, "error": "No scenarios provided"}), 400

    try:
        df = load_or_generate_data()
        predicted_mu = _get_predicted_mu()

        if predicted_mu is not None:
            cov_annual = df.cov().values * 12
            engine = MarkowitzEngine(mu_annual=predicted_mu, cov_annual=cov_annual)
        else:
            engine = MarkowitzEngine.from_return_series(df)

        personalizer = Personalizer(db_path=_db_path())
        results = []

        for sc in scenarios:
            sc_risk = max(1, min(10, int(sc.get("risk_score", 5))))
            portfolio = engine.optimal_for_risk_score(sc_risk)
            portfolio = personalizer.adjust(portfolio, user_id=int(user_id),
                                            investable_amount=investable_amount)
            results.append({
                "name": sc.get("name", f"Risk {sc_risk}"),
                "risk_score": sc_risk,
                "portfolio": portfolio,
            })

        return jsonify({"success": True, "scenarios": results, "investable_amount": investable_amount})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _db_path() -> str:
    """Resolve the auth.db path relative to backend/."""
    here = Path(__file__).parent.parent  # backend/
    return str(here / "auth.db")

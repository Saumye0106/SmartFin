"""
nudge_engine/api.py — Flask Blueprint for behavioral nudge endpoints

Endpoints:
  GET /api/nudges/           — Get current nudges for authenticated user
  GET /api/nudges/patterns   — Get recurring spending patterns
  GET /api/nudges/history    — Weekly anomaly score history (for timeline chart)
"""

from __future__ import annotations

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from nudge_engine.feature_builder import FeatureBuilder
from nudge_engine.anomaly_detector import AnomalyDetector
from nudge_engine.nudge_generator import NudgeGenerator

nudge_bp = Blueprint("nudges", __name__, url_prefix="/api/nudges")

# In-memory detector cache (re-trains per request if not cached)
_detector = AnomalyDetector(contamination=0.15)


def _db_path() -> str:
    from db_core import DB_PATH
    return DB_PATH


@nudge_bp.route("/", methods=["GET"])
@jwt_required()
def get_nudges():
    """
    Get personalized spending nudges for the authenticated user.

    Response:
    {
      "success": true,
      "nudges": [ {severity, emoji, title, message, action, ...}, ... ],
      "data_quality": { "weeks_of_data": 12, "sufficient": true },
      "budget_bust_probability": 0.42,
      "model_info": { "algorithm": "IsolationForest", "contamination": 0.15 }
    }
    """
    user_id = get_jwt_identity()

    try:
        builder = FeatureBuilder(db_path=_db_path())
        feature_df, info = builder.build(int(user_id))

        if feature_df is None or not info["sufficient"]:
            return jsonify({
                "success": True,
                "nudges": [{
                    "id": "insufficient_data",
                    "severity": "low",
                    "emoji": "📈",
                    "color": "blue",
                    "label": "Getting Started",
                    "category": None,
                    "title": "Log more expenses to unlock nudges",
                    "message": (
                        f"You have {info['weeks_of_data']} week(s) of expense history. "
                        f"Log expenses for at least 4 weeks to activate your personalized "
                        f"spending anomaly detection model."
                    ),
                    "action": "Go to Budget Manager → Add Expense",
                }],
                "data_quality": info,
                "budget_bust_probability": None,
                "model_info": {"algorithm": "IsolationForest", "status": "insufficient_data"},
            })

        # Run anomaly detection
        anomaly_scores, bb_prob = _detector.score(feature_df, int(user_id))
        anomalous_weeks = _detector.get_top_anomalous_weeks(feature_df, anomaly_scores, top_n=3)
        patterns = _detector.get_patterns(feature_df, int(user_id))

        # Generate nudge cards
        generator = NudgeGenerator()
        nudges = generator.generate_nudges(
            anomalous_weeks=anomalous_weeks,
            patterns=patterns,
            budget_bust_prob=bb_prob,
            weeks_of_data=info["weeks_of_data"],
        )

        return jsonify({
            "success": True,
            "nudges": nudges,
            "data_quality": info,
            "budget_bust_probability": round(bb_prob, 3) if bb_prob is not None else None,
            "model_info": {
                "algorithm": "IsolationForest",
                "contamination": _detector.contamination,
                "weeks_of_data": info["weeks_of_data"],
                "status": "active",
            },
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@nudge_bp.route("/patterns", methods=["GET"])
@jwt_required()
def get_patterns():
    """
    Get recurring spending patterns detected for the user.

    Response:
    {
      "success": true,
      "patterns": [ {category, description, avg_ratio_week1, ...}, ... ],
      "data_quality": { ... }
    }
    """
    user_id = get_jwt_identity()

    try:
        builder = FeatureBuilder(db_path=_db_path())
        feature_df, info = builder.build(int(user_id))

        if feature_df is None or not info["sufficient"]:
            return jsonify({
                "success": True,
                "patterns": [],
                "data_quality": info,
            })

        patterns = _detector.get_patterns(feature_df, int(user_id))
        return jsonify({
            "success": True,
            "patterns": patterns,
            "data_quality": info,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@nudge_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    """
    Return weekly anomaly score history for the timeline chart.

    Response:
    {
      "success": true,
      "history": [ { "week": "2025-01-06", "anomaly_score": 0.32, "severity": "low" }, ... ]
    }
    """
    user_id = get_jwt_identity()

    try:
        builder = FeatureBuilder(db_path=_db_path())
        feature_df, info = builder.build(int(user_id))

        if feature_df is None or not info["sufficient"]:
            return jsonify({"success": True, "history": [], "data_quality": info})

        anomaly_scores, _ = _detector.score(feature_df, int(user_id))

        from nudge_engine.anomaly_detector import _severity
        history = [
            {
                "week": str(idx.date()) if hasattr(idx, "date") else str(idx),
                "anomaly_score": round(float(score), 3),
                "severity": _severity(float(score)),
            }
            for idx, score in anomaly_scores.items()
        ]

        return jsonify({"success": True, "history": history, "data_quality": info})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

"""
Health Score Blueprint
Home health-check, the predict/whatif/model-info endpoints, and
predict-from-budget (which bridges into the budget tracker's data).
The score comes from risk_scorer; see legacy_scorer/service.py.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from db_core import get_db

from budget.service import current_month_string, build_budget_summary, build_analysis_payload_from_summary
from legacy_scorer.model import feature_names, model_data, model_metadata
from legacy_scorer.service import compare_scores, run_prediction_analysis
from risk_scorer.service import get_risk_profile, model_summary, save_risk_profile, user_history

legacy_scorer_bp = Blueprint('legacy_scorer', __name__)


def _current_user_history():
    """Age and payment record of the logged-in user; None for anonymous callers (these routes allow both)."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        return user_history(get_db(), int(identity)) if identity else None
    except Exception:
        return None


def _remember_card_details(data):
    """A logged-in user who types their card limit/balance into the score form shouldn't have to type it again."""
    if data.get('card_limit') is None:
        return
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            save_risk_profile(get_db(), int(identity), data.get('card_limit'), data.get('card_balance'))
    except Exception:
        pass  # saving is a convenience; never block the score on it


@legacy_scorer_bp.route('/api/risk-profile', methods=['GET'])
@jwt_required()
def read_risk_profile():
    """Saved credit-card limit and balance for the logged-in user."""
    return jsonify({'success': True, **get_risk_profile(get_db(), int(get_jwt_identity()))})


@legacy_scorer_bp.route('/api/risk-profile', methods=['PUT'])
@jwt_required()
def write_risk_profile():
    """Save or clear (null) the logged-in user's credit-card limit and balance."""
    payload = request.get_json(silent=True) or {}
    try:
        saved = save_risk_profile(get_db(), int(get_jwt_identity()), payload.get('card_limit'), payload.get('card_balance'))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'success': True, **saved})


@legacy_scorer_bp.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'SmartFin Financial Health API',
        'version': '1.0',
        'model': model_data['model_type'],
        'model_auc': model_metadata['metrics']['xgb']['auc']
    })


@legacy_scorer_bp.route('/api/predict', methods=['POST'])
def predict_score():
    """
    Main prediction endpoint
    Accepts financial data and returns comprehensive analysis
    """
    try:
        data = request.get_json()

        required_fields = ['income', 'emi', 'savings']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            if not isinstance(data[field], (int, float)) or data[field] < 0:
                return jsonify({'error': f'Invalid value for {field}. Must be non-negative number.'}), 400

        _remember_card_details(data)
        return jsonify(run_prediction_analysis(data, _current_user_history()))

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@legacy_scorer_bp.route('/api/predict/from-budget', methods=['POST'])
@jwt_required()
def predict_from_budget():
    """Predict financial health directly from tracked budget + expenses for a month."""
    try:
        user_id = int(get_jwt_identity())
        payload = request.get_json() or {}
        month = payload.get('month', current_month_string())
        summary = build_budget_summary(user_id, month)

        if summary['expense_count'] == 0 and summary['monthly_income'] <= 0:
            return jsonify({'error': 'No budget or expenses found for this month'}), 404

        analysis_input = build_analysis_payload_from_summary(summary)

        # Ensure mandatory fields are present for prediction model.
        for key in ['income', 'emi', 'savings']:
            analysis_input.setdefault(key, 0)

        response = run_prediction_analysis(analysis_input, user_history(get_db(), user_id))
        response['source'] = 'budget_tracker'
        response['month'] = summary['month']
        response['analysis_input'] = analysis_input
        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@legacy_scorer_bp.route('/api/whatif', methods=['POST'])
def what_if_simulation():
    """
    What-if simulation endpoint
    Allows users to test different financial scenarios
    """
    try:
        data = request.get_json()

        # Current scenario
        current_data = data.get('current', {})

        # Modified scenario
        modified_data = data.get('modified', {})

        return jsonify(compare_scores(current_data, modified_data, _current_user_history()))

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@legacy_scorer_bp.route('/api/model-info', methods=['GET'])
def model_info():
    """Get information about the ML model"""
    return jsonify({
        'model_type': model_data['model_type'],
        'features': feature_names,
        'summary': model_summary(),
        'data_source': model_metadata['data_source'],
        'trained_at': model_metadata['trained_at'],
        'metrics': model_metadata['metrics'],
        'calibration': model_metadata['calibration'],
        'feature_importance': model_metadata['feature_importance'],
        'age_band_stats': model_metadata['age_band_stats'],
        'caveats': model_metadata['caveats'],
    })

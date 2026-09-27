"""
Legacy Scorer Blueprint
Home health-check, the original 8-factor predict/whatif/model-info endpoints,
and predict-from-budget (which bridges into the budget tracker's data).
"""

import pandas as pd
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from budget.service import current_month_string, build_budget_summary, build_analysis_payload_from_summary
from legacy_scorer.model import model, feature_names, model_data, model_metadata
from legacy_scorer.service import classify_score, run_prediction_analysis

legacy_scorer_bp = Blueprint('legacy_scorer', __name__)


@legacy_scorer_bp.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'SmartFin Financial Health API',
        'version': '1.0',
        'model': model_data['model_type'],
        'model_accuracy': f"{model_metadata['r2_test']:.2%}"
    })


@legacy_scorer_bp.route('/api/predict', methods=['POST'])
def predict_score():
    """
    Main prediction endpoint
    Accepts financial data and returns comprehensive analysis
    """
    try:
        data = request.get_json()

        # Validate input - new enhanced model requires different fields
        required_fields = ['income', 'emi', 'savings']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            if not isinstance(data[field], (int, float)) or data[field] < 0:
                return jsonify({'error': f'Invalid value for {field}. Must be non-negative number.'}), 400

        return jsonify(run_prediction_analysis(data))

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

        response = run_prediction_analysis(analysis_input)
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

        # Helper function to calculate expenses
        def get_expenses(scenario_data):
            expenses = scenario_data.get('expenses', 0)
            if expenses == 0 and any(k in scenario_data for k in ['rent', 'food', 'travel', 'shopping']):
                expenses = (scenario_data.get('rent', 0) + scenario_data.get('food', 0) +
                           scenario_data.get('travel', 0) + scenario_data.get('shopping', 0))
            return expenses

        # Predict current score
        current_expenses = get_expenses(current_data)
        current_features = pd.DataFrame([[
            current_data.get('income', 0),
            current_expenses,
            current_data.get('savings', 0),
            current_data.get('emi', 0),
            current_data.get('age', 30),
            int(current_data.get('has_loan', False)),
            current_data.get('loan_amount', 0),
            current_data.get('interest_rate', 0)
        ]], columns=feature_names)

        current_score = float(model.predict(current_features)[0])
        current_score = max(0, min(100, round(current_score, 2)))

        # Predict modified score
        modified_expenses = get_expenses(modified_data)
        modified_features = pd.DataFrame([[
            modified_data.get('income', 0),
            modified_expenses,
            modified_data.get('savings', 0),
            modified_data.get('emi', 0),
            modified_data.get('age', 30),
            int(modified_data.get('has_loan', False)),
            modified_data.get('loan_amount', 0),
            modified_data.get('interest_rate', 0)
        ]], columns=feature_names)

        modified_score = float(model.predict(modified_features)[0])
        modified_score = max(0, min(100, round(modified_score, 2)))

        # Calculate impact
        score_change = modified_score - current_score

        response = {
            'success': True,
            'current_score': current_score,
            'modified_score': modified_score,
            'score_change': round(score_change, 2),
            'impact': 'positive' if score_change > 0 else 'negative' if score_change < 0 else 'neutral',
            'current_classification': classify_score(current_score),
            'modified_classification': classify_score(modified_score)
        }

        return jsonify(response)

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
        'performance': {
            'r2_score': model_metadata['r2_test'],
            'mae': model_metadata['mae_test'],
            'rmse': model_metadata['rmse_test']
        }
    })

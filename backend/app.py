"""
SmartFin - Flask Backend
Main application file for financial health scoring and guidance
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# ==================== LOAD ML MODEL ====================
print("Loading ML model...")
# Get the absolute path to the ml directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(BASE_DIR, 'ml')

model = joblib.load(os.path.join(ML_DIR, 'financial_health_model.pkl'))
feature_names = joblib.load(os.path.join(ML_DIR, 'feature_names.pkl'))
model_metadata = joblib.load(os.path.join(ML_DIR, 'model_metadata.pkl'))
print(f"Model loaded: {model_metadata['model_type']}")
print(f"Model R2 Score: {model_metadata['test_r2']:.4f}")

# ==================== HELPER FUNCTIONS ====================

def classify_score(score):
    """
    Classify financial health score into 5 categories
    """
    if score >= 80:
        return {
            'category': 'Excellent',
            'color': '#10b981',  # green
            'emoji': '🌟',
            'description': 'Outstanding financial health! Keep up the great work.'
        }
    elif score >= 65:
        return {
            'category': 'Very Good',
            'color': '#3b82f6',  # blue
            'emoji': '✨',
            'description': 'Strong financial position with room for minor improvements.'
        }
    elif score >= 50:
        return {
            'category': 'Good',
            'color': '#f59e0b',  # amber
            'emoji': '👍',
            'description': 'Decent financial health, but consider optimizing your spending.'
        }
    elif score >= 35:
        return {
            'category': 'Average',
            'color': '#f97316',  # orange
            'emoji': '⚠️',
            'description': 'Your finances need attention. Review your expenses carefully.'
        }
    else:
        return {
            'category': 'Poor',
            'color': '#ef4444',  # red
            'emoji': '🚨',
            'description': 'Critical financial situation. Immediate action required!'
        }


def analyze_spending_patterns(data):
    """
    Analyze spending patterns and provide insights
    """
    income = data['income']
    rent = data['rent']
    food = data['food']
    travel = data['travel']
    shopping = data['shopping']
    emi = data['emi']
    savings = data['savings']

    total_expense = rent + food + travel + shopping + emi

    # Calculate ratios
    expense_ratio = total_expense / income if income > 0 else 0
    savings_ratio = savings / income if income > 0 else 0
    emi_ratio = emi / income if income > 0 else 0

    # Calculate percentage breakdown
    breakdown = {
        'rent': (rent / income * 100) if income > 0 else 0,
        'food': (food / income * 100) if income > 0 else 0,
        'travel': (travel / income * 100) if income > 0 else 0,
        'shopping': (shopping / income * 100) if income > 0 else 0,
        'emi': (emi / income * 100) if income > 0 else 0,
        'savings': (savings / income * 100) if income > 0 else 0
    }

    # Identify highest expense
    expense_categories = {
        'Rent': rent,
        'Food': food,
        'Travel': travel,
        'Shopping': shopping,
        'EMI': emi
    }
    highest_expense = max(expense_categories, key=expense_categories.get)

    patterns = {
        'total_expense': total_expense,
        'expense_ratio': round(expense_ratio, 3),
        'savings_ratio': round(savings_ratio, 3),
        'emi_ratio': round(emi_ratio, 3),
        'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
        'highest_expense_category': highest_expense,
        'highest_expense_amount': expense_categories[highest_expense]
    }

    return patterns


def generate_guidance(data, score, patterns):
    """
    Generate personalized financial guidance based on score and patterns
    """
    guidance = {
        'recommendations': [],
        'strengths': [],
        'warnings': []
    }

    income = data['income']
    expense_ratio = patterns['expense_ratio']
    savings_ratio = patterns['savings_ratio']
    emi_ratio = patterns['emi_ratio']

    # Analyze savings
    if savings_ratio >= 0.25:
        guidance['strengths'].append("Excellent savings habit! You're saving 25%+ of your income.")
    elif savings_ratio >= 0.15:
        guidance['strengths'].append("Good savings discipline. Keep it up!")
    elif savings_ratio < 0.05:
        guidance['warnings'].append("Very low savings rate. Try to save at least 10% of income.")
        guidance['recommendations'].append("Set up automatic savings transfers on payday.")

    # Analyze expenses
    if expense_ratio > 0.8:
        guidance['warnings'].append("You're spending over 80% of your income. This is unsustainable.")
        guidance['recommendations'].append("Review all expenses and cut non-essential spending immediately.")
    elif expense_ratio > 0.6:
        guidance['recommendations'].append("Try to reduce total expenses to below 60% of income.")

    # Analyze EMI
    if emi_ratio > 0.4:
        guidance['warnings'].append("EMI is consuming over 40% of income - very high debt burden!")
        guidance['recommendations'].append("Avoid taking new loans. Focus on clearing existing debt.")
    elif emi_ratio > 0.3:
        guidance['recommendations'].append("EMI burden is high. Consider debt consolidation.")
    elif emi_ratio == 0:
        guidance['strengths'].append("No EMI burden - excellent!")

    # Analyze specific categories
    rent_ratio = data['rent'] / income if income > 0 else 0
    if rent_ratio > 0.35:
        guidance['recommendations'].append("Rent is high (>35% of income). Consider finding cheaper accommodation.")

    shopping_ratio = data['shopping'] / income if income > 0 else 0
    if shopping_ratio > 0.15:
        guidance['recommendations'].append("Shopping expenses are high. Try to limit discretionary spending.")

    # Overall recommendations based on score
    if score < 35:
        guidance['recommendations'].insert(0, "URGENT: Create a strict budget and track every expense.")
    elif score < 50:
        guidance['recommendations'].insert(0, "Focus on building an emergency fund of 3-6 months expenses.")
    elif score >= 80:
        guidance['strengths'].append("Excellent financial management! Consider investment opportunities.")

    return guidance


def detect_anomalies(data, patterns):
    """
    Detect financial anomalies and risks
    """
    anomalies = []

    income = data['income']
    savings = data['savings']
    expense_ratio = patterns['expense_ratio']
    savings_ratio = patterns['savings_ratio']
    emi_ratio = patterns['emi_ratio']

    # Critical anomalies
    if expense_ratio > 1.0:
        anomalies.append({
            'severity': 'critical',
            'type': 'deficit',
            'message': 'You are spending MORE than you earn! Immediate action needed.'
        })

    if savings == 0 and income > 20000:
        anomalies.append({
            'severity': 'high',
            'type': 'no_savings',
            'message': 'Zero savings detected. You have no financial cushion for emergencies.'
        })

    if emi_ratio > 0.5:
        anomalies.append({
            'severity': 'critical',
            'type': 'debt_trap',
            'message': 'EMI exceeds 50% of income. Risk of debt trap!'
        })

    # Medium risk anomalies
    if savings_ratio < 0.05 and expense_ratio > 0.7:
        anomalies.append({
            'severity': 'medium',
            'type': 'low_buffer',
            'message': 'Very low savings with high expenses. Financial vulnerability detected.'
        })

    # Warnings
    if data['shopping'] > data['savings'] and data['shopping'] > 5000:
        anomalies.append({
            'severity': 'low',
            'type': 'spending_priority',
            'message': 'Shopping expenses exceed savings. Consider rebalancing priorities.'
        })

    return anomalies


def suggest_investments(score, data, patterns):
    """
    Rule-based investment suggestions based on score and financial profile
    """
    suggestions = []

    savings_ratio = patterns['savings_ratio']
    emi_ratio = patterns['emi_ratio']
    monthly_savings = data['savings']

    # Investment eligibility based on score and ratios
    if score >= 70 and savings_ratio >= 0.15 and emi_ratio < 0.3:
        suggestions.append({
            'type': 'Equity Mutual Funds',
            'risk': 'Medium to High',
            'recommended_amount': f"Rs.{int(monthly_savings * 0.4):,}",
            'reason': 'Good financial health allows for growth-oriented investments.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Public Provident Fund (PPF)',
            'risk': 'Low',
            'recommended_amount': f"Rs.{int(monthly_savings * 0.3):,}",
            'reason': 'Tax-saving with guaranteed returns.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Fixed Deposits',
            'risk': 'Low',
            'recommended_amount': f"Rs.{int(monthly_savings * 0.3):,}",
            'reason': 'Safe option for emergency fund.',
            'suitable': True
        })

    elif score >= 50 and savings_ratio >= 0.1:
        suggestions.append({
            'type': 'Hybrid Mutual Funds',
            'risk': 'Medium',
            'recommended_amount': f"Rs.{int(monthly_savings * 0.5):,}",
            'reason': 'Balanced approach for moderate risk appetite.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Recurring Deposits',
            'risk': 'Very Low',
            'recommended_amount': f"Rs.{int(monthly_savings * 0.5):,}",
            'reason': 'Build disciplined savings habit.',
            'suitable': True
        })

    elif score >= 35:
        suggestions.append({
            'type': 'Emergency Fund (Savings Account)',
            'risk': 'None',
            'recommended_amount': f"Rs.{monthly_savings:,}",
            'reason': 'Build emergency fund first before investing.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Equity Investments',
            'risk': 'High',
            'recommended_amount': 'Not Recommended',
            'reason': 'Focus on stabilizing finances before risky investments.',
            'suitable': False
        })

    else:  # score < 35
        suggestions.append({
            'type': 'Focus on Debt Reduction',
            'risk': 'N/A',
            'recommended_amount': 'All available funds',
            'reason': 'Clear debts and stabilize finances before investing.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Any Investments',
            'risk': 'N/A',
            'recommended_amount': 'Not Recommended',
            'reason': 'Investment not advisable until financial health improves.',
            'suitable': False
        })

    return {
        'eligible_for_investment': score >= 50 and savings_ratio >= 0.1,
        'suggestions': suggestions,
        'overall_advice': get_investment_advice(score)
    }


def get_investment_advice(score):
    """Get overall investment advice based on score"""
    if score >= 80:
        return "Your finances are excellent! Consider aggressive investment strategies for wealth building."
    elif score >= 65:
        return "Good financial position. Diversify investments across equity and debt instruments."
    elif score >= 50:
        return "Decent financial health. Start with low-risk investments and build emergency fund."
    elif score >= 35:
        return "Focus on building emergency fund before investing. Aim for 3 months of expenses."
    else:
        return "Not advisable to invest currently. Focus on reducing debt and increasing savings."


# ==================== API ENDPOINTS ====================

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'SmartFin Financial Health API',
        'version': '1.0',
        'model': model_metadata['model_type'],
        'model_accuracy': f"{model_metadata['test_r2']:.2%}"
    })


@app.route('/api/predict', methods=['POST'])
def predict_score():
    """
    Main prediction endpoint
    Accepts financial data and returns comprehensive analysis
    """
    try:
        data = request.get_json()

        # Validate input
        required_fields = ['income', 'rent', 'food', 'travel', 'shopping', 'emi', 'savings']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            if not isinstance(data[field], (int, float)) or data[field] < 0:
                return jsonify({'error': f'Invalid value for {field}. Must be non-negative number.'}), 400

        # Prepare features for prediction
        features = pd.DataFrame([[
            data['income'],
            data['rent'],
            data['food'],
            data['travel'],
            data['shopping'],
            data['emi'],
            data['savings']
        ]], columns=feature_names)

        # Predict score
        predicted_score = float(model.predict(features)[0])
        predicted_score = max(0, min(100, round(predicted_score, 2)))  # Clamp between 0-100

        # Get classification
        classification = classify_score(predicted_score)

        # Analyze spending patterns
        patterns = analyze_spending_patterns(data)

        # Generate guidance
        guidance = generate_guidance(data, predicted_score, patterns)

        # Detect anomalies
        anomalies = detect_anomalies(data, patterns)

        # Suggest investments
        investments = suggest_investments(predicted_score, data, patterns)

        # Build response
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'score': predicted_score,
            'classification': classification,
            'patterns': patterns,
            'guidance': guidance,
            'anomalies': anomalies,
            'investments': investments,
            'model_info': {
                'model_type': model_metadata['model_type'],
                'accuracy': f"{model_metadata['test_r2']:.2%}",
                'average_error': f"±{model_metadata['mae']:.1f} points"
            }
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/whatif', methods=['POST'])
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

        # Predict current score
        current_features = pd.DataFrame([[
            current_data['income'],
            current_data['rent'],
            current_data['food'],
            current_data['travel'],
            current_data['shopping'],
            current_data['emi'],
            current_data['savings']
        ]], columns=feature_names)

        current_score = float(model.predict(current_features)[0])
        current_score = max(0, min(100, round(current_score, 2)))

        # Predict modified score
        modified_features = pd.DataFrame([[
            modified_data['income'],
            modified_data['rent'],
            modified_data['food'],
            modified_data['travel'],
            modified_data['shopping'],
            modified_data['emi'],
            modified_data['savings']
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


@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get information about the ML model"""
    return jsonify({
        'model_type': model_metadata['model_type'],
        'features': feature_names,
        'performance': {
            'r2_score': model_metadata['test_r2'],
            'mae': model_metadata['mae'],
            'rmse': model_metadata['rmse']
        },
        'training_samples': model_metadata['n_samples']
    })


# ==================== RUN SERVER ====================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("SmartFin Backend Server Starting...")
    print("="*60)
    print(f"Model: {model_metadata['model_type']}")
    print(f"Accuracy: {model_metadata['test_r2']:.2%}")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=5000)

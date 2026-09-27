"""
Legacy 8-factor financial health scorer.
Rule-based labels + a GradientBoosting model trained to replicate them
(see AGENTS.md section 5 for the full honest description). Kept live
alongside the newer ML modules for backward compatibility.
"""

import logging
from datetime import datetime

import pandas as pd

from guidance_engine import PersonalizedGuidanceEngine
from legacy_scorer.model import model, feature_names, model_data, model_metadata

logger = logging.getLogger(__name__)


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
    try:
        guidance, meta = PersonalizedGuidanceEngine.generate_guidance_ai(
            data, score, patterns, return_meta=True
        )
        logger.info(
            "guidance_engine source=%s engine=%s score=%.2f",
            meta.get('source'),
            meta.get('engine'),
            float(score or 0),
        )
        return guidance
    except Exception:
        # Keep legacy fallback behavior for resilience.
        pass

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
    try:
        investments, meta = PersonalizedGuidanceEngine.suggest_investments_ai(
            score, data, patterns, return_meta=True
        )
        logger.info(
            "investment_engine source=%s engine=%s score=%.2f",
            meta.get('source'),
            meta.get('engine'),
            float(score or 0),
        )
        return investments
    except Exception:
        # Keep legacy fallback behavior for resilience.
        pass

    suggestions = []

    savings_ratio = patterns['savings_ratio']
    emi_ratio = patterns['emi_ratio']
    monthly_savings = data['savings']

    # Investment eligibility based on score and ratios
    if score >= 70 and savings_ratio >= 0.15 and emi_ratio < 0.3:
        suggestions.append({
            'type': 'Equity Mutual Funds',
            'risk_level': 'Medium to High',
            'allocation': int(monthly_savings * 0.4),
            'description': 'Good financial health allows for growth-oriented investments.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Public Provident Fund (PPF)',
            'risk_level': 'Low',
            'allocation': int(monthly_savings * 0.3),
            'description': 'Tax-saving with guaranteed returns.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Fixed Deposits',
            'risk_level': 'Low',
            'allocation': int(monthly_savings * 0.3),
            'description': 'Safe option for emergency fund.',
            'suitable': True
        })

    elif score >= 50 and savings_ratio >= 0.1:
        suggestions.append({
            'type': 'Hybrid Mutual Funds',
            'risk_level': 'Medium',
            'allocation': int(monthly_savings * 0.5),
            'description': 'Balanced approach for moderate risk appetite.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Recurring Deposits',
            'risk_level': 'Very Low',
            'allocation': int(monthly_savings * 0.5),
            'description': 'Build disciplined savings habit.',
            'suitable': True
        })

    elif score >= 35:
        suggestions.append({
            'type': 'Emergency Fund (Savings Account)',
            'risk_level': 'None',
            'allocation': monthly_savings,
            'description': 'Build emergency fund first before investing.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Equity Investments',
            'risk_level': 'High',
            'allocation': 0,
            'description': 'Focus on stabilizing finances before risky investments. Not recommended at this time.',
            'suitable': False
        })

    else:  # score < 35
        suggestions.append({
            'type': 'Focus on Debt Reduction',
            'risk_level': 'N/A',
            'allocation': monthly_savings,
            'description': 'Clear debts and stabilize finances before investing.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Any Investments',
            'risk_level': 'N/A',
            'allocation': 0,
            'description': 'Investment not advisable until financial health improves.',
            'suitable': False
        })

    return {
        'eligible': score >= 50 and savings_ratio >= 0.1,
        'suggestions': suggestions,
        'message': get_investment_advice(score),
        'advice': get_investment_advice(score)
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


def run_prediction_analysis(data):
    # Calculate expenses from individual categories if provided
    expenses = data.get('expenses', 0)
    if expenses == 0 and any(k in data for k in ['rent', 'food', 'travel', 'shopping']):
        expenses = (data.get('rent', 0) + data.get('food', 0) +
                   data.get('travel', 0) + data.get('shopping', 0))

    # Get optional fields with defaults
    age = data.get('age', 30)
    has_loan = data.get('has_loan', False)
    loan_amount = data.get('loan_amount', 0)
    interest_rate = data.get('interest_rate', 0)

    # Prepare features for enhanced model prediction
    features = pd.DataFrame([[
        data['income'],           # income
        expenses,                 # expenses
        data['savings'],          # savings
        data['emi'],              # emi
        age,                      # age
        int(has_loan),            # has_loan_numeric
        loan_amount,              # loan_amount_filled
        interest_rate             # interest_rate_filled
    ]], columns=feature_names)

    # Predict score
    predicted_score = float(model.predict(features)[0])
    predicted_score = max(0, min(100, round(predicted_score, 2)))

    # Get classification and enrichments
    classification = classify_score(predicted_score)
    patterns = analyze_spending_patterns(data)
    guidance = generate_guidance(data, predicted_score, patterns)
    anomalies = detect_anomalies(data, patterns)
    investments = suggest_investments(predicted_score, data, patterns)

    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'score': predicted_score,
        'classification': classification,
        'patterns': patterns,
        'guidance': guidance,
        'anomalies': anomalies,
        'investments': investments,
        'model_info': {
            'model_type': model_data['model_type'],
            'accuracy': f"{model_metadata['r2_test']:.2%}",
            'average_error': f"±{model_metadata['mae_test']:.1f} points"
        }
    }

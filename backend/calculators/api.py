"""
Investment Calculators Blueprint
SIP and Lumpsum future-value calculators. Pure math, no DB/auth dependency.
"""

from flask import Blueprint, request, jsonify

calculators_bp = Blueprint('calculators', __name__)


@calculators_bp.route('/api/sip-calculator', methods=['POST'])
def calculate_sip():
    """
    Calculate SIP (Systematic Investment Plan) returns

    Formula: FV = P × ((1 + r)^n - 1) / r) × (1 + r)
    Where:
    - P = Monthly investment amount
    - r = Monthly rate of return (annual rate / 12)
    - n = Total number of months
    """
    try:
        data = request.get_json()

        # Validate input
        monthly_investment = float(data.get('monthly_investment', 0))
        annual_return_rate = float(data.get('annual_return_rate', 0))
        time_period_years = float(data.get('time_period_years', 0))

        if monthly_investment <= 0:
            return jsonify({'error': 'Monthly investment must be greater than 0'}), 400

        if annual_return_rate < 0 or annual_return_rate > 100:
            return jsonify({'error': 'Annual return rate must be between 0 and 100'}), 400

        if time_period_years <= 0 or time_period_years > 50:
            return jsonify({'error': 'Time period must be between 0 and 50 years'}), 400

        # Calculate SIP
        monthly_rate = (annual_return_rate / 12) / 100
        total_months = int(time_period_years * 12)

        # Total invested amount
        total_invested = monthly_investment * total_months

        # Future value calculation
        if monthly_rate == 0:
            # If return rate is 0, future value = total invested
            future_value = total_invested
        else:
            # Standard SIP formula
            future_value = monthly_investment * (((1 + monthly_rate) ** total_months - 1) / monthly_rate) * (1 + monthly_rate)

        # Calculate returns
        estimated_returns = future_value - total_invested

        # Calculate year-wise breakdown
        yearly_breakdown = []
        for year in range(1, int(time_period_years) + 1):
            months = year * 12
            invested_till_year = monthly_investment * months

            if monthly_rate == 0:
                value_till_year = invested_till_year
            else:
                value_till_year = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)

            returns_till_year = value_till_year - invested_till_year

            yearly_breakdown.append({
                'year': year,
                'invested': round(invested_till_year, 2),
                'value': round(value_till_year, 2),
                'returns': round(returns_till_year, 2)
            })

        response = {
            'success': True,
            'monthly_investment': round(monthly_investment, 2),
            'annual_return_rate': round(annual_return_rate, 2),
            'time_period_years': round(time_period_years, 2),
            'total_invested': round(total_invested, 2),
            'estimated_returns': round(estimated_returns, 2),
            'future_value': round(future_value, 2),
            'total_months': total_months,
            'yearly_breakdown': yearly_breakdown
        }

        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500


@calculators_bp.route('/api/lumpsum-calculator', methods=['POST'])
def calculate_lumpsum():
    """
    Calculate Lumpsum investment returns

    Formula: FV = P × (1 + r)^n
    Where:
    - P = Principal amount (lumpsum investment)
    - r = Annual rate of return
    - n = Time period in years
    """
    try:
        data = request.get_json()

        # Validate input
        principal_amount = float(data.get('principal_amount', 0))
        annual_return_rate = float(data.get('annual_return_rate', 0))
        time_period_years = float(data.get('time_period_years', 0))

        if principal_amount <= 0:
            return jsonify({'error': 'Principal amount must be greater than 0'}), 400

        if annual_return_rate < 0 or annual_return_rate > 100:
            return jsonify({'error': 'Annual return rate must be between 0 and 100'}), 400

        if time_period_years <= 0 or time_period_years > 50:
            return jsonify({'error': 'Time period must be between 0 and 50 years'}), 400

        # Calculate Lumpsum
        annual_rate = annual_return_rate / 100

        # Future value calculation
        if annual_rate == 0:
            future_value = principal_amount
        else:
            future_value = principal_amount * ((1 + annual_rate) ** time_period_years)

        # Calculate returns
        estimated_returns = future_value - principal_amount

        # Calculate year-wise breakdown
        yearly_breakdown = []
        for year in range(1, int(time_period_years) + 1):
            if annual_rate == 0:
                value_till_year = principal_amount
            else:
                value_till_year = principal_amount * ((1 + annual_rate) ** year)

            returns_till_year = value_till_year - principal_amount

            yearly_breakdown.append({
                'year': year,
                'invested': round(principal_amount, 2),
                'value': round(value_till_year, 2),
                'returns': round(returns_till_year, 2)
            })

        response = {
            'success': True,
            'principal_amount': round(principal_amount, 2),
            'annual_return_rate': round(annual_return_rate, 2),
            'time_period_years': round(time_period_years, 2),
            'total_invested': round(principal_amount, 2),
            'estimated_returns': round(estimated_returns, 2),
            'future_value': round(future_value, 2),
            'yearly_breakdown': yearly_breakdown
        }

        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500

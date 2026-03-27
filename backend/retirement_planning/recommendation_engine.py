"""
Recommendation Engine

Generates personalized action plans based on retirement readiness assessment:
- Prioritized recommendations (3-5 items)
- Impact estimation on readiness score
- Loan payoff strategies (Snowball, Avalanche, Balanced)
- Expense reduction recommendations
- Investment strategy recommendations
"""

import uuid
from typing import Dict, List, Optional, Tuple
from .models import ActionPlanItem
from .constants import (
    MIN_RECOMMENDATIONS,
    MAX_RECOMMENDATIONS,
    SAVINGS_ACHIEVABILITY_THRESHOLD
)


class RecommendationEngine:
    """
    Generates personalized action plans for retirement readiness improvement
    
    Analyzes financial situation and provides prioritized, actionable recommendations
    with estimated impact on retirement readiness score.
    """
    
    @staticmethod
    def generate_action_plan(
        readiness_score: float,
        financial_health_factor: float,
        savings_adequacy_factor: float,
        savings_rate_factor: float,
        debt_burden_factor: float,
        time_horizon_factor: float,
        current_age: int,
        retirement_age: int,
        required_monthly_savings: float,
        current_monthly_income: float,
        total_loan_amount: float,
        annual_salary: float,
        gap: float,
        corpus_target: float
    ) -> List[Dict]:
        """
        Generate prioritized action plan with 3-5 recommendations
        
        Args:
            readiness_score: Current retirement readiness score
            financial_health_factor: Financial health factor (0-100)
            savings_adequacy_factor: Savings adequacy factor (0-100)
            savings_rate_factor: Savings rate factor (0-100)
            debt_burden_factor: Debt burden factor (0-100)
            time_horizon_factor: Time horizon factor (0-100)
            current_age: Current age
            retirement_age: Target retirement age
            required_monthly_savings: Monthly savings needed
            current_monthly_income: Monthly income
            total_loan_amount: Total loan amount
            annual_salary: Annual salary
            gap: Savings gap
            corpus_target: Target corpus
        
        Returns:
            List of action plan items (3-5 recommendations)
        """
        recommendations = []
        
        # Analyze situation and generate recommendations
        years_to_retirement = retirement_age - current_age
        
        # Recommendation 1: Address debt if high burden
        if debt_burden_factor < 60 and total_loan_amount > 0:
            recommendations.append({
                'action_id': str(uuid.uuid4()),
                'priority': 1,
                'action_type': 'reduce_debt',
                'description': 'Prioritize paying off high-interest loans',
                'estimated_impact_on_score': 15.0,
                'timeline': 'short_term',
                'details': {
                    'current_debt': total_loan_amount,
                    'debt_to_income_ratio': (total_loan_amount / annual_salary) if annual_salary > 0 else 0,
                    'benefit': 'Reduce debt burden and improve financial health'
                }
            })
        
        # Recommendation 2: Increase savings if gap exists
        if gap > 0 and savings_rate_factor < 100:
            savings_increase_needed = (gap / (retirement_age - current_age)) / 12 if years_to_retirement > 0 else 0
            recommendations.append({
                'action_id': str(uuid.uuid4()),
                'priority': 2 if debt_burden_factor >= 60 else 1,
                'action_type': 'increase_savings',
                'description': f'Increase monthly savings by ₹{savings_increase_needed:,.0f}',
                'estimated_impact_on_score': 20.0,
                'timeline': 'immediate',
                'details': {
                    'current_monthly_savings': required_monthly_savings,
                    'additional_savings_needed': savings_increase_needed,
                    'new_total_monthly_savings': required_monthly_savings + savings_increase_needed,
                    'savings_rate_percentage': ((required_monthly_savings + savings_increase_needed) / current_monthly_income * 100) if current_monthly_income > 0 else 0
                }
            })
        
        # Recommendation 3: Improve investment returns
        if gap > 0 and years_to_retirement > 5:
            recommendations.append({
                'action_id': str(uuid.uuid4()),
                'priority': 3,
                'action_type': 'improve_returns',
                'description': 'Optimize investment allocation for better returns',
                'estimated_impact_on_score': 12.0,
                'timeline': 'long_term',
                'details': {
                    'current_gap': gap,
                    'benefit': 'Higher returns can close the gap without increasing savings',
                    'risk_level': 'moderate' if years_to_retirement > 10 else 'low'
                }
            })
        
        # Recommendation 4: Improve financial health
        if financial_health_factor < 70:
            recommendations.append({
                'action_id': str(uuid.uuid4()),
                'priority': 2,
                'action_type': 'improve_financial_health',
                'description': 'Improve financial health through better money management',
                'estimated_impact_on_score': 10.0,
                'timeline': 'short_term',
                'details': {
                    'current_score': financial_health_factor,
                    'target_score': 80,
                    'focus_areas': ['Increase savings rate', 'Reduce expenses', 'Improve payment history']
                }
            })
        
        # Recommendation 5: Consider retirement age adjustment
        if gap > 0 and years_to_retirement < 10:
            recommendations.append({
                'action_id': str(uuid.uuid4()),
                'priority': 4,
                'action_type': 'delay_retirement',
                'description': 'Consider delaying retirement by 2-3 years',
                'estimated_impact_on_score': 18.0,
                'timeline': 'long_term',
                'details': {
                    'current_retirement_age': retirement_age,
                    'suggested_retirement_age': retirement_age + 2,
                    'benefit': 'More time to save and compound investments'
                }
            })
        
        # Sort by priority and limit to MAX_RECOMMENDATIONS
        recommendations.sort(key=lambda x: x['priority'])
        recommendations = recommendations[:MAX_RECOMMENDATIONS]
        
        # Ensure at least MIN_RECOMMENDATIONS
        if len(recommendations) < MIN_RECOMMENDATIONS:
            # Add generic recommendations if needed
            if len(recommendations) < MIN_RECOMMENDATIONS:
                recommendations.append({
                    'action_id': str(uuid.uuid4()),
                    'priority': len(recommendations) + 1,
                    'action_type': 'review_plan',
                    'description': 'Review and adjust retirement plan annually',
                    'estimated_impact_on_score': 5.0,
                    'timeline': 'ongoing',
                    'details': {
                        'benefit': 'Stay on track with changing circumstances'
                    }
                })
        
        return recommendations[:MAX_RECOMMENDATIONS]
    
    @staticmethod
    def estimate_recommendation_impact(
        recommendation: Dict,
        current_readiness_score: float
    ) -> float:
        """
        Estimate impact of recommendation on readiness score
        
        Args:
            recommendation: Recommendation item
            current_readiness_score: Current readiness score
        
        Returns:
            Estimated new readiness score after implementing recommendation
        """
        estimated_impact = recommendation.get('estimated_impact_on_score', 0)
        new_score = current_readiness_score + estimated_impact
        
        # Cap at 100
        new_score = min(100, new_score)
        
        return round(new_score, 2)
    
    @staticmethod
    def generate_loan_payoff_strategy(
        loans: List[Dict],
        strategy_type: str = 'balanced'
    ) -> Dict:
        """
        Generate loan payoff strategy
        
        Args:
            loans: List of loan dictionaries with amount, rate, emi
            strategy_type: 'snowball', 'avalanche', or 'balanced'
        
        Returns:
            Payoff strategy with timeline and impact
        """
        if not loans:
            return {'strategy': 'no_loans', 'message': 'No loans to pay off'}
        
        if strategy_type == 'snowball':
            # Sort by amount (smallest first)
            sorted_loans = sorted(loans, key=lambda x: x.get('amount', 0))
        elif strategy_type == 'avalanche':
            # Sort by interest rate (highest first)
            sorted_loans = sorted(loans, key=lambda x: x.get('interest_rate', 0), reverse=True)
        else:  # balanced
            # Mix of both - prioritize high-interest small loans
            sorted_loans = sorted(
                loans,
                key=lambda x: (x.get('interest_rate', 0) * 0.6 + (1 - x.get('amount', 0) / sum(l.get('amount', 0) for l in loans)) * 0.4),
                reverse=True
            )
        
        total_amount = sum(loan.get('amount', 0) for loan in loans)
        total_interest = sum(loan.get('interest_amount', 0) for loan in loans)
        
        return {
            'strategy_type': strategy_type,
            'loan_order': sorted_loans,
            'total_amount': total_amount,
            'total_interest': total_interest,
            'estimated_payoff_months': len(loans) * 12,  # Simplified
            'monthly_payment': total_amount / (len(loans) * 12) if len(loans) > 0 else 0
        }
    
    @staticmethod
    def generate_expense_reduction_recommendations(
        current_monthly_expenses: float,
        target_reduction_percentage: float = 0.10
    ) -> List[Dict]:
        """
        Generate expense reduction recommendations
        
        Args:
            current_monthly_expenses: Current monthly expenses
            target_reduction_percentage: Target reduction (default 10%)
        
        Returns:
            List of expense reduction suggestions
        """
        target_reduction = current_monthly_expenses * target_reduction_percentage
        
        recommendations = [
            {
                'category': 'Subscriptions',
                'current_spend': current_monthly_expenses * 0.05,
                'reduction_potential': current_monthly_expenses * 0.02,
                'action': 'Cancel unused subscriptions and memberships'
            },
            {
                'category': 'Dining Out',
                'current_spend': current_monthly_expenses * 0.15,
                'reduction_potential': current_monthly_expenses * 0.05,
                'action': 'Reduce dining out frequency'
            },
            {
                'category': 'Utilities',
                'current_spend': current_monthly_expenses * 0.10,
                'reduction_potential': current_monthly_expenses * 0.02,
                'action': 'Optimize energy usage'
            },
            {
                'category': 'Shopping',
                'current_spend': current_monthly_expenses * 0.20,
                'reduction_potential': current_monthly_expenses * 0.05,
                'action': 'Reduce discretionary spending'
            }
        ]
        
        return recommendations
    
    @staticmethod
    def generate_investment_strategy_recommendation(
        time_horizon: int,
        risk_tolerance: int = 5
    ) -> Dict:
        """
        Generate investment strategy recommendation
        
        Args:
            time_horizon: Years until retirement
            risk_tolerance: Risk tolerance (1-10 scale)
        
        Returns:
            Investment strategy recommendation
        """
        if time_horizon > 15:
            allocation = {
                'equity': 80,
                'debt': 15,
                'gold': 5,
                'description': 'Aggressive growth strategy'
            }
        elif time_horizon > 10:
            allocation = {
                'equity': 65,
                'debt': 30,
                'gold': 5,
                'description': 'Balanced growth strategy'
            }
        elif time_horizon > 5:
            allocation = {
                'equity': 50,
                'debt': 45,
                'gold': 5,
                'description': 'Conservative growth strategy'
            }
        else:
            allocation = {
                'equity': 30,
                'debt': 65,
                'gold': 5,
                'description': 'Capital preservation strategy'
            }
        
        return {
            'time_horizon': time_horizon,
            'risk_tolerance': risk_tolerance,
            'recommended_allocation': allocation,
            'expected_annual_return': 0.08 + (time_horizon / 100),
            'rebalancing_frequency': 'Quarterly'
        }

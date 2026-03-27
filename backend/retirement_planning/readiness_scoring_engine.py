"""
Retirement Readiness Scoring Engine

Calculates retirement readiness score (0-100) based on 5 weighted factors:
- Financial Health Score (30%) - ML model score
- Savings Adequacy (25%) - Current savings vs target
- Savings Rate (20%) - Can achieve required savings
- Debt Burden (15%) - Loan obligations
- Time Horizon (10%) - Years until retirement
"""

from typing import Dict, Tuple, Optional
from .models import RetirementReadinessAssessment
from .constants import (
    READINESS_SCORE_WEIGHTS,
    READINESS_CLASSIFICATIONS,
    TIME_HORIZON_FACTORS,
    SAVINGS_RATE_ACHIEVABLE,
    SAVINGS_RATE_MARGINAL,
    SAVINGS_RATE_NOT_ACHIEVABLE,
    SAVINGS_ACHIEVABILITY_THRESHOLD,
    SAVINGS_ACHIEVABILITY_MARGINAL_THRESHOLD,
    DEBT_BURDEN_CRITICAL_RATIO
)


class RetirementReadinessScoringEngine:
    """
    Calculates comprehensive retirement readiness score based on 5 factors
    
    The scoring system uses weighted factors to provide a holistic view of
    retirement preparedness, integrating financial health, savings capacity,
    debt burden, and time horizon.
    """
    
    FACTOR_WEIGHTS = READINESS_SCORE_WEIGHTS
    
    @staticmethod
    def calculate_financial_health_factor(
        financial_health_score: float
    ) -> float:
        """
        Use user's 8-factor financial health score from ML model
        
        Args:
            financial_health_score: Score from ML model (0-100)
        
        Returns:
            Financial health factor (0-100)
        """
        # Clamp score between 0 and 100
        factor = max(0, min(100, financial_health_score))
        return round(factor, 2)
    
    @staticmethod
    def calculate_savings_adequacy_factor(
        current_savings: float,
        corpus_target: float
    ) -> float:
        """
        Calculate savings adequacy: (current_savings / corpus_target) × 100
        
        Capped at 100 (100% adequacy is maximum)
        
        Args:
            current_savings: Accumulated retirement savings
            corpus_target: Target retirement corpus
        
        Returns:
            Savings adequacy factor (0-100)
        """
        if corpus_target <= 0:
            return 0.0
        
        adequacy = (current_savings / corpus_target) * 100
        # Cap at 100
        factor = min(100, adequacy)
        return round(factor, 2)
    
    @staticmethod
    def calculate_savings_rate_factor(
        required_monthly_savings: float,
        current_monthly_income: float
    ) -> float:
        """
        Determine if required savings is achievable
        
        Returns:
        - 100 if achievable (< 50% of income)
        - 50 if marginal (50-70% of income)
        - 20 if not achievable (> 70% of income)
        
        Args:
            required_monthly_savings: Monthly savings needed
            current_monthly_income: Monthly income
        
        Returns:
            Savings rate factor (0-100)
        """
        if current_monthly_income <= 0:
            return 0.0
        
        savings_rate = required_monthly_savings / current_monthly_income
        
        if savings_rate <= SAVINGS_ACHIEVABILITY_THRESHOLD:
            # Easily achievable (<=35% of income)
            return float(SAVINGS_RATE_ACHIEVABLE)
        elif savings_rate <= SAVINGS_ACHIEVABILITY_MARGINAL_THRESHOLD:
            # Marginal (35-50% of income)
            return float(SAVINGS_RATE_MARGINAL)
        else:
            # Not achievable (>50% of income)
            return float(SAVINGS_RATE_NOT_ACHIEVABLE)
    
    @staticmethod
    def calculate_debt_burden_factor(
        total_loan_amount: float,
        annual_salary: float
    ) -> float:
        """
        Calculate debt burden factor
        
        Formula: 100 - (total_loan_amount / annual_salary × 100)
        Minimum 0
        
        Args:
            total_loan_amount: Total outstanding loan amount
            annual_salary: Annual income
        
        Returns:
            Debt burden factor (0-100)
        """
        if annual_salary <= 0:
            return 0.0
        
        debt_ratio = total_loan_amount / annual_salary
        
        # Calculate factor: 100 - (debt_ratio × 100)
        factor = 100 - (debt_ratio * 100)
        
        # Clamp between 0 and 100
        factor = max(0, min(100, factor))
        return round(factor, 2)
    
    @staticmethod
    def calculate_time_horizon_factor(
        current_age: int,
        retirement_age: int
    ) -> float:
        """
        Calculate time horizon factor based on years until retirement
        
        - >15 years: 100 points
        - 10-15 years: 80 points
        - 5-10 years: 60 points
        - <5 years: 40 points
        
        Args:
            current_age: User's current age
            retirement_age: Target retirement age
        
        Returns:
            Time horizon factor (0-100)
        """
        years_to_retirement = retirement_age - current_age
        
        if years_to_retirement > 15:
            return 100.0
        elif years_to_retirement >= 10:
            return 80.0
        elif years_to_retirement >= 5:
            return 60.0
        else:
            return 40.0
    
    @staticmethod
    def calculate_readiness_score(
        financial_health_factor: float,
        savings_adequacy_factor: float,
        savings_rate_factor: float,
        debt_burden_factor: float,
        time_horizon_factor: float
    ) -> float:
        """
        Calculate overall retirement readiness score (0-100)
        
        Uses weighted aggregation of 5 factors:
        - Financial Health: 30%
        - Savings Adequacy: 25%
        - Savings Rate: 20%
        - Debt Burden: 15%
        - Time Horizon: 10%
        
        Args:
            financial_health_factor: Financial health score (0-100)
            savings_adequacy_factor: Savings adequacy (0-100)
            savings_rate_factor: Savings rate achievability (0-100)
            debt_burden_factor: Debt burden (0-100)
            time_horizon_factor: Time horizon (0-100)
        
        Returns:
            Overall readiness score (0-100)
        """
        readiness_score = (
            financial_health_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['financial_health'] +
            savings_adequacy_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['savings_adequacy'] +
            savings_rate_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['savings_rate'] +
            debt_burden_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['debt_burden'] +
            time_horizon_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['time_horizon']
        )
        
        # Clamp between 0 and 100
        readiness_score = max(0, min(100, readiness_score))
        return round(readiness_score, 2)
    
    @staticmethod
    def classify_score(score: float) -> str:
        """
        Classify score into categories
        
        - Excellent: 80-100
        - Good: 60-79
        - Fair: 40-59
        - Poor: 20-39
        - Critical: 0-19
        
        Args:
            score: Readiness score (0-100)
        
        Returns:
            Classification string
        """
        for classification, (min_score, max_score) in READINESS_CLASSIFICATIONS.items():
            if min_score <= score <= max_score:
                return classification
        
        # Default to critical if out of range
        return 'critical'
    
    @staticmethod
    def get_classification_color(classification: str) -> str:
        """
        Get color code for classification
        
        Args:
            classification: Classification string
        
        Returns:
            Color code (hex or name)
        """
        colors = {
            'excellent': '#10b981',      # Green
            'good': '#3b82f6',           # Blue
            'fair': '#f59e0b',           # Amber
            'poor': '#ef5350',           # Red
            'critical': '#c62828'        # Dark Red
        }
        return colors.get(classification, '#6b7280')  # Gray default
    
    @staticmethod
    def calculate_full_assessment(
        current_age: int,
        retirement_age: int,
        current_savings: float,
        corpus_target: float,
        required_monthly_savings: float,
        current_monthly_income: float,
        total_loan_amount: float,
        annual_salary: float,
        financial_health_score: float
    ) -> RetirementReadinessAssessment:
        """
        Calculate complete retirement readiness assessment
        
        Args:
            current_age: User's current age
            retirement_age: Target retirement age
            current_savings: Accumulated retirement savings
            corpus_target: Target retirement corpus
            required_monthly_savings: Monthly savings needed
            current_monthly_income: Monthly income
            total_loan_amount: Total outstanding loans
            annual_salary: Annual income
            financial_health_score: ML model financial health score
        
        Returns:
            RetirementReadinessAssessment object
        """
        # Calculate individual factors
        financial_health_factor = RetirementReadinessScoringEngine.calculate_financial_health_factor(
            financial_health_score
        )
        savings_adequacy_factor = RetirementReadinessScoringEngine.calculate_savings_adequacy_factor(
            current_savings, corpus_target
        )
        savings_rate_factor = RetirementReadinessScoringEngine.calculate_savings_rate_factor(
            required_monthly_savings, current_monthly_income
        )
        debt_burden_factor = RetirementReadinessScoringEngine.calculate_debt_burden_factor(
            total_loan_amount, annual_salary
        )
        time_horizon_factor = RetirementReadinessScoringEngine.calculate_time_horizon_factor(
            current_age, retirement_age
        )
        
        # Calculate overall score
        readiness_score = RetirementReadinessScoringEngine.calculate_readiness_score(
            financial_health_factor,
            savings_adequacy_factor,
            savings_rate_factor,
            debt_burden_factor,
            time_horizon_factor
        )
        
        # Classify score
        classification = RetirementReadinessScoringEngine.classify_score(readiness_score)
        
        # Create factors breakdown
        factors_breakdown = {
            'financial_health': {
                'value': financial_health_factor,
                'weight': RetirementReadinessScoringEngine.FACTOR_WEIGHTS['financial_health'],
                'contribution': financial_health_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['financial_health']
            },
            'savings_adequacy': {
                'value': savings_adequacy_factor,
                'weight': RetirementReadinessScoringEngine.FACTOR_WEIGHTS['savings_adequacy'],
                'contribution': savings_adequacy_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['savings_adequacy']
            },
            'savings_rate': {
                'value': savings_rate_factor,
                'weight': RetirementReadinessScoringEngine.FACTOR_WEIGHTS['savings_rate'],
                'contribution': savings_rate_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['savings_rate']
            },
            'debt_burden': {
                'value': debt_burden_factor,
                'weight': RetirementReadinessScoringEngine.FACTOR_WEIGHTS['debt_burden'],
                'contribution': debt_burden_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['debt_burden']
            },
            'time_horizon': {
                'value': time_horizon_factor,
                'weight': RetirementReadinessScoringEngine.FACTOR_WEIGHTS['time_horizon'],
                'contribution': time_horizon_factor * RetirementReadinessScoringEngine.FACTOR_WEIGHTS['time_horizon']
            }
        }
        
        return RetirementReadinessAssessment(
            readiness_score=readiness_score,
            classification=classification,
            financial_health_factor=financial_health_factor,
            savings_adequacy_factor=savings_adequacy_factor,
            savings_rate_factor=savings_rate_factor,
            debt_burden_factor=debt_burden_factor,
            time_horizon_factor=time_horizon_factor,
            factors_breakdown=factors_breakdown
        )
    
    @staticmethod
    def get_factor_insights(factor_name: str, factor_value: float) -> str:
        """
        Get human-readable insights for a factor
        
        Args:
            factor_name: Name of the factor
            factor_value: Factor value (0-100)
        
        Returns:
            Insight string
        """
        insights = {
            'financial_health': {
                80: 'Excellent financial health - strong foundation for retirement',
                60: 'Good financial health - on track for retirement',
                40: 'Fair financial health - some improvements needed',
                20: 'Poor financial health - significant improvements needed',
                0: 'Critical financial health - urgent action required'
            },
            'savings_adequacy': {
                80: 'Excellent savings progress - well ahead of target',
                60: 'Good savings progress - on track',
                40: 'Fair savings progress - need to increase savings',
                20: 'Low savings - significant gap to target',
                0: 'No savings - starting from zero'
            },
            'savings_rate': {
                100: 'Savings target is easily achievable',
                50: 'Savings target is challenging but possible',
                20: 'Savings target is not achievable with current income'
            },
            'debt_burden': {
                100: 'No debt - excellent position',
                80: 'Low debt - manageable',
                60: 'Moderate debt - needs attention',
                40: 'High debt - significant burden',
                0: 'Critical debt - urgent action needed'
            },
            'time_horizon': {
                100: 'Long time horizon - can take calculated risks',
                80: 'Good time horizon - balanced approach',
                60: 'Moderate time horizon - conservative approach',
                40: 'Short time horizon - very conservative approach'
            }
        }
        
        factor_insights = insights.get(factor_name, {})
        
        # Find closest insight level
        for threshold in sorted(factor_insights.keys(), reverse=True):
            if factor_value >= threshold:
                return factor_insights[threshold]
        
        return 'Unable to determine insight'

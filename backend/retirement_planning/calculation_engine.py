"""
Retirement Calculation Engine

Core calculations for retirement planning including:
- Retirement corpus calculation with inflation adjustment
- Required monthly savings calculation
- Projected savings calculation
- Gap analysis
- Input validation
"""

import math
from typing import Dict, Tuple, Optional
from .models import RetirementPlan, GapAnalysis
from .exceptions import InvalidInputError, UnrealisticValueError
from .validators import validate_retirement_plan_inputs
from .constants import (
    DEFAULT_INFLATION_RATE,
    DEFAULT_INVESTMENT_RETURN_RATE,
    DEFAULT_LIFE_EXPECTANCY,
    CORPUS_MULTIPLIER_MIN,
    CORPUS_MULTIPLIER_MAX
)


class RetirementCalculationEngine:
    """
    Core calculation engine for retirement planning
    
    Handles all mathematical calculations for retirement corpus, savings requirements,
    and gap analysis using standard financial formulas.
    """
    
    @staticmethod
    def calculate_retirement_corpus(
        current_age: int,
        retirement_age: int,
        current_monthly_expenses: float,
        inflation_rate: float = DEFAULT_INFLATION_RATE,
        life_expectancy: int = DEFAULT_LIFE_EXPECTANCY
    ) -> Tuple[float, float]:
        """
        Calculate total retirement corpus needed
        
        Formula:
        1. retirement_monthly_expenses = current_monthly_expenses × (1 + inflation_rate)^(retirement_age - current_age)
        2. corpus = retirement_monthly_expenses × 12 × (life_expectancy - retirement_age)
        
        Args:
            current_age: User's current age
            retirement_age: Target retirement age
            current_monthly_expenses: Current monthly lifestyle expenses
            inflation_rate: Annual inflation rate (default 6%)
            life_expectancy: Assumed lifespan (default 85)
        
        Returns:
            Tuple of (retirement_corpus, monthly_expenses_at_retirement)
        
        Raises:
            InvalidInputError: If inputs are invalid
            UnrealisticValueError: If result is unrealistic
        """
        # Validation is handled at the API level, no need to re-validate here
        
        # Calculate years until retirement
        years_to_retirement = retirement_age - current_age
        
        # Calculate monthly expenses at retirement with inflation
        monthly_expenses_at_retirement = current_monthly_expenses * (
            (1 + inflation_rate) ** years_to_retirement
        )
        
        # Calculate years in retirement
        years_in_retirement = life_expectancy - retirement_age
        
        # Calculate total corpus needed using present-value annuity
        # This accounts for inflation continuing during retirement
        # while the corpus earns investment returns.
        # We use a real return rate: (1+nominal)/(1+inflation) - 1
        # If real_rate > 0, corpus = annual_expenses * [(1 - (1+real_rate)^(-years)) / real_rate]
        # If real_rate ≈ 0, corpus = annual_expenses * years
        annual_expenses_at_retirement = monthly_expenses_at_retirement * 12
        
        # Assume a conservative post-retirement return of 7% (shift from equity to debt)
        post_retirement_return = 0.07
        real_rate = ((1 + post_retirement_return) / (1 + inflation_rate)) - 1
        
        if abs(real_rate) < 0.0001:
            # Real rate near zero — simple multiplication
            retirement_corpus = annual_expenses_at_retirement * years_in_retirement
        elif real_rate > 0:
            # PV of growing annuity
            retirement_corpus = annual_expenses_at_retirement * (
                (1 - (1 + real_rate) ** (-years_in_retirement)) / real_rate
            )
        else:
            # Negative real rate — expenses grow faster than returns
            # Use the simple (conservative / overestimate) formula
            retirement_corpus = annual_expenses_at_retirement * years_in_retirement
        
        # Round to nearest rupee
        retirement_corpus = round(retirement_corpus, 2)
        monthly_expenses_at_retirement = round(monthly_expenses_at_retirement, 2)
        
        # Check for unrealistic values
        if retirement_corpus > current_monthly_expenses * 12 * 1000:
            raise UnrealisticValueError(
                'retirement_corpus',
                retirement_corpus,
                'Corpus is more than 1000x annual expenses. Please review inputs.'
            )
        
        return retirement_corpus, monthly_expenses_at_retirement
    
    @staticmethod
    def calculate_required_monthly_savings(
        current_savings: float,
        corpus_target: float,
        current_age: int,
        retirement_age: int,
        return_rate: float = DEFAULT_INVESTMENT_RETURN_RATE
    ) -> float:
        """
        Calculate monthly savings needed using Future Value of Annuity formula
        
        Formula:
        1. future_value_current = current_savings × (1 + return_rate)^(retirement_age - current_age)
        2. remaining_corpus = corpus_target - future_value_current
        3. monthly_savings = remaining_corpus / [((1 + return_rate)^(retirement_age - current_age) - 1) / return_rate]
        
        Args:
            current_savings: Accumulated retirement savings
            corpus_target: Target retirement corpus
            current_age: User's current age
            retirement_age: Target retirement age
            return_rate: Expected annual return rate (default 10%)
        
        Returns:
            Required monthly savings amount
        
        Raises:
            InvalidInputError: If inputs are invalid
        """
        # Validation is handled at the API level, no need to re-validate here
        
        years_to_retirement = retirement_age - current_age
        total_months = years_to_retirement * 12
        monthly_rate = return_rate / 12
        
        # Calculate future value of current savings (compound monthly)
        future_value_current = current_savings * (
            (1 + monthly_rate) ** total_months
        )
        
        # Calculate remaining corpus needed
        remaining_corpus = corpus_target - future_value_current
        
        # If remaining corpus is negative or zero, no monthly savings needed
        if remaining_corpus <= 0:
            return 0.0
        
        # Calculate annuity factor (monthly compounding)
        # annuity_factor = ((1 + r_monthly)^n_months - 1) / r_monthly
        annuity_factor = (
            ((1 + monthly_rate) ** total_months - 1) / monthly_rate
        )
        
        # Calculate required monthly savings
        monthly_savings = remaining_corpus / annuity_factor
        
        # Round to nearest rupee
        monthly_savings = round(monthly_savings, 2)
        
        return monthly_savings
    
    @staticmethod
    def calculate_monthly_expenses_at_retirement(
        current_monthly_expenses: float,
        inflation_rate: float,
        years_to_retirement: int
    ) -> float:
        """
        Calculate monthly expenses at retirement with inflation adjustment
        
        Formula:
        Future Expenses = Current Expenses × (1 + inflation_rate)^years
        
        Args:
            current_monthly_expenses: Current monthly expenses
            inflation_rate: Annual inflation rate
            years_to_retirement: Years until retirement
        
        Returns:
            Adjusted monthly expenses at retirement
        """
        # Validation is handled at the API level, no need to re-validate here
        
        # Calculate monthly expenses at retirement with inflation
        monthly_expenses_at_retirement = current_monthly_expenses * (
            (1 + inflation_rate) ** years_to_retirement
        )
        
        return round(monthly_expenses_at_retirement, 2)
    
    @staticmethod
    def calculate_projected_savings(
        current_savings: float,
        monthly_savings: float,
        current_age: int,
        retirement_age: int,
        return_rate: float = DEFAULT_INVESTMENT_RETURN_RATE
    ) -> float:
        """
        Calculate projected savings at retirement
        
        Formula:
        projected_savings = current_savings × (1 + r)^n + monthly_savings × [((1 + r)^n - 1) / r]
        
        Where:
        - current_savings grows with compound interest
        - monthly_savings accumulate with compound interest
        
        Args:
            current_savings: Accumulated retirement savings
            monthly_savings: Monthly savings amount
            current_age: User's current age
            retirement_age: Target retirement age
            return_rate: Expected annual return rate (default 10%)
        
        Returns:
            Projected savings at retirement
        """
        years_to_retirement = retirement_age - current_age
        total_months = years_to_retirement * 12
        monthly_rate = return_rate / 12
        
        # Future value of current savings (compound monthly)
        fv_current = current_savings * (
            (1 + monthly_rate) ** total_months
        )
        
        # Future value of monthly savings (annuity, monthly compounding)
        if monthly_savings > 0:
            annuity_factor = (
                ((1 + monthly_rate) ** total_months - 1) / monthly_rate
            )
            fv_monthly = monthly_savings * annuity_factor
        else:
            fv_monthly = 0.0
        
        # Total projected savings
        projected_savings = fv_current + fv_monthly
        
        # Round to nearest rupee
        projected_savings = round(projected_savings, 2)
        
        return projected_savings
    
    @staticmethod
    def calculate_gap(
        corpus_target: float,
        projected_savings: float
    ) -> GapAnalysis:
        """
        Calculate gap between target and projected savings
        
        Args:
            corpus_target: Target retirement corpus
            projected_savings: Projected savings at retirement
        
        Returns:
            GapAnalysis object with gap details
        """
        gap = corpus_target - projected_savings
        gap_percentage = (gap / corpus_target * 100) if corpus_target > 0 else 0
        is_shortfall = gap > 0
        
        # Round values
        gap = round(gap, 2)
        gap_percentage = round(gap_percentage, 2)
        
        # Calculate improvement paths
        improvement_paths = {}
        
        if is_shortfall:
            # Calculate percentage increase in monthly savings needed
            # This is a simplified calculation
            improvement_paths['increase_savings_percentage'] = round(
                (gap / projected_savings * 100) if projected_savings > 0 else 0, 2
            )
            
            # Calculate percentage increase in returns needed
            # Simplified: assume linear relationship
            improvement_paths['increase_returns_percentage'] = round(
                (gap / projected_savings * 100) if projected_savings > 0 else 0, 2
            )
        
        return GapAnalysis(
            corpus_target=corpus_target,
            projected_savings=projected_savings,
            gap=gap,
            gap_percentage=gap_percentage,
            is_shortfall=is_shortfall,
            improvement_paths=improvement_paths
        )
    
    @staticmethod
    def validate_inputs(
        current_age: int,
        retirement_age: int,
        current_salary: float,
        current_monthly_expenses: float,
        current_savings: float,
        inflation_rate: float = DEFAULT_INFLATION_RATE,
        investment_return_rate: float = DEFAULT_INVESTMENT_RETURN_RATE,
        life_expectancy: int = DEFAULT_LIFE_EXPECTANCY
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate all input parameters
        
        Args:
            current_age: User's current age
            retirement_age: Target retirement age
            current_salary: Annual income
            current_monthly_expenses: Monthly lifestyle expenses
            current_savings: Accumulated retirement savings
            inflation_rate: Annual inflation rate
            investment_return_rate: Expected annual return
            life_expectancy: Assumed lifespan
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            validate_retirement_plan_inputs(
                current_age,
                retirement_age,
                current_salary,
                current_monthly_expenses,
                current_savings,
                inflation_rate,
                investment_return_rate,
                life_expectancy
            )
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def estimate_corpus_from_salary(
        current_salary: float,
        multiplier: Optional[float] = None
    ) -> float:
        """
        Quick estimation of retirement corpus as multiple of annual salary
        
        For India, typical multiplier is 25-30x annual salary
        
        Args:
            current_salary: Annual income
            multiplier: Corpus multiplier (default: 25-30x)
        
        Returns:
            Estimated retirement corpus
        """
        if multiplier is None:
            # Use middle value
            multiplier = (CORPUS_MULTIPLIER_MIN + CORPUS_MULTIPLIER_MAX) / 2
        
        corpus = current_salary * multiplier
        return round(corpus, 2)
    
    @staticmethod
    def calculate_savings_rate_percentage(
        monthly_savings: float,
        current_monthly_income: float
    ) -> float:
        """
        Calculate savings as percentage of monthly income
        
        Args:
            monthly_savings: Monthly savings amount
            current_monthly_income: Monthly income
        
        Returns:
            Savings rate as percentage (0-100)
        """
        if current_monthly_income <= 0:
            return 0.0
        
        savings_rate = (monthly_savings / current_monthly_income) * 100
        return round(savings_rate, 2)
    
    @staticmethod
    def calculate_years_to_retirement(
        current_age: int,
        retirement_age: int
    ) -> int:
        """
        Calculate years until retirement
        
        Args:
            current_age: User's current age
            retirement_age: Target retirement age
        
        Returns:
            Years until retirement
        """
        return retirement_age - current_age

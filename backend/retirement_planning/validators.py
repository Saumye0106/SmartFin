"""
Input validation functions for Retirement Planning Calculator
"""

from typing import Tuple, Optional
from .exceptions import InvalidInputError, ConflictingInputError
from .constants import (
    MIN_CURRENT_AGE,
    MAX_CURRENT_AGE,
    MIN_RETIREMENT_AGE,
    MAX_RETIREMENT_AGE,
    MIN_SALARY,
    MIN_EXPENSES,
    MAX_INFLATION_RATE,
    MAX_INVESTMENT_RETURN_RATE,
    MIN_INVESTMENT_RETURN_RATE
)


def validate_current_age(current_age: int) -> Tuple[bool, Optional[str]]:
    """
    Validate current age
    
    Args:
        current_age: User's current age
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(current_age, int):
        raise InvalidInputError('current_age', current_age, f'integer between {MIN_CURRENT_AGE} and {MAX_CURRENT_AGE}')
    
    if current_age < MIN_CURRENT_AGE or current_age > MAX_CURRENT_AGE:
        raise InvalidInputError('current_age', current_age, f'{MIN_CURRENT_AGE} to {MAX_CURRENT_AGE}')
    
    return True, None


def validate_retirement_age(retirement_age: int, current_age: int) -> Tuple[bool, Optional[str]]:
    """
    Validate retirement age
    
    Args:
        retirement_age: Target retirement age
        current_age: Current age for comparison
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(retirement_age, int):
        raise InvalidInputError('retirement_age', retirement_age, f'integer between {MIN_RETIREMENT_AGE} and {MAX_RETIREMENT_AGE}')
    
    if retirement_age <= current_age:
        raise ConflictingInputError(f'retirement_age ({retirement_age}) must be greater than current_age ({current_age})')
    
    if retirement_age < MIN_RETIREMENT_AGE or retirement_age > MAX_RETIREMENT_AGE:
        raise InvalidInputError('retirement_age', retirement_age, f'{MIN_RETIREMENT_AGE} to {MAX_RETIREMENT_AGE}')
    
    return True, None


def validate_salary(current_salary: float) -> Tuple[bool, Optional[str]]:
    """
    Validate current salary
    
    Args:
        current_salary: Annual salary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(current_salary, (int, float)):
        raise InvalidInputError('current_salary', current_salary, 'positive number')
    
    if current_salary <= 0:
        raise InvalidInputError('current_salary', current_salary, f'greater than {MIN_SALARY}')
    
    return True, None


def validate_monthly_expenses(current_monthly_expenses: float) -> Tuple[bool, Optional[str]]:
    """
    Validate monthly expenses
    
    Args:
        current_monthly_expenses: Monthly lifestyle expenses
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(current_monthly_expenses, (int, float)):
        raise InvalidInputError('current_monthly_expenses', current_monthly_expenses, 'positive number')
    
    if current_monthly_expenses <= 0:
        raise InvalidInputError('current_monthly_expenses', current_monthly_expenses, f'greater than {MIN_EXPENSES}')
    
    return True, None


def validate_current_savings(current_savings: float) -> Tuple[bool, Optional[str]]:
    """
    Validate current savings
    
    Args:
        current_savings: Accumulated retirement savings
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(current_savings, (int, float)):
        raise InvalidInputError('current_savings', current_savings, 'non-negative number')
    
    if current_savings < 0:
        raise InvalidInputError('current_savings', current_savings, 'greater than or equal to 0')
    
    return True, None


def validate_inflation_rate(inflation_rate: float) -> Tuple[bool, Optional[str]]:
    """
    Validate inflation rate
    
    Args:
        inflation_rate: Annual inflation rate (0-1)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(inflation_rate, (int, float)):
        raise InvalidInputError('inflation_rate', inflation_rate, 'number between 0 and 0.15')
    
    if inflation_rate < 0 or inflation_rate > MAX_INFLATION_RATE:
        raise InvalidInputError('inflation_rate', inflation_rate, f'0 to {MAX_INFLATION_RATE} (0% to 15%)')
    
    return True, None


def validate_investment_return_rate(investment_return_rate: float) -> Tuple[bool, Optional[str]]:
    """
    Validate investment return rate
    
    Args:
        investment_return_rate: Expected annual return rate (0-1)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(investment_return_rate, (int, float)):
        raise InvalidInputError('investment_return_rate', investment_return_rate, 'number between 0 and 0.30')
    
    if investment_return_rate < MIN_INVESTMENT_RETURN_RATE or investment_return_rate > MAX_INVESTMENT_RETURN_RATE:
        raise InvalidInputError('investment_return_rate', investment_return_rate, f'{MIN_INVESTMENT_RETURN_RATE} to {MAX_INVESTMENT_RETURN_RATE} (0% to 30%)')
    
    return True, None


def validate_life_expectancy(life_expectancy: int, retirement_age: int) -> Tuple[bool, Optional[str]]:
    """
    Validate life expectancy
    
    Args:
        life_expectancy: Assumed lifespan
        retirement_age: Retirement age for comparison
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(life_expectancy, int):
        raise InvalidInputError('life_expectancy', life_expectancy, 'integer greater than retirement_age')
    
    if life_expectancy <= retirement_age:
        raise ConflictingInputError(f'life_expectancy ({life_expectancy}) must be greater than retirement_age ({retirement_age})')
    
    if life_expectancy < 60 or life_expectancy > 120:
        raise InvalidInputError('life_expectancy', life_expectancy, '60 to 120 years')
    
    return True, None


def validate_retirement_plan_inputs(
    current_age: int,
    retirement_age: int,
    current_salary: float,
    current_monthly_expenses: float,
    current_savings: float,
    inflation_rate: float = 0.06,
    investment_return_rate: float = 0.10,
    life_expectancy: int = 85
) -> Tuple[bool, Optional[str]]:
    """
    Validate all retirement plan inputs
    
    Args:
        current_age: User's current age
        retirement_age: Target retirement age
        current_salary: Annual income
        current_monthly_expenses: Monthly lifestyle expenses
        current_savings: Accumulated retirement savings
        inflation_rate: Annual inflation rate (default 6%)
        investment_return_rate: Expected annual return (default 10%)
        life_expectancy: Assumed lifespan (default 85)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate individual fields
    validate_current_age(current_age)
    validate_retirement_age(retirement_age, current_age)
    validate_salary(current_salary)
    validate_monthly_expenses(current_monthly_expenses)
    validate_current_savings(current_savings)
    validate_inflation_rate(inflation_rate)
    validate_investment_return_rate(investment_return_rate)
    validate_life_expectancy(life_expectancy, retirement_age)
    
    return True, None


def validate_scenario_parameters(
    retirement_age: int,
    monthly_savings: float,
    investment_return_rate: float,
    inflation_rate: float,
    current_age: int
) -> Tuple[bool, Optional[str]]:
    """
    Validate scenario parameters
    
    Args:
        retirement_age: Target retirement age
        monthly_savings: Monthly savings amount
        investment_return_rate: Expected annual return
        inflation_rate: Annual inflation rate
        current_age: Current age for comparison
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    validate_retirement_age(retirement_age, current_age)
    
    if not isinstance(monthly_savings, (int, float)):
        raise InvalidInputError('monthly_savings', monthly_savings, 'positive number')
    
    if monthly_savings < 0:
        raise InvalidInputError('monthly_savings', monthly_savings, 'greater than or equal to 0')
    
    validate_investment_return_rate(investment_return_rate)
    validate_inflation_rate(inflation_rate)
    
    return True, None



class RetirementPlanValidator:
    """Validator class for retirement plan inputs"""
    
    def validate_plan_inputs(self, data: dict) -> Tuple[bool, Optional[str]]:
        """
        Validate all retirement plan inputs from request data
        
        Args:
            data: Dictionary containing plan input parameters
        
        Returns:
            Tuple of (is_valid, error_message)
        
        Raises:
            InvalidInputError: If any input is invalid
            ConflictingInputError: If inputs conflict with each other
        """
        required_fields = [
            'current_age', 'retirement_age', 'current_salary',
            'current_monthly_expenses', 'current_savings'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                raise InvalidInputError(field, None, 'required field')
        
        # Validate individual fields
        validate_current_age(data['current_age'])
        validate_retirement_age(data['retirement_age'], data['current_age'])
        validate_salary(data['current_salary'])
        validate_monthly_expenses(data['current_monthly_expenses'])
        validate_current_savings(data['current_savings'])
        
        # Validate optional fields with defaults
        inflation_rate = data.get('inflation_rate', 0.06)
        investment_return_rate = data.get('investment_return_rate', 0.10)
        life_expectancy = data.get('life_expectancy', 85)
        
        validate_inflation_rate(inflation_rate)
        validate_investment_return_rate(investment_return_rate)
        validate_life_expectancy(life_expectancy, data['retirement_age'])
        
        return True, None

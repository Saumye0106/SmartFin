"""
Constants and configuration for Retirement Planning Calculator
"""

# Default calculation parameters
DEFAULT_INFLATION_RATE = 0.06  # 6% annual inflation
DEFAULT_INVESTMENT_RETURN_RATE = 0.10  # 10% annual return
DEFAULT_LIFE_EXPECTANCY = 85  # Years

# Age constraints
MIN_CURRENT_AGE = 18
MAX_CURRENT_AGE = 75
MIN_RETIREMENT_AGE = 40
MAX_RETIREMENT_AGE = 75

# Financial constraints
MIN_SALARY = 0.01
MIN_EXPENSES = 0.01
MAX_INFLATION_RATE = 0.15  # 15% max
MAX_INVESTMENT_RETURN_RATE = 0.30  # 30% max
MIN_INVESTMENT_RETURN_RATE = 0.0

# Savings achievability (fraction of monthly income)
# <= 35% of income = easily achievable
# 35-50% of income = marginal
# > 50% of income = not achievable
SAVINGS_ACHIEVABILITY_THRESHOLD = 0.35
SAVINGS_ACHIEVABILITY_MARGINAL_THRESHOLD = 0.50

# Readiness score weights (must sum to 1.0)
READINESS_SCORE_WEIGHTS = {
    'financial_health': 0.30,      # ML model score
    'savings_adequacy': 0.25,      # Current savings vs target
    'savings_rate': 0.20,          # Can achieve required savings
    'debt_burden': 0.15,           # Loan obligations
    'time_horizon': 0.10           # Years until retirement
}

# Readiness score classifications
READINESS_CLASSIFICATIONS = {
    'excellent': (80, 100),
    'good': (60, 79),
    'fair': (40, 59),
    'poor': (20, 39),
    'critical': (0, 19)
}

# Time horizon factors
TIME_HORIZON_FACTORS = {
    'very_long': (15, 100),      # >15 years: 100 points
    'long': (10, 15),            # 10-15 years: 80 points
    'medium': (5, 10),           # 5-10 years: 60 points
    'short': (0, 5)              # <5 years: 40 points
}

# Savings rate factors
SAVINGS_RATE_ACHIEVABLE = 100      # Can achieve required savings
SAVINGS_RATE_MARGINAL = 50         # Marginal achievability
SAVINGS_RATE_NOT_ACHIEVABLE = 20   # Cannot achieve required savings

# Debt burden calculation
DEBT_BURDEN_CRITICAL_RATIO = 2.0   # Debt > 2x annual salary is critical

# Scenario limits
MAX_SCENARIOS_PER_PLAN = 5
PRESET_SCENARIOS = {
    'conservative': {
        'return_rate': 0.08,
        'retirement_age': 65,
        'description': 'Conservative approach with lower returns'
    },
    'moderate': {
        'return_rate': 0.10,
        'retirement_age': 60,
        'description': 'Balanced approach with moderate returns'
    },
    'aggressive': {
        'return_rate': 0.12,
        'retirement_age': 55,
        'description': 'Aggressive approach with higher returns'
    }
}

# Action plan
MIN_RECOMMENDATIONS = 3
MAX_RECOMMENDATIONS = 5

# Corpus multiplier for quick estimation (25-30x annual salary for India)
CORPUS_MULTIPLIER_MIN = 25
CORPUS_MULTIPLIER_MAX = 30

# Database
SOFT_DELETE_MARKER = 'deleted_at'

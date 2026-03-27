"""
Retirement Planning Calculator Module

A comprehensive retirement planning system that helps users calculate retirement corpus,
determine savings requirements, assess retirement readiness, and create personalized
action plans for achieving retirement goals.

Key Components:
- Calculation Engine: Core retirement calculations
- Readiness Scoring Engine: 5-factor retirement readiness assessment
- Scenario Analysis Engine: What-if modeling and scenario comparison
- Recommendation Engine: Personalized action plan generation
- Integration Manager: Integration with existing SmartFin systems
- Parser & Serializer: JSON serialization/deserialization

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "SmartFin Team"

from .models import RetirementPlan, RetirementScenario
from .exceptions import (
    RetirementPlanningException,
    InvalidInputError,
    ConflictingInputError,
    UnrealisticValueError,
    SerializationError,
    IntegrationError
)
from .constants import (
    DEFAULT_INFLATION_RATE,
    DEFAULT_INVESTMENT_RETURN_RATE,
    DEFAULT_LIFE_EXPECTANCY,
    MIN_CURRENT_AGE,
    MAX_RETIREMENT_AGE,
    MAX_SCENARIOS_PER_PLAN,
    SAVINGS_ACHIEVABILITY_THRESHOLD,
    READINESS_SCORE_WEIGHTS
)

__all__ = [
    'RetirementPlan',
    'RetirementScenario',
    'RetirementPlanningException',
    'InvalidInputError',
    'ConflictingInputError',
    'UnrealisticValueError',
    'SerializationError',
    'IntegrationError',
    'DEFAULT_INFLATION_RATE',
    'DEFAULT_INVESTMENT_RETURN_RATE',
    'DEFAULT_LIFE_EXPECTANCY',
    'MIN_CURRENT_AGE',
    'MAX_RETIREMENT_AGE',
    'MAX_SCENARIOS_PER_PLAN',
    'SAVINGS_ACHIEVABILITY_THRESHOLD',
    'READINESS_SCORE_WEIGHTS'
]

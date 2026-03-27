"""
Scenario Analysis Engine

Supports what-if modeling with multiple scenarios:
- Create and save scenarios with modified parameters
- Real-time recalculation of results
- Side-by-side scenario comparison
- Preset scenarios (Conservative, Moderate, Aggressive)
- Primary scenario management
"""

import uuid
from typing import Dict, List, Optional, Tuple
from .models import RetirementScenario
from .calculation_engine import RetirementCalculationEngine
from .readiness_scoring_engine import RetirementReadinessScoringEngine
from .exceptions import (
    ScenarioNotFoundError,
    ScenarioLimitExceededError,
    DuplicateScenarioNameError,
    InvalidInputError
)
from .validators import validate_scenario_parameters
from .constants import (
    MAX_SCENARIOS_PER_PLAN,
    PRESET_SCENARIOS,
    DEFAULT_INFLATION_RATE,
    DEFAULT_INVESTMENT_RETURN_RATE
)


class ScenarioAnalysisEngine:
    """
    Manages what-if scenario analysis for retirement planning
    
    Allows users to create multiple scenarios with different parameters,
    compare them side-by-side, and identify the best retirement strategy.
    """
    
    PRESET_SCENARIOS = PRESET_SCENARIOS
    
    @staticmethod
    def create_scenario(
        plan_id: str,
        scenario_name: str,
        retirement_age: int,
        monthly_savings: float,
        investment_return_rate: float,
        inflation_rate: float,
        current_age: int,
        desired_retirement_lifestyle: Optional[float] = None
    ) -> RetirementScenario:
        """
        Create and save a new scenario
        
        Args:
            plan_id: Reference to parent plan
            scenario_name: User-provided scenario name
            retirement_age: Target retirement age for this scenario
            monthly_savings: Monthly savings for this scenario
            investment_return_rate: Expected return rate for this scenario
            inflation_rate: Inflation rate for this scenario
            current_age: Current age (for validation)
            desired_retirement_lifestyle: Optional lifestyle expenses
        
        Returns:
            RetirementScenario object
        
        Raises:
            InvalidInputError: If parameters are invalid
        """
        # Validate parameters
        validate_scenario_parameters(
            retirement_age,
            monthly_savings,
            investment_return_rate,
            inflation_rate,
            current_age
        )
        
        # Create scenario
        scenario_id = str(uuid.uuid4())
        scenario = RetirementScenario(
            scenario_id=scenario_id,
            plan_id=plan_id,
            scenario_name=scenario_name,
            retirement_age=retirement_age,
            monthly_savings=monthly_savings,
            investment_return_rate=investment_return_rate,
            inflation_rate=inflation_rate,
            desired_retirement_lifestyle=desired_retirement_lifestyle
        )
        
        return scenario
    
    @staticmethod
    def update_scenario(
        scenario: RetirementScenario,
        **kwargs
    ) -> RetirementScenario:
        """
        Update scenario parameters and recalculate results
        
        Args:
            scenario: Scenario to update
            **kwargs: Parameters to update (retirement_age, monthly_savings, etc.)
        
        Returns:
            Updated RetirementScenario object
        """
        # Update parameters
        for key, value in kwargs.items():
            if hasattr(scenario, key):
                setattr(scenario, key, value)
        
        return scenario
    
    @staticmethod
    def calculate_scenario_results(
        scenario: RetirementScenario,
        current_savings: float,
        corpus_target: float,
        current_age: int,
        financial_health_score: float = 0.0,
        total_loan_amount: float = 0.0,
        annual_salary: float = 0.0
    ) -> RetirementScenario:
        """
        Calculate results for a scenario
        
        Args:
            scenario: Scenario to calculate
            current_savings: Current accumulated savings
            corpus_target: Target retirement corpus
            current_age: Current age
            financial_health_score: Financial health score
            total_loan_amount: Total loan amount
            annual_salary: Annual salary
        
        Returns:
            Scenario with calculated results
        """
        # Calculate projected savings
        projected_savings = RetirementCalculationEngine.calculate_projected_savings(
            current_savings,
            scenario.monthly_savings,
            current_age,
            scenario.retirement_age,
            scenario.investment_return_rate
        )
        
        # Calculate gap
        gap = corpus_target - projected_savings
        
        # Calculate readiness score for this scenario
        current_monthly_income = annual_salary / 12 if annual_salary > 0 else 0
        
        readiness_assessment = RetirementReadinessScoringEngine.calculate_full_assessment(
            current_age,
            scenario.retirement_age,
            # Use scenario projected savings as adequacy basis so readiness
            # reflects scenario-specific contribution trajectory.
            projected_savings,
            corpus_target,
            scenario.monthly_savings,
            current_monthly_income,
            total_loan_amount,
            annual_salary,
            financial_health_score
        )
        
        # Update scenario with results
        scenario.retirement_corpus = corpus_target
        scenario.projected_savings = projected_savings
        scenario.gap = gap
        scenario.readiness_score = readiness_assessment.readiness_score
        
        return scenario
    
    @staticmethod
    def compare_scenarios(
        scenarios: List[RetirementScenario]
    ) -> Dict:
        """
        Compare multiple scenarios side-by-side
        
        Args:
            scenarios: List of scenarios to compare
        
        Returns:
            Comparison data with best scenario highlighted
        """
        if not scenarios:
            return {}
        
        # Find best scenario (highest readiness score)
        best_scenario = max(scenarios, key=lambda s: s.readiness_score)
        
        # Build comparison data
        comparison = {
            'scenarios': [],
            'best_scenario_id': best_scenario.scenario_id,
            'best_scenario_name': best_scenario.scenario_name,
            'best_readiness_score': best_scenario.readiness_score
        }
        
        for scenario in scenarios:
            scenario_data = {
                'scenario_id': scenario.scenario_id,
                'scenario_name': scenario.scenario_name,
                'retirement_age': scenario.retirement_age,
                'monthly_savings': scenario.monthly_savings,
                'investment_return_rate': scenario.investment_return_rate,
                'inflation_rate': scenario.inflation_rate,
                'retirement_corpus': scenario.retirement_corpus,
                'required_monthly_savings': scenario.required_monthly_savings,
                'projected_savings': scenario.projected_savings,
                'gap': scenario.gap,
                'readiness_score': scenario.readiness_score,
                'is_best': scenario.scenario_id == best_scenario.scenario_id
            }
            comparison['scenarios'].append(scenario_data)
        
        return comparison
    
    @staticmethod
    def get_preset_scenario(
        preset_name: str,
        current_age: int,
        current_savings: float,
        corpus_target: float,
        annual_salary: float
    ) -> Dict:
        """
        Get preset scenario parameters
        
        Args:
            preset_name: Name of preset ('conservative', 'moderate', 'aggressive')
            current_age: Current age
            current_savings: Current savings
            corpus_target: Target corpus
            annual_salary: Annual salary
        
        Returns:
            Preset scenario parameters
        
        Raises:
            InvalidInputError: If preset not found
        """
        if preset_name not in ScenarioAnalysisEngine.PRESET_SCENARIOS:
            raise InvalidInputError(
                'preset_name',
                preset_name,
                f'one of {list(ScenarioAnalysisEngine.PRESET_SCENARIOS.keys())}'
            )
        
        preset = ScenarioAnalysisEngine.PRESET_SCENARIOS[preset_name]
        
        # Calculate required monthly savings for this preset
        required_monthly_savings = RetirementCalculationEngine.calculate_required_monthly_savings(
            current_savings,
            corpus_target,
            current_age,
            preset['retirement_age'],
            preset['return_rate']
        )
        
        return {
            'preset_name': preset_name,
            'description': preset['description'],
            'retirement_age': preset['retirement_age'],
            'investment_return_rate': preset['return_rate'],
            'required_monthly_savings': required_monthly_savings,
            'inflation_rate': DEFAULT_INFLATION_RATE
        }
    
    @staticmethod
    def set_primary_scenario(
        scenarios: List[RetirementScenario],
        scenario_id: str
    ) -> List[RetirementScenario]:
        """
        Set scenario as primary plan
        
        Args:
            scenarios: List of scenarios
            scenario_id: ID of scenario to set as primary
        
        Returns:
            Updated list of scenarios
        
        Raises:
            ScenarioNotFoundError: If scenario not found
        """
        found = False
        for scenario in scenarios:
            if scenario.scenario_id == scenario_id:
                scenario.is_primary = True
                found = True
            else:
                scenario.is_primary = False
        
        if not found:
            raise ScenarioNotFoundError(scenario_id)
        
        return scenarios
    
    @staticmethod
    def validate_scenario_limit(
        existing_scenarios: List[RetirementScenario],
        max_scenarios: int = MAX_SCENARIOS_PER_PLAN
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that scenario limit is not exceeded
        
        Args:
            existing_scenarios: List of existing scenarios
            max_scenarios: Maximum allowed scenarios
        
        Returns:
            Tuple of (is_valid, error_message)
        
        Raises:
            ScenarioLimitExceededError: If limit exceeded
        """
        if len(existing_scenarios) >= max_scenarios:
            raise ScenarioLimitExceededError(max_scenarios)
        
        return True, None
    
    @staticmethod
    def validate_scenario_name_unique(
        scenario_name: str,
        existing_scenarios: List[RetirementScenario]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that scenario name is unique
        
        Args:
            scenario_name: Name to validate
            existing_scenarios: List of existing scenarios
        
        Returns:
            Tuple of (is_valid, error_message)
        
        Raises:
            DuplicateScenarioNameError: If name already exists
        """
        for scenario in existing_scenarios:
            if scenario.scenario_name.lower() == scenario_name.lower():
                raise DuplicateScenarioNameError(scenario_name)
        
        return True, None
    
    @staticmethod
    def get_scenario_summary(scenario: RetirementScenario) -> Dict:
        """
        Get summary of scenario
        
        Args:
            scenario: Scenario to summarize
        
        Returns:
            Summary dictionary
        """
        return {
            'scenario_id': scenario.scenario_id,
            'scenario_name': scenario.scenario_name,
            'retirement_age': scenario.retirement_age,
            'monthly_savings': scenario.monthly_savings,
            'investment_return_rate': scenario.investment_return_rate,
            'inflation_rate': scenario.inflation_rate,
            'projected_savings': scenario.projected_savings,
            'gap': scenario.gap,
            'readiness_score': scenario.readiness_score,
            'is_primary': scenario.is_primary,
            'created_at': scenario.created_at
        }
    
    @staticmethod
    def calculate_scenario_impact(
        base_scenario: RetirementScenario,
        modified_scenario: RetirementScenario
    ) -> Dict:
        """
        Calculate impact of scenario changes
        
        Args:
            base_scenario: Original scenario
            modified_scenario: Modified scenario
        
        Returns:
            Impact analysis dictionary
        """
        impact = {
            'retirement_age_change': modified_scenario.retirement_age - base_scenario.retirement_age,
            'monthly_savings_change': modified_scenario.monthly_savings - base_scenario.monthly_savings,
            'return_rate_change': modified_scenario.investment_return_rate - base_scenario.investment_return_rate,
            'projected_savings_change': modified_scenario.projected_savings - base_scenario.projected_savings,
            'gap_change': modified_scenario.gap - base_scenario.gap,
            'readiness_score_change': modified_scenario.readiness_score - base_scenario.readiness_score
        }
        
        return impact

"""
Retirement Plan Parser & Serializer

Handles JSON serialization/deserialization of retirement plans with validation
"""

import json
from typing import Dict, Any, Optional, Tuple
from .models import RetirementPlan, RetirementScenario
from .exceptions import SerializationError


class RetirementPlanSerializer:
    """
    Serializes and deserializes retirement plans to/from JSON
    
    Ensures data integrity through validation and supports round-trip
    consistency (serialize → deserialize → serialize produces same result).
    """
    
    # Required fields for plan validation
    REQUIRED_PLAN_FIELDS = [
        'plan_id', 'user_id', 'plan_name',
        'current_age', 'retirement_age', 'current_salary',
        'current_monthly_expenses', 'current_savings'
    ]
    
    REQUIRED_SCENARIO_FIELDS = [
        'scenario_id', 'plan_id', 'scenario_name',
        'retirement_age', 'monthly_savings',
        'investment_return_rate', 'inflation_rate'
    ]
    
    @staticmethod
    def serialize_plan(plan: RetirementPlan) -> Dict[str, Any]:
        """
        Serialize retirement plan to dictionary
        
        Args:
            plan: RetirementPlan object
        
        Returns:
            Dictionary representation (for API responses)
        
        Raises:
            SerializationError: If serialization fails
        """
        try:
            plan_dict = plan.to_dict()
            return plan_dict
        except Exception as e:
            raise SerializationError(f"Failed to serialize plan: {str(e)}")
    
    @staticmethod
    def deserialize_plan(json_str: str) -> RetirementPlan:
        """
        Deserialize JSON string to retirement plan object
        
        Args:
            json_str: JSON string
        
        Returns:
            RetirementPlan object
        
        Raises:
            SerializationError: If deserialization or validation fails
        """
        try:
            data = json.loads(json_str)
            
            # Validate required fields
            is_valid, error_msg = RetirementPlanSerializer.validate_plan_json(json_str)
            if not is_valid:
                raise SerializationError(error_msg)
            
            plan = RetirementPlan.from_dict(data)
            return plan
        except json.JSONDecodeError as e:
            raise SerializationError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            raise SerializationError(f"Failed to deserialize plan: {str(e)}")
    
    @staticmethod
    def validate_plan_json(json_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON structure and field values
        
        Args:
            json_str: JSON string to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}"
        
        # Check required fields
        for field in RetirementPlanSerializer.REQUIRED_PLAN_FIELDS:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        # Validate field types
        type_validations = {
            'plan_id': str,
            'user_id': int,
            'plan_name': str,
            'current_age': int,
            'retirement_age': int,
            'current_salary': (int, float),
            'current_monthly_expenses': (int, float),
            'current_savings': (int, float),
            'inflation_rate': (int, float),
            'investment_return_rate': (int, float),
            'life_expectancy': int,
            'readiness_score': (int, float),
            'retirement_corpus': (int, float)
        }
        
        for field, expected_type in type_validations.items():
            if field in data:
                if not isinstance(data[field], expected_type):
                    return False, f"Invalid type for {field}: expected {expected_type}, got {type(data[field])}"
        
        # Validate value ranges
        if data.get('current_age', 0) < 18 or data.get('current_age', 0) > 75:
            return False, "current_age must be between 18 and 75"
        
        if data.get('retirement_age', 0) <= data.get('current_age', 0):
            return False, "retirement_age must be greater than current_age"
        
        if data.get('current_salary', 0) <= 0:
            return False, "current_salary must be positive"
        
        if data.get('current_monthly_expenses', 0) <= 0:
            return False, "current_monthly_expenses must be positive"
        
        if data.get('readiness_score', 0) < 0 or data.get('readiness_score', 0) > 100:
            return False, "readiness_score must be between 0 and 100"
        
        return True, None
    
    @staticmethod
    def serialize_scenario(scenario: RetirementScenario) -> str:
        """
        Serialize scenario to JSON string
        
        Args:
            scenario: RetirementScenario object
        
        Returns:
            JSON string representation
        
        Raises:
            SerializationError: If serialization fails
        """
        try:
            scenario_dict = scenario.to_dict()
            json_str = json.dumps(scenario_dict, default=str, indent=2)
            return json_str
        except Exception as e:
            raise SerializationError(f"Failed to serialize scenario: {str(e)}")
    
    @staticmethod
    def deserialize_scenario(json_str: str) -> RetirementScenario:
        """
        Deserialize JSON string to scenario object
        
        Args:
            json_str: JSON string
        
        Returns:
            RetirementScenario object
        
        Raises:
            SerializationError: If deserialization or validation fails
        """
        try:
            data = json.loads(json_str)
            
            # Validate required fields
            for field in RetirementPlanSerializer.REQUIRED_SCENARIO_FIELDS:
                if field not in data:
                    raise SerializationError(f"Missing required field: {field}")
            
            scenario = RetirementScenario.from_dict(data)
            return scenario
        except json.JSONDecodeError as e:
            raise SerializationError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            raise SerializationError(f"Failed to deserialize scenario: {str(e)}")
    
    @staticmethod
    def export_plan_to_json(plan: RetirementPlan) -> str:
        """
        Export plan to JSON for external use
        
        Args:
            plan: RetirementPlan object
        
        Returns:
            JSON string
        """
        return RetirementPlanSerializer.serialize_plan(plan)
    
    @staticmethod
    def import_plan_from_json(json_str: str) -> RetirementPlan:
        """
        Import plan from JSON
        
        Args:
            json_str: JSON string
        
        Returns:
            RetirementPlan object
        """
        return RetirementPlanSerializer.deserialize_plan(json_str)
    
    @staticmethod
    def validate_round_trip(plan: RetirementPlan) -> bool:
        """
        Validate round-trip consistency
        
        Serializes and deserializes plan, then compares key fields
        
        Args:
            plan: RetirementPlan object
        
        Returns:
            True if round-trip is consistent
        """
        try:
            # Serialize
            json_str = RetirementPlanSerializer.serialize_plan(plan)
            
            # Deserialize
            restored_plan = RetirementPlanSerializer.deserialize_plan(json_str)
            
            # Compare key fields
            key_fields = [
                'plan_id', 'user_id', 'plan_name',
                'current_age', 'retirement_age', 'current_salary',
                'current_monthly_expenses', 'current_savings',
                'readiness_score', 'retirement_corpus'
            ]
            
            for field in key_fields:
                original_value = getattr(plan, field)
                restored_value = getattr(restored_plan, field)
                
                # Handle floating point comparison
                if isinstance(original_value, float):
                    if abs(original_value - restored_value) > 0.01:
                        return False
                else:
                    if original_value != restored_value:
                        return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_plan_summary(plan: RetirementPlan) -> Dict[str, Any]:
        """
        Get summary of plan for display
        
        Args:
            plan: RetirementPlan object
        
        Returns:
            Summary dictionary
        """
        return {
            'plan_id': plan.plan_id,
            'plan_name': plan.plan_name,
            'current_age': plan.current_age,
            'retirement_age': plan.retirement_age,
            'years_to_retirement': plan.retirement_age - plan.current_age,
            'current_salary': plan.current_salary,
            'current_savings': plan.current_savings,
            'retirement_corpus': plan.retirement_corpus,
            'required_monthly_savings': plan.required_monthly_savings,
            'projected_savings': plan.projected_savings,
            'gap': plan.gap,
            'readiness_score': plan.readiness_score,
            'readiness_classification': plan.readiness_classification,
            'created_at': plan.created_at,
            'updated_at': plan.updated_at
        }

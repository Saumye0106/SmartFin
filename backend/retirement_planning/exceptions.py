"""
Custom exceptions for Retirement Planning Calculator
"""


class RetirementPlanningException(Exception):
    """Base exception for all retirement planning errors"""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code or 'RETIREMENT_PLANNING_ERROR'
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary for API responses"""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code
        }


class InvalidInputError(RetirementPlanningException):
    """Raised when input validation fails"""
    
    def __init__(self, field: str, value, valid_range: str = None):
        self.field = field
        self.value = value
        self.valid_range = valid_range
        
        if valid_range:
            message = f"Invalid {field}: {value}. Valid range: {valid_range}"
        else:
            message = f"Invalid {field}: {value}"
        
        super().__init__(message, 'INVALID_INPUT')


class ConflictingInputError(RetirementPlanningException):
    """Raised when inputs conflict with each other"""
    
    def __init__(self, message: str):
        super().__init__(message, 'CONFLICTING_INPUT')


class UnrealisticValueError(RetirementPlanningException):
    """Raised when calculation results in unrealistic values"""
    
    def __init__(self, field: str, value, reason: str):
        message = f"Unrealistic {field}: {value}. Reason: {reason}"
        super().__init__(message, 'UNREALISTIC_VALUE')


class SerializationError(RetirementPlanningException):
    """Raised when JSON serialization/deserialization fails"""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, 'SERIALIZATION_ERROR')


class IntegrationError(RetirementPlanningException):
    """Raised when integration with external systems fails"""
    
    def __init__(self, system: str, message: str):
        self.system = system
        full_message = f"Integration error with {system}: {message}"
        super().__init__(full_message, 'INTEGRATION_ERROR')


class PlanNotFoundError(RetirementPlanningException):
    """Raised when a retirement plan is not found"""
    
    def __init__(self, plan_id: str):
        message = f"Retirement plan not found: {plan_id}"
        super().__init__(message, 'PLAN_NOT_FOUND')


class ScenarioNotFoundError(RetirementPlanningException):
    """Raised when a scenario is not found"""
    
    def __init__(self, scenario_id: str):
        message = f"Scenario not found: {scenario_id}"
        super().__init__(message, 'SCENARIO_NOT_FOUND')


class ScenarioLimitExceededError(RetirementPlanningException):
    """Raised when scenario limit is exceeded"""
    
    def __init__(self, max_scenarios: int):
        message = f"Maximum scenarios ({max_scenarios}) exceeded"
        super().__init__(message, 'SCENARIO_LIMIT_EXCEEDED')


class DuplicateScenarioNameError(RetirementPlanningException):
    """Raised when scenario name is duplicate"""
    
    def __init__(self, scenario_name: str):
        message = f"Scenario name already exists: {scenario_name}"
        super().__init__(message, 'DUPLICATE_SCENARIO_NAME')



class ValidationError(RetirementPlanningException):
    """Raised when validation fails"""
    
    def __init__(self, message: str):
        super().__init__(message, 'VALIDATION_ERROR')


class CalculationError(RetirementPlanningException):
    """Raised when calculation fails"""
    
    def __init__(self, message: str):
        super().__init__(message, 'CALCULATION_ERROR')

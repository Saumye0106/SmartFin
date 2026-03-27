"""
Data models for Retirement Planning Calculator
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class RetirementPlan:
    """Represents a complete retirement plan with calculations and assessments"""
    
    # Identifiers
    plan_id: str
    user_id: int
    plan_name: str
    
    # Input Parameters
    current_age: int
    retirement_age: int
    current_salary: float
    current_monthly_expenses: float
    current_savings: float
    inflation_rate: float = 0.06
    investment_return_rate: float = 0.10
    life_expectancy: int = 85
    desired_retirement_lifestyle: Optional[float] = None
    
    # Calculated Results
    retirement_corpus: float = 0.0
    monthly_expenses_at_retirement: float = 0.0
    required_monthly_savings: float = 0.0
    projected_savings: float = 0.0
    gap: float = 0.0
    gap_percentage: float = 0.0
    
    # Readiness Assessment
    readiness_score: float = 0.0
    readiness_classification: str = 'critical'
    financial_health_factor: float = 0.0
    savings_adequacy_factor: float = 0.0
    savings_rate_factor: float = 0.0
    debt_burden_factor: float = 0.0
    time_horizon_factor: float = 0.0
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_primary: bool = False
    deleted_at: Optional[str] = None
    
    # Relationships
    scenarios: List[str] = field(default_factory=list)
    action_plan: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert plan to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetirementPlan':
        """Create plan from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RetirementPlan':
        """Create plan from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_deleted(self) -> bool:
        """Check if plan is soft-deleted"""
        return self.deleted_at is not None
    
    def mark_deleted(self) -> None:
        """Mark plan as deleted (soft delete)"""
        self.deleted_at = datetime.utcnow().isoformat()
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow().isoformat()


@dataclass
class RetirementScenario:
    """Represents a what-if scenario for retirement planning"""
    
    # Identifiers
    scenario_id: str
    plan_id: str
    scenario_name: str
    
    # Modified Parameters
    retirement_age: int
    monthly_savings: float
    investment_return_rate: float
    inflation_rate: float
    desired_retirement_lifestyle: Optional[float] = None
    
    # Calculated Results
    retirement_corpus: float = 0.0
    required_monthly_savings: float = 0.0
    projected_savings: float = 0.0
    gap: float = 0.0
    readiness_score: float = 0.0
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_primary: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert scenario to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetirementScenario':
        """Create scenario from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RetirementScenario':
        """Create scenario from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class RetirementReadinessAssessment:
    """Represents the retirement readiness assessment"""
    
    readiness_score: float
    classification: str
    financial_health_factor: float
    savings_adequacy_factor: float
    savings_rate_factor: float
    debt_burden_factor: float
    time_horizon_factor: float
    factors_breakdown: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment to dictionary"""
        return asdict(self)


@dataclass
class GapAnalysis:
    """Represents gap analysis between target and projected savings"""
    
    corpus_target: float
    projected_savings: float
    gap: float
    gap_percentage: float
    is_shortfall: bool
    improvement_paths: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert gap analysis to dictionary"""
        return asdict(self)


@dataclass
class ActionPlanItem:
    """Represents a single action plan recommendation"""
    
    action_id: str
    priority: int  # 1 = highest priority
    action_type: str  # 'increase_savings', 'improve_returns', 'delay_retirement', etc.
    description: str
    estimated_impact_on_score: float  # Points improvement on readiness score
    timeline: str  # 'immediate', 'short_term', 'long_term'
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary"""
        return asdict(self)

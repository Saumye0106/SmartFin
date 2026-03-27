# Retirement Planning Calculator

A comprehensive retirement planning system for SmartFin that helps users calculate retirement corpus, determine savings requirements, assess retirement readiness, and create personalized action plans.

## Quick Start

### Installation

```python
from backend.retirement_planning import (
    RetirementPlan,
    RetirementCalculationEngine,
    RetirementReadinessScoringEngine,
    ScenarioAnalysisEngine,
    RecommendationEngine,
    IntegrationManager,
    RetirementPlanSerializer
)
```

### Basic Usage

```python
# 1. Create a retirement plan
plan = RetirementPlan(
    plan_id='plan_001',
    user_id=123,
    plan_name='My Retirement Plan',
    current_age=30,
    retirement_age=60,
    current_salary=1000000,
    current_monthly_expenses=50000,
    current_savings=500000
)

# 2. Calculate retirement corpus
corpus, monthly_expenses = RetirementCalculationEngine.calculate_retirement_corpus(
    current_age=30,
    retirement_age=60,
    current_monthly_expenses=50000,
    inflation_rate=0.06,
    life_expectancy=85
)
print(f"Retirement corpus needed: ₹{corpus:,.0f}")

# 3. Calculate required monthly savings
monthly_savings = RetirementCalculationEngine.calculate_required_monthly_savings(
    current_savings=500000,
    corpus_target=corpus,
    current_age=30,
    retirement_age=60,
    return_rate=0.10
)
print(f"Monthly savings needed: ₹{monthly_savings:,.0f}")

# 4. Calculate retirement readiness
assessment = RetirementReadinessScoringEngine.calculate_full_assessment(
    current_age=30,
    retirement_age=60,
    current_savings=500000,
    corpus_target=corpus,
    required_monthly_savings=monthly_savings,
    current_monthly_income=1000000/12,
    total_loan_amount=0,
    annual_salary=1000000,
    financial_health_score=75
)
print(f"Readiness score: {assessment.readiness_score}/100")
print(f"Classification: {assessment.classification}")

# 5. Create scenarios
scenario = ScenarioAnalysisEngine.create_scenario(
    plan_id='plan_001',
    scenario_name='Aggressive Growth',
    retirement_age=55,
    monthly_savings=monthly_savings * 1.2,
    investment_return_rate=0.12,
    inflation_rate=0.06,
    current_age=30
)

# 6. Generate recommendations
recommendations = RecommendationEngine.generate_action_plan(
    readiness_score=assessment.readiness_score,
    financial_health_factor=assessment.financial_health_factor,
    savings_adequacy_factor=assessment.savings_adequacy_factor,
    savings_rate_factor=assessment.savings_rate_factor,
    debt_burden_factor=assessment.debt_burden_factor,
    time_horizon_factor=assessment.time_horizon_factor,
    current_age=30,
    retirement_age=60,
    required_monthly_savings=monthly_savings,
    current_monthly_income=1000000/12,
    total_loan_amount=0,
    annual_salary=1000000,
    gap=0,
    corpus_target=corpus
)
for rec in recommendations:
    print(f"- {rec['description']} (Impact: +{rec['estimated_impact_on_score']} points)")

# 7. Serialize plan
json_str = RetirementPlanSerializer.serialize_plan(plan)
print(json_str)

# 8. Deserialize plan
restored_plan = RetirementPlanSerializer.deserialize_plan(json_str)
```

## Components

### 1. Calculation Engine
Handles all mathematical calculations:
- Retirement corpus with inflation adjustment
- Required monthly savings using Future Value of Annuity
- Projected savings with compound interest
- Gap analysis

### 2. Readiness Scoring Engine
Calculates retirement readiness (0-100) based on 5 factors:
- Financial Health (30%) - ML model score
- Savings Adequacy (25%) - Current savings vs target
- Savings Rate (20%) - Achievability
- Debt Burden (15%) - Loan obligations
- Time Horizon (10%) - Years until retirement

### 3. Scenario Analysis Engine
Supports what-if modeling:
- Create and save up to 5 scenarios
- Real-time recalculation
- Side-by-side comparison
- Preset scenarios (Conservative/Moderate/Aggressive)

### 4. Recommendation Engine
Generates personalized action plans:
- 3-5 prioritized recommendations
- Impact estimation on readiness score
- Loan payoff strategies (Snowball/Avalanche/Balanced)
- Expense reduction suggestions
- Investment strategy recommendations

### 5. Integration Manager
Integrates with existing systems:
- Financial Health Scorer (ML model)
- Loan History System
- Goals Manager
- Profile Service

### 6. Parser & Serializer
Handles data persistence:
- JSON serialization/deserialization
- Validation with error messages
- Round-trip consistency
- Export/import functionality

## Configuration

Default values in `constants.py`:
- Inflation Rate: 6%
- Investment Return Rate: 10%
- Life Expectancy: 85 years
- Max Scenarios: 5
- Savings Threshold: 50% of income

## Error Handling

Custom exceptions for specific errors:
- `InvalidInputError` - Input validation failures
- `ConflictingInputError` - Conflicting parameters
- `UnrealisticValueError` - Unrealistic calculations
- `SerializationError` - JSON issues
- `IntegrationError` - External system failures
- `ScenarioLimitExceededError` - Too many scenarios
- `DuplicateScenarioNameError` - Duplicate names

## Validation

All inputs are validated:
- Age ranges (18-75)
- Positive financial values
- Inflation rates (0-15%)
- Return rates (0-30%)
- Conflicting parameters

## Testing

Ready for:
- Unit tests (calculation accuracy)
- Property-based tests (universal properties)
- Integration tests (system interactions)
- Validation tests (input/output)

## API Integration

Ready for Flask API endpoints:
- POST /api/retirement/calculate
- POST /api/retirement/plans
- GET /api/retirement/plans/{user_id}
- PUT /api/retirement/plans/{plan_id}
- POST /api/retirement/scenarios
- GET /api/retirement/readiness

## Performance

- Calculations: O(1) complexity
- Scenario comparison: O(n) where n ≤ 5
- Serialization: O(n) where n = plan size
- Integration calls: Async-ready

## Security

- Input validation on all parameters
- Type checking for all fields
- Error messages don't expose sensitive data
- Logging for audit trail

## Future Enhancements

- [ ] Async API endpoints
- [ ] Caching for expensive calculations
- [ ] Advanced visualization support
- [ ] PDF export functionality
- [ ] Email notifications
- [ ] Mobile app support

## Support

For issues or questions, refer to:
- `docs/development/retirement_planning_calculator/IMPLEMENTATION_PHASE1.md`
- `.kiro/specs/retirement-planning-calculator/requirements.md`
- `.kiro/specs/retirement-planning-calculator/design.md`

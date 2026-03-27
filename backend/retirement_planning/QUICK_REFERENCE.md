# Retirement Planning Calculator - Quick Reference

## Module Structure

```python
from backend.retirement_planning import (
    # Models
    RetirementPlan,
    RetirementScenario,
    RetirementReadinessAssessment,
    GapAnalysis,
    ActionPlanItem,
    
    # Engines
    RetirementCalculationEngine,
    RetirementReadinessScoringEngine,
    ScenarioAnalysisEngine,
    RecommendationEngine,
    IntegrationManager,
    RetirementPlanSerializer,
    
    # Exceptions
    InvalidInputError,
    ConflictingInputError,
    UnrealisticValueError,
    SerializationError,
    IntegrationError,
    
    # Constants
    DEFAULT_INFLATION_RATE,
    DEFAULT_INVESTMENT_RETURN_RATE,
    DEFAULT_LIFE_EXPECTANCY,
    READINESS_SCORE_WEIGHTS
)
```

## Common Operations

### 1. Calculate Retirement Corpus
```python
corpus, monthly_expenses = RetirementCalculationEngine.calculate_retirement_corpus(
    current_age=30,
    retirement_age=60,
    current_monthly_expenses=50000,
    inflation_rate=0.06,
    life_expectancy=85
)
```

### 2. Calculate Required Savings
```python
monthly_savings = RetirementCalculationEngine.calculate_required_monthly_savings(
    current_savings=500000,
    corpus_target=corpus,
    current_age=30,
    retirement_age=60,
    return_rate=0.10
)
```

### 3. Calculate Readiness Score
```python
assessment = RetirementReadinessScoringEngine.calculate_full_assessment(
    current_age=30,
    retirement_age=60,
    current_savings=500000,
    corpus_target=corpus,
    required_monthly_savings=monthly_savings,
    current_monthly_income=83333,
    total_loan_amount=0,
    annual_salary=1000000,
    financial_health_score=75
)
```

### 4. Create Scenario
```python
scenario = ScenarioAnalysisEngine.create_scenario(
    plan_id='plan_001',
    scenario_name='Aggressive Growth',
    retirement_age=55,
    monthly_savings=50000,
    investment_return_rate=0.12,
    inflation_rate=0.06,
    current_age=30
)
```

### 5. Generate Recommendations
```python
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
    current_monthly_income=83333,
    total_loan_amount=0,
    annual_salary=1000000,
    gap=0,
    corpus_target=corpus
)
```

### 6. Serialize Plan
```python
json_str = RetirementPlanSerializer.serialize_plan(plan)
```

### 7. Deserialize Plan
```python
plan = RetirementPlanSerializer.deserialize_plan(json_str)
```

## Readiness Score Interpretation

| Score | Classification | Color | Meaning |
|-------|-----------------|-------|---------|
| 80-100 | Excellent | Green | On track for retirement |
| 60-79 | Good | Blue | Generally prepared |
| 40-59 | Fair | Amber | Needs improvement |
| 20-39 | Poor | Red | Significant gaps |
| 0-19 | Critical | Dark Red | Urgent action needed |

## Scoring Factors

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Financial Health | 30% | ML model score (0-100) |
| Savings Adequacy | 25% | (current_savings / corpus_target) × 100 |
| Savings Rate | 20% | 100 if achievable, 50 if marginal, 20 if not |
| Debt Burden | 15% | 100 - (debt / salary × 100) |
| Time Horizon | 10% | 100 if >15 yrs, 80 if 10-15, 60 if 5-10, 40 if <5 |

## Preset Scenarios

| Scenario | Return Rate | Retirement Age | Risk Level |
|----------|-------------|-----------------|------------|
| Conservative | 8% | 65 | Low |
| Moderate | 10% | 60 | Medium |
| Aggressive | 12% | 55 | High |

## Loan Payoff Strategies

| Strategy | Approach | Best For |
|----------|----------|----------|
| Snowball | Smallest to largest | Psychological wins |
| Avalanche | Highest interest first | Financial optimization |
| Balanced | Mix of both | Balanced approach |

## Error Handling

```python
try:
    corpus = RetirementCalculationEngine.calculate_retirement_corpus(...)
except InvalidInputError as e:
    print(f"Invalid input: {e.message}")
    print(f"Error code: {e.error_code}")
except UnrealisticValueError as e:
    print(f"Unrealistic value: {e.message}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

## Validation

```python
# Validate all inputs
is_valid, error_msg = RetirementCalculationEngine.validate_inputs(
    current_age=30,
    retirement_age=60,
    current_salary=1000000,
    current_monthly_expenses=50000,
    current_savings=500000,
    inflation_rate=0.06,
    investment_return_rate=0.10,
    life_expectancy=85
)

if not is_valid:
    print(f"Validation error: {error_msg}")
```

## Integration

```python
# Get financial health score
score = IntegrationManager.get_financial_health_score(user_id=123)

# Get user loans
loans = IntegrationManager.get_user_loans(user_id=123)

# Get financial goals
goals = IntegrationManager.get_financial_goals(user_id=123)

# Create retirement goal
goal_id = IntegrationManager.create_retirement_goal(
    user_id=123,
    corpus_target=corpus,
    retirement_age=60
)

# Check integration health
health = IntegrationManager.validate_integration_health()
```

## Constants

```python
# Default values
DEFAULT_INFLATION_RATE = 0.06              # 6%
DEFAULT_INVESTMENT_RETURN_RATE = 0.10      # 10%
DEFAULT_LIFE_EXPECTANCY = 85               # years

# Constraints
MIN_CURRENT_AGE = 18
MAX_RETIREMENT_AGE = 75
SAVINGS_ACHIEVABILITY_THRESHOLD = 0.50     # 50% of income

# Limits
MAX_SCENARIOS_PER_PLAN = 5
MIN_RECOMMENDATIONS = 3
MAX_RECOMMENDATIONS = 5

# Weights
READINESS_SCORE_WEIGHTS = {
    'financial_health': 0.30,
    'savings_adequacy': 0.25,
    'savings_rate': 0.20,
    'debt_burden': 0.15,
    'time_horizon': 0.10
}
```

## Data Models

### RetirementPlan
```python
plan = RetirementPlan(
    plan_id='plan_001',
    user_id=123,
    plan_name='My Retirement Plan',
    current_age=30,
    retirement_age=60,
    current_salary=1000000,
    current_monthly_expenses=50000,
    current_savings=500000,
    inflation_rate=0.06,
    investment_return_rate=0.10,
    life_expectancy=85
)
```

### RetirementScenario
```python
scenario = RetirementScenario(
    scenario_id='scenario_001',
    plan_id='plan_001',
    scenario_name='Aggressive Growth',
    retirement_age=55,
    monthly_savings=50000,
    investment_return_rate=0.12,
    inflation_rate=0.06
)
```

## Testing

```python
# Unit test example
def test_corpus_calculation():
    corpus, expenses = RetirementCalculationEngine.calculate_retirement_corpus(
        current_age=30,
        retirement_age=60,
        current_monthly_expenses=50000,
        inflation_rate=0.06,
        life_expectancy=85
    )
    assert corpus > 0
    assert expenses > 50000  # Should be inflated

# Property test example
from hypothesis import given, strategies as st

@given(
    current_age=st.integers(min_value=18, max_value=60),
    retirement_age=st.integers(min_value=40, max_value=75),
    monthly_expenses=st.floats(min_value=1000, max_value=1000000)
)
def test_corpus_always_positive(current_age, retirement_age, monthly_expenses):
    if retirement_age > current_age:
        corpus, _ = RetirementCalculationEngine.calculate_retirement_corpus(
            current_age=current_age,
            retirement_age=retirement_age,
            current_monthly_expenses=monthly_expenses
        )
        assert corpus >= 0
```

## Performance Tips

1. **Cache calculations** - Store results for repeated queries
2. **Batch operations** - Process multiple plans together
3. **Lazy loading** - Load integration data only when needed
4. **Async integration** - Use async calls for external systems
5. **Optimize serialization** - Use streaming for large datasets

## Debugging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('retirement_planning')

# Check integration health
health = IntegrationManager.validate_integration_health()
print(health)

# Validate round-trip serialization
is_consistent = RetirementPlanSerializer.validate_round_trip(plan)
print(f"Round-trip consistent: {is_consistent}")
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Unrealistic corpus value | Check inflation rate and life expectancy |
| Savings not achievable | Increase income or reduce corpus target |
| Low readiness score | Focus on debt reduction and savings increase |
| Serialization error | Validate JSON structure and field types |
| Integration error | Check system health and error logs |

## Resources

- **Documentation:** `backend/retirement_planning/README.md`
- **Implementation:** `docs/development/retirement_planning_calculator/IMPLEMENTATION_PHASE1.md`
- **Specification:** `.kiro/specs/retirement-planning-calculator/`
- **Examples:** See "Common Operations" section above

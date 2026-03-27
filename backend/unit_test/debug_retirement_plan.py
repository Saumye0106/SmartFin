#!/usr/bin/env python3
"""
Debug script for retirement planning functionality.
Tests with different input values to detect anomalies like:
- Same output for different inputs
- Unrealistic outputs
- Logical inconsistencies
"""

import os
import sys
from pathlib import Path

# Setup path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from retirement_planning.calculation_engine import RetirementCalculationEngine
from retirement_planning.readiness_scoring_engine import RetirementReadinessScoringEngine
from retirement_planning.recommendation_engine import RecommendationEngine


def format_currency(value):
    """Format value as Indian Rupees"""
    return f"₹{value:,.2f}"


def test_scenario(name, params):
    """Test a single retirement planning scenario"""
    print(f"\n{'='*80}")
    print(f"SCENARIO: {name}")
    print(f"{'='*80}")
    
    # Input parameters
    current_age = params.get('current_age', 30)
    retirement_age = params.get('retirement_age', 60)
    current_salary = params.get('current_salary', 600000)  # Annual
    current_monthly_expenses = params.get('current_monthly_expenses', 50000)
    current_savings = params.get('current_savings', 500000)
    inflation_rate = params.get('inflation_rate', 0.06)
    investment_return_rate = params.get('investment_return_rate', 0.10)
    life_expectancy = params.get('life_expectancy', 85)
    total_loan_amount = params.get('total_loan_amount', 0)
    
    print(f"\nInput Parameters:")
    print(f"  Current Age: {current_age}")
    print(f"  Retirement Age: {retirement_age}")
    print(f"  Annual Salary: {format_currency(current_salary)}")
    print(f"  Monthly Expenses: {format_currency(current_monthly_expenses)}")
    print(f"  Current Savings: {format_currency(current_savings)}")
    print(f"  Inflation Rate: {inflation_rate*100}%")
    print(f"  Investment Return: {investment_return_rate*100}%")
    print(f"  Life Expectancy: {life_expectancy}")
    print(f"  Total Loan Amount: {format_currency(total_loan_amount)}")
    
    try:
        # 1. Calculate corpus
        engine = RetirementCalculationEngine()
        corpus, monthly_at_retirement = engine.calculate_retirement_corpus(
            current_age=current_age,
            retirement_age=retirement_age,
            current_monthly_expenses=current_monthly_expenses,
            inflation_rate=inflation_rate,
            life_expectancy=life_expectancy
        )
        
        print(f"\nCorpus Calculation:")
        print(f"  Monthly Expenses at Retirement: {format_currency(monthly_at_retirement)}")
        print(f"  Retirement Corpus Needed: {format_currency(corpus)}")
        
        # 2. Calculate required monthly savings
        monthly_savings = engine.calculate_required_monthly_savings(
            current_savings=current_savings,
            corpus_target=corpus,
            current_age=current_age,
            retirement_age=retirement_age,
            return_rate=investment_return_rate
        )
        
        print(f"\nSavings Requirement:")
        print(f"  Required Monthly Savings: {format_currency(monthly_savings)}")
        print(f"  Required Annual Savings: {format_currency(monthly_savings * 12)}")
        
        # 3. Calculate readiness score
        scoring = RetirementReadinessScoringEngine()
        
        # Financial health score (assume average)
        financial_health_score = 60
        savings_adequacy = scoring.calculate_savings_adequacy_factor(current_savings, corpus)
        savings_rate_factor = scoring.calculate_savings_rate_factor(
            monthly_savings, current_salary / 12
        )
        debt_burden = scoring.calculate_debt_burden_factor(total_loan_amount, current_salary)
        time_horizon = scoring.calculate_time_horizon_factor(current_age, retirement_age)
        
        print(f"\nReadiness Score Components:")
        print(f"  Financial Health Score: {financial_health_score}/100")
        print(f"  Savings Adequacy: {savings_adequacy:.2f}/100")
        print(f"  Savings Rate Factor: {savings_rate_factor:.2f}/100")
        print(f"  Debt Burden Factor: {debt_burden:.2f}/100")
        print(f"  Time Horizon Factor: {time_horizon:.2f}/100")
        
        # 4. Full assessment
        assessment = scoring.calculate_full_assessment(
            current_age=current_age,
            retirement_age=retirement_age,
            current_savings=current_savings,
            corpus_target=corpus,
            required_monthly_savings=monthly_savings,
            current_monthly_income=current_salary / 12,
            total_loan_amount=total_loan_amount,
            annual_salary=current_salary,
            financial_health_score=financial_health_score
        )
        
        print(f"\nFull Assessment:")
        print(f"  Readiness Score: {assessment.readiness_score}")
        print(f"  Classification: {assessment.classification}")
        
        # 5. Recommendations
        reco_engine = RecommendationEngine()
        recommendations_list = reco_engine.generate_action_plan(
            readiness_score=assessment.readiness_score,
            financial_health_factor=assessment.financial_health_factor,
            savings_adequacy_factor=assessment.factors_breakdown['savings_adequacy']['value'],
            savings_rate_factor=assessment.factors_breakdown['savings_rate']['value'],
            debt_burden_factor=assessment.factors_breakdown['debt_burden']['value'],
            time_horizon_factor=assessment.factors_breakdown['time_horizon']['value'],
            current_age=current_age,
            retirement_age=retirement_age,
            required_monthly_savings=monthly_savings,
            current_monthly_income=current_salary / 12,
            total_loan_amount=total_loan_amount,
            annual_salary=current_salary,
            gap=corpus - current_savings,
            corpus_target=corpus
        )
        
        print(f"\nRecommendations:")
        for i, rec in enumerate(recommendations_list[:3], 1):
            desc = rec.get('description', 'N/A')
            print(f"  {i}. {desc}")
        
        return {
            'corpus': corpus,
            'monthly_savings': monthly_savings,
            'readiness_score': assessment.readiness_score,
            'monthly_at_retirement': monthly_at_retirement
        }
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("\n" + "="*80)
    print("RETIREMENT PLANNING DEBUG TEST")
    print("Testing multiple scenarios for anomalies")
    print("="*80)
    
    # Test scenarios
    scenarios = {
        "Baseline (30yr, ₹600k salary, ₹50k expenses)": {
            'current_age': 30,
            'retirement_age': 60,
            'current_salary': 600000,
            'current_monthly_expenses': 50000,
            'current_savings': 500000,
        },
        "Conservative (35yr, low savings)": {
            'current_age': 35,
            'retirement_age': 60,
            'current_salary': 500000,
            'current_monthly_expenses': 60000,
            'current_savings': 100000,
        },
        "Aggressive (25yr, high salary)": {
            'current_age': 25,
            'retirement_age': 60,
            'current_salary': 1000000,
            'current_monthly_expenses': 40000,
            'current_savings': 1000000,
        },
        "High expenses (50yr, limited time)": {
            'current_age': 50,
            'retirement_age': 60,
            'current_salary': 600000,
            'current_monthly_expenses': 80000,
            'current_savings': 200000,
        },
        "Early retirement (35yr, retire at 50)": {
            'current_age': 35,
            'retirement_age': 50,
            'current_salary': 800000,
            'current_monthly_expenses': 60000,
            'current_savings': 1000000,
        },
        "Very late retirement (55yr, retire at 70)": {
            'current_age': 55,
            'retirement_age': 70,
            'current_salary': 600000,
            'current_monthly_expenses': 50000,
            'current_savings': 2000000,
        },
        "High inflation scenario": {
            'current_age': 30,
            'retirement_age': 60,
            'current_salary': 600000,
            'current_monthly_expenses': 50000,
            'current_savings': 500000,
            'inflation_rate': 0.10,
        },
        "Low returns scenario": {
            'current_age': 30,
            'retirement_age': 60,
            'current_salary': 600000,
            'current_monthly_expenses': 50000,
            'current_savings': 500000,
            'investment_return_rate': 0.05,
        },
    }
    
    results = {}
    for scenario_name, params in scenarios.items():
        result = test_scenario(scenario_name, params)
        if result:
            results[scenario_name] = result
    
    # Analysis and anomaly detection
    print(f"\n\n{'='*80}")
    print("ANOMALY DETECTION & ANALYSIS")
    print(f"{'='*80}")
    
    print(f"\nComparison of Results:")
    print(f"{'Scenario':<50} {'Corpus':<20} {'Monthly Savings':<20}")
    print("-" * 90)
    
    for scenario_name, result in results.items():
        if result:
            corpus_str = format_currency(result['corpus'])
            savings_str = format_currency(result['monthly_savings'])
            short_name = scenario_name[:47] + "..." if len(scenario_name) > 50 else scenario_name
            print(f"{short_name:<50} {corpus_str:<20} {savings_str:<20}")
    
    # Check for identical outputs
    print(f"\n\nChecking for Identical Outputs:")
    print("-" * 90)
    
    corpus_values = [r['corpus'] for r in results.values() if r]
    savings_values = [r['monthly_savings'] for r in results.values() if r]
    
    if len(set(corpus_values)) == len(corpus_values):
        print("✅ All corpus values are unique (no duplicates detected)")
    else:
        print("⚠️  WARNING: Identical corpus values found!")
        from collections import Counter
        duplicates = [val for val, cnt in Counter(corpus_values).items() if cnt > 1]
        for dup in duplicates:
            print(f"   Corpus {format_currency(dup)} appears multiple times")
    
    if len(set(savings_values)) == len(savings_values):
        print("✅ All monthly savings values are unique (no duplicates detected)")
    else:
        print("⚠️  WARNING: Identical savings values found!")
        from collections import Counter
        duplicates = [val for val, cnt in Counter(savings_values).items() if cnt > 1]
        for dup in duplicates:
            print(f"   Monthly Savings {format_currency(dup)} appears multiple times")
    
    # Sanity checks
    print(f"\n\nSanity Checks:")
    print("-" * 90)
    
    for scenario_name, result in results.items():
        if not result:
            continue
        
        corpus = result['corpus']
        monthly_savings = result['monthly_savings']
        monthly_at_retirement = result['monthly_at_retirement']
        
        # Check 1: Corpus should be positive
        if corpus <= 0:
            print(f"❌ {scenario_name}: Corpus is {corpus} (should be positive)")
        
        # Check 2: Monthly savings should be positive
        if monthly_savings < 0:
            print(f"❌ {scenario_name}: Monthly savings is {monthly_savings} (should be >= 0)")
        
        # Check 3: Corpus should generally be >> monthly expenses at retirement
        if monthly_at_retirement * 12 > corpus:
            print(f"⚠️  {scenario_name}: Annual expenses at retirement exceed corpus")
        
        # Check 4: Corpus should scale with retirement expenses
        if monthly_at_retirement > 0:
            expense_to_corpus_ratio = (monthly_at_retirement * 12) / corpus
            if expense_to_corpus_ratio > 0.5:
                print(f"⚠️  {scenario_name}: Annual expenses are {expense_to_corpus_ratio*100:.1f}% of corpus (unusually high)")
    
    print(f"\n{'='*80}")
    print("DEBUG TEST COMPLETE")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

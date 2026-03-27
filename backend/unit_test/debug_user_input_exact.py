#!/usr/bin/env python3
"""
Test with user's exact inputs from the UI screenshot
Testing: Same inputs but different "Desired Retirement Lifestyle"
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


def display_results(scenario_name, params):
    """Display results for a scenario"""
    print(f"\n{'='*100}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*100}")
    
    current_age = params['current_age']
    retirement_age = params['retirement_age']
    annual_salary = params['annual_salary']
    monthly_expenses = params['monthly_expenses']
    current_savings = params['current_savings']
    desired_retirement_lifestyle = params['desired_retirement_lifestyle']
    inflation_rate = params['inflation_rate']
    return_rate = params['return_rate']
    life_expectancy = params['life_expectancy']
    
    print(f"\nInput Parameters:")
    print(f"  Current Age: {current_age}")
    print(f"  Retirement Age: {retirement_age}")
    print(f"  Annual Salary: ₹{annual_salary:,}")
    print(f"  Monthly Expenses: ₹{monthly_expenses:,}")
    print(f"  Current Savings: ₹{current_savings:,}")
    print(f"  Desired Retirement Lifestyle: ₹{desired_retirement_lifestyle:,}/month")
    print(f"  Inflation Rate: {inflation_rate*100}%")
    print(f"  Return Rate: {return_rate*100}%")
    print(f"  Life Expectancy: {life_expectancy}")
    
    try:
        engine = RetirementCalculationEngine()
        
        # Calculate corpus based on desired retirement lifestyle
        # This is the anticipated monthly expense at retirement
        years_to_retirement = retirement_age - current_age
        years_in_retirement = life_expectancy - retirement_age
        
        # The desired lifestyle is what they want to spend monthly in retirement (in today's rupees)
        # We need to account for inflation
        monthly_at_retirement = desired_retirement_lifestyle * ((1 + inflation_rate) ** years_to_retirement)
        
        # Calculate corpus needed for this lifestyle
        annual_at_retirement = monthly_at_retirement * 12
        post_retirement_return = 0.07
        real_rate = ((1 + post_retirement_return) / (1 + inflation_rate)) - 1
        
        if abs(real_rate) < 0.0001:
            corpus = annual_at_retirement * years_in_retirement
        elif real_rate > 0:
            corpus = annual_at_retirement * (
                (1 - (1 + real_rate) ** (-years_in_retirement)) / real_rate
            )
        else:
            corpus = annual_at_retirement * years_in_retirement
        
        corpus = round(corpus, 2)
        monthly_at_retirement = round(monthly_at_retirement, 2)
        
        print(f"\nCalculations:")
        print(f"  Monthly Expense at Retirement (with inflation): ₹{monthly_at_retirement:,.2f}")
        print(f"  Annual at Retirement: ₹{annual_at_retirement:,.2f}")
        print(f"  Retirement Corpus Needed: ₹{corpus:,.2f}")
        
        # Calculate required monthly savings
        monthly_savings = engine.calculate_required_monthly_savings(
            current_savings=current_savings,
            corpus_target=corpus,
            current_age=current_age,
            retirement_age=retirement_age,
            return_rate=return_rate
        )
        
        print(f"\nSavings Requirement:")
        print(f"  Required Monthly Savings: ₹{monthly_savings:,.2f}")
        print(f"  Required Annual Savings: ₹{monthly_savings * 12:,.2f}")
        
        # Calculate readiness
        scoring = RetirementReadinessScoringEngine()
        financial_health_score = 60  # Assume average
        
        assessment = scoring.calculate_full_assessment(
            current_age=current_age,
            retirement_age=retirement_age,
            current_savings=current_savings,
            corpus_target=corpus,
            required_monthly_savings=monthly_savings,
            current_monthly_income=annual_salary / 12,
            total_loan_amount=0,
            annual_salary=annual_salary,
            financial_health_score=financial_health_score
        )
        
        print(f"\nReadiness Score:")
        print(f"  Readiness Score: {assessment.readiness_score}/100")
        print(f"  Classification: {assessment.classification}")
        
        return {
            'corpus': corpus,
            'monthly_savings': monthly_savings,
            'monthly_at_retirement': monthly_at_retirement,
            'readiness_score': assessment.readiness_score
        }
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("\n" + "="*100)
    print("USER'S EXACT INPUT TEST: Different Desired Retirement Lifestyle")
    print("="*100)
    
    # Base parameters from the screenshot
    base_params = {
        'current_age': 30,
        'retirement_age': 60,
        'annual_salary': 960000,
        'monthly_expenses': 69000,
        'current_savings': 23333,
        'inflation_rate': 0.06,
        'return_rate': 0.10,
        'life_expectancy': 85,
    }
    
    # Test 1: Desired Retirement Lifestyle = 200000
    params1 = {**base_params, 'desired_retirement_lifestyle': 200000}
    result1 = display_results("Desired Lifestyle ₹200,000/month", params1)
    
    # Test 2: Desired Retirement Lifestyle = 300000
    params2 = {**base_params, 'desired_retirement_lifestyle': 300000}
    result2 = display_results("Desired Lifestyle ₹300,000/month", params2)
    
    # Comparison
    print(f"\n\n" + "="*100)
    print("COMPARISON")
    print("="*100)
    
    if result1 and result2:
        print(f"\n{'Metric':<40} {'₹200k Lifestyle':<25} {'₹300k Lifestyle':<25}")
        print("-"*90)
        
        corpus_ratio = result2['corpus'] / result1['corpus']
        print(f"{'Corpus Needed':<40} ₹{result1['corpus']:>23,.0f} ₹{result2['corpus']:>23,.0f}")
        print(f"  (Ratio: {corpus_ratio:.2f}x)")
        
        savings_ratio = result2['monthly_savings'] / result1['monthly_savings'] if result1['monthly_savings'] > 0 else 0
        print(f"\n{'Monthly Savings Needed':<40} ₹{result1['monthly_savings']:>23,.2f} ₹{result2['monthly_savings']:>23,.2f}")
        print(f"  (Ratio: {savings_ratio:.2f}x)")
        
        print(f"\n{'Readiness Score':<40} {result1['readiness_score']:>23.2f} {result2['readiness_score']:>23.2f}")
        
        # Anomaly check
        print(f"\n" + "="*100)
        print("ANOMALY CHECK")
        print("="*100)
        
        if result1['corpus'] == result2['corpus']:
            print(f"\n⚠️  ANOMALY FOUND!")
            print(f"  Corpus values are IDENTICAL despite different desired lifestyle:")
            print(f"    ₹200k → ₹{result1['corpus']:,.0f}")
            print(f"    ₹300k → ₹{result2['corpus']:,.0f}")
        elif abs(result1['monthly_savings'] - result2['monthly_savings']) < 0.01:
            print(f"\n⚠️  ANOMALY FOUND!")
            print(f"  Monthly savings are IDENTICAL despite different desired lifestyle:")
            print(f"    ₹200k → ₹{result1['monthly_savings']:,.2f}")
            print(f"    ₹300k → ₹{result2['monthly_savings']:,.2f}")
        else:
            print(f"\n✅ No anomalies detected")
            print(f"   Both corpus and monthly savings change appropriately with desired lifestyle")
            print(f"   Expected: 50% increase in desired lifestyle → ~{savings_ratio:.1f}x increase in corpus/savings")
    
    print(f"\n{'='*100}\n")


if __name__ == '__main__':
    main()

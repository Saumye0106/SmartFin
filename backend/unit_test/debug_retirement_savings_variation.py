#!/usr/bin/env python3
"""
Test retirement planning with SAME parameters but DIFFERENT current savings.
This will verify if output changes appropriately with different starting amounts.
"""

import os
import sys
from pathlib import Path

# Setup path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from retirement_planning.calculation_engine import RetirementCalculationEngine


def test_same_params_different_savings():
    """Test with identical parameters but varying current_savings"""
    engine = RetirementCalculationEngine()
    
    # Fixed parameters (all same)
    current_age = 30
    retirement_age = 60
    monthly_expenses = 50000
    inflation_rate = 0.06
    return_rate = 0.10
    life_expectancy = 85
    
    print("\n" + "="*100)
    print("TEST: Same Parameters, Different Current Savings")
    print("="*100)
    print(f"\nFixed Parameters:")
    print(f"  Current Age: {current_age}")
    print(f"  Retirement Age: {retirement_age}")
    print(f"  Monthly Expenses: ₹{monthly_expenses:,}")
    print(f"  Inflation Rate: {inflation_rate*100}%")
    print(f"  Return Rate: {return_rate*100}%")
    print(f"  Life Expectancy: {life_expectancy}")
    
    # Calculate corpus once (should be same for all since it doesn't depend on savings)
    corpus, monthly_at_ret = engine.calculate_retirement_corpus(
        current_age=current_age,
        retirement_age=retirement_age,
        current_monthly_expenses=monthly_expenses,
        inflation_rate=inflation_rate,
        life_expectancy=life_expectancy
    )
    
    print(f"\nCorpus Calculation (same for all since independent of current savings):")
    print(f"  Monthly Expenses at Retirement: ₹{monthly_at_ret:,.2f}")
    print(f"  Retirement Corpus Needed: ₹{corpus:,.2f}")
    
    # Test with different current_savings values
    savings_amounts = [
        100000,     # Low savings
        500000,     # Medium savings
        1000000,    # High savings
        2000000,    # Very high savings
    ]
    
    print(f"\n" + "-"*100)
    print(f"{'Current Savings':<20} {'Required Monthly Savings':<30} {'Outcome':<50}")
    print("-"*100)
    
    results = {}
    for savings in savings_amounts:
        monthly_savings = engine.calculate_required_monthly_savings(
            current_savings=savings,
            corpus_target=corpus,
            current_age=current_age,
            retirement_age=retirement_age,
            return_rate=return_rate
        )
        
        results[savings] = monthly_savings
        
        savings_str = f"₹{savings:,}"
        monthly_str = f"₹{monthly_savings:,.2f}"
        
        # Determine outcome
        if savings < 500000:
            outcome = "Need to save more monthly"
        elif savings > 1500000:
            outcome = "Minimal monthly savings needed"
        else:
            outcome = "Moderate monthly savings needed"
        
        print(f"{savings_str:<20} {monthly_str:<30} {outcome:<50}")
    
    # Check for anomalies
    print(f"\n" + "="*100)
    print("ANOMALY CHECK")
    print("="*100)
    
    # 1. Check if output changes with different inputs
    unique_outputs = len(set(results.values()))
    total_inputs = len(results)
    
    print(f"\n✓ Unique Outputs: {unique_outputs} out of {total_inputs} test cases")
    
    if unique_outputs == total_inputs:
        print("  ✅ All outputs are unique (expected behavior)")
    else:
        print("  ⚠️  ANOMALY: Some outputs are identical for different inputs!")
        from collections import Counter
        duplicates = Counter(results.values())
        for value, count in duplicates.items():
            if count > 1:
                matching_savings = [s for s, v in results.items() if v == value]
                print(f"     Monthly savings ₹{value:,.2f} for: {[f'₹{s/1e6:.1f}M' for s in matching_savings]}")
    
    # 2. Verify relationship: more savings = less monthly savings needed
    print(f"\n✓ Savings Relationship Check:")
    sorted_results = sorted(results.items())
    is_decreasing = all(
        sorted_results[i][1] >= sorted_results[i+1][1] 
        for i in range(len(sorted_results)-1)
    )
    
    if is_decreasing:
        print("  ✅ Correct: More current savings = Less monthly savings needed")
    else:
        print("  ⚠️  ANOMALY: Monthly savings doesn't decrease with more current savings!")
        for i in range(len(sorted_results)-1):
            s1, m1 = sorted_results[i]
            s2, m2 = sorted_results[i+1]
            if m1 < m2:
                print(f"     ₹{s1:,} → monthly ₹{m1:,.2f}")
                print(f"     ₹{s2:,} → monthly ₹{m2:,.2f} (should be less!)")
    
    # 3. Calculate the rate of change
    print(f"\n✓ Rate of Change Analysis:")
    for i in range(len(sorted_results)-1):
        s1, m1 = sorted_results[i]
        s2, m2 = sorted_results[i+1]
        savings_diff = s2 - s1
        monthly_diff = m1 - m2
        
        if savings_diff > 0:
            rate = monthly_diff / savings_diff
            print(f"  ₹{s1:,} → ₹{s2:,}: Saving ₹{savings_diff:,} reduces monthly need by ₹{monthly_diff:,.2f}")
            print(f"    Rate: ₹{rate:.4f} per rupee saved")
    
    print(f"\n" + "="*100)


if __name__ == '__main__':
    test_same_params_different_savings()

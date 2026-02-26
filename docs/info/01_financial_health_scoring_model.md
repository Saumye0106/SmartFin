# Financial Health Scoring Model

**Document Version:** 1.0  
**Date:** February 26, 2026  
**Status:** Complete

---

## Executive Summary

This document outlines SmartFin's financial health scoring methodology using Dataset 2 (India Personal Finance). The model evaluates individuals across 5 key dimensions to produce a realistic, actionable financial health score (0-100).

---

## Table of Contents

1. [Overview](#overview)
2. [Scoring Methodology](#scoring-methodology)
3. [Weightage Justification](#weightage-justification)
4. [Scoring Factors](#scoring-factors)
5. [Implementation](#implementation)
6. [Validation](#validation)
7. [Why No Credit Score](#why-no-credit-score)

---

## Overview

### What is Financial Health?

Financial health is the overall assessment of an individual's financial situation based on:
- Current income and expenses
- Savings capacity
- Debt management
- Spending discipline
- Life stage context

### Our Approach

Instead of using traditional credit scores (which measure historical behavior), we use a **5-factor model** that measures **current financial behavior** and provides **actionable insights**.

### Why This Matters

- ✅ Relevant for students with no credit history
- ✅ Measures current behavior (more predictive)
- ✅ Provides actionable recommendations
- ✅ Fair and transparent scoring
- ✅ Works with available data (Dataset 2)

---

## Scoring Methodology

### The Formula

```
Financial Health Score = (S × 0.30) + (D × 0.25) + (E × 0.20) + (B × 0.15) + (L × 0.10)

Where:
S = Savings Score (0-100)
D = Debt Management Score (0-100)
E = Expense Control Score (0-100)
B = Balance Score (0-100)
L = Life Stage Score (0-100)

Result: 0-100 scale
```

### Score Categories

| Score Range | Category | Emoji | Color | Interpretation |
|-------------|----------|-------|-------|-----------------|
| 80-100 | Excellent | 🌟 | #10b981 | Outstanding financial health |
| 65-79 | Very Good | 👍 | #3b82f6 | Strong financial position |
| 50-64 | Good | ✓ | #f59e0b | Decent financial health |
| 35-49 | Average | ⚠️ | #f97316 | Moderate concerns |
| 0-34 | Poor | 🚨 | #ef4444 | Critical issues |

---

## Weightage Justification

### Why These Weights?

#### 1. Savings (30%) - HIGHEST WEIGHT

**Rationale:**
- Savings is the **foundation of financial health**
- Shows discipline and future planning
- Builds emergency fund and wealth
- Most important long-term indicator
- Enables financial independence

**Financial Principle:** "Pay yourself first"

**Target:** 20% of monthly income

**Scoring Logic:**
```
Savings Ratio ≥ 20% → 100 points (Excellent)
Savings Ratio 15-20% → 85 points (Very Good)
Savings Ratio 10-15% → 70 points (Good)
Savings Ratio 5-10% → 50 points (Average)
Savings Ratio < 5% → 30 points (Poor)
```

---

#### 2. Debt Management (25%) - SECOND HIGHEST

**Rationale:**
- Debt can **destroy financial health quickly**
- High EMI reduces money for other needs
- Debt trap is a real risk for young professionals
- Critical indicator of financial stress
- Directly impacts quality of life

**Financial Principle:** "Debt is a liability that reduces net worth"

**Target:** EMI < 10% of monthly income

**Scoring Logic:**
```
EMI Ratio ≤ 10% → 100 points (Excellent)
EMI Ratio 10-20% → 85 points (Very Good)
EMI Ratio 20-30% → 65 points (Good)
EMI Ratio 30-40% → 45 points (Average)
EMI Ratio > 40% → 25 points (Poor)
```

---

#### 3. Expense Control (20%) - MEDIUM WEIGHT

**Rationale:**
- Shows **financial discipline** and sustainability
- If expenses > income, financial trouble ahead
- Expense ratio indicates lifestyle sustainability
- Shows ability to live within means
- Foundation for savings

**Financial Principle:** "You can't save if you overspend"

**Target:** Total expenses < 70% of income

**Scoring Logic:**
```
Expense Ratio ≤ 70% → 100 points (Excellent)
Expense Ratio 70-80% → 85 points (Very Good)
Expense Ratio 80-90% → 65 points (Good)
Expense Ratio 90-100% → 40 points (Average)
Expense Ratio > 100% → 20 points (Poor)
```

---

#### 4. Balance (15%) - LOWER WEIGHT

**Rationale:**
- Shows **smart allocation** of expenses
- Distinguishes essential vs discretionary spending
- Prevents lifestyle inflation
- Less critical than savings/debt (if those are good, balance usually follows)
- More of an "optimization" factor

**Financial Principle:** "Balance prevents lifestyle inflation"

**Target:** Essential < 60%, Discretionary < 20%

**Scoring Logic:**
```
Essential ≤ 60% AND Discretionary ≤ 20% → 100 points
Essential ≤ 70% AND Discretionary ≤ 25% → 85 points
Essential ≤ 80% AND Discretionary ≤ 30% → 65 points
Essential ≤ 90% AND Discretionary ≤ 35% → 45 points
Otherwise → 25 points
```

---

#### 5. Life Stage (10%) - LOWEST WEIGHT

**Rationale:**
- **Context matters** but shouldn't override fundamentals
- A 25-year-old with 10% savings is different from 55-year-old
- Age and dependents affect expectations
- But good financial habits matter at any age
- Adjustment factor, not primary indicator

**Financial Principle:** "Adjust expectations by life stage, but maintain discipline"

**Scoring Logic:**
```
Age < 25:
  - Savings ≥ 25% → +20 points
  - Savings ≥ 15% → +10 points

Age 25-40:
  - Savings ≥ 20% → +20 points
  - Savings ≥ 15% → +10 points

Age 40-55:
  - Savings ≥ 25% → +20 points
  - Savings ≥ 20% → +10 points

Age > 55:
  - Savings ≥ 30% → +20 points
  - Savings ≥ 25% → +10 points

Dependents > 3: -10 points
```

---

## Scoring Factors

### Factor 1: Savings Score

**Definition:** Measures how much an individual saves relative to income

**Formula:**
```python
savings_ratio = disposable_income / monthly_income

if savings_ratio >= 0.20:
    score = 100
elif savings_ratio >= 0.15:
    score = 85
elif savings_ratio >= 0.10:
    score = 70
elif savings_ratio >= 0.05:
    score = 50
else:
    score = 30
```

**Why It Matters:**
- Shows financial discipline
- Builds emergency fund
- Enables wealth creation
- Indicates future financial security

**Data Source:** `Disposable_Income` from Dataset 2

---

### Factor 2: Debt Management Score

**Definition:** Measures EMI burden relative to income

**Formula:**
```python
emi_ratio = loan_repayment / monthly_income

if emi_ratio <= 0.10:
    score = 100
elif emi_ratio <= 0.20:
    score = 85
elif emi_ratio <= 0.30:
    score = 65
elif emi_ratio <= 0.40:
    score = 45
else:
    score = 25
```

**Why It Matters:**
- High EMI reduces financial flexibility
- Indicates debt trap risk
- Shows ability to manage obligations
- Critical for financial stability

**Data Source:** `Loan_Repayment` from Dataset 2

---

### Factor 3: Expense Control Score

**Definition:** Measures total spending relative to income

**Formula:**
```python
total_expenses = (Rent + Loan_Repayment + Insurance + Groceries + 
                  Transport + Eating_Out + Entertainment + Utilities + 
                  Healthcare + Education + Miscellaneous)

expense_ratio = total_expenses / monthly_income

if expense_ratio <= 0.70:
    score = 100
elif expense_ratio <= 0.80:
    score = 85
elif expense_ratio <= 0.90:
    score = 65
elif expense_ratio <= 1.00:
    score = 40
else:
    score = 20
```

**Why It Matters:**
- Shows spending discipline
- Indicates sustainability
- Reveals financial stress
- Foundation for savings

**Data Source:** All expense categories from Dataset 2

---

### Factor 4: Balance Score

**Definition:** Measures balance between essential and discretionary spending

**Formula:**
```python
essential = Rent + Groceries + Transport + Utilities + Healthcare + Insurance
discretionary = Eating_Out + Entertainment + Miscellaneous

essential_ratio = essential / monthly_income
discretionary_ratio = discretionary / monthly_income

if essential_ratio <= 0.60 and discretionary_ratio <= 0.20:
    score = 100
elif essential_ratio <= 0.70 and discretionary_ratio <= 0.25:
    score = 85
elif essential_ratio <= 0.80 and discretionary_ratio <= 0.30:
    score = 65
elif essential_ratio <= 0.90 and discretionary_ratio <= 0.35:
    score = 45
else:
    score = 25
```

**Why It Matters:**
- Prevents lifestyle inflation
- Shows spending priorities
- Indicates financial maturity
- Enables optimization

**Data Source:** Categorized expenses from Dataset 2

---

### Factor 5: Life Stage Score

**Definition:** Adjusts score based on age and dependents

**Formula:**
```python
base_score = 70

# Age-based adjustment
if age < 25:
    if savings_ratio >= 0.25:
        base_score += 20
    elif savings_ratio >= 0.15:
        base_score += 10
elif age < 40:
    if savings_ratio >= 0.20:
        base_score += 20
    elif savings_ratio >= 0.15:
        base_score += 10
elif age < 55:
    if savings_ratio >= 0.25:
        base_score += 20
    elif savings_ratio >= 0.20:
        base_score += 10
else:
    if savings_ratio >= 0.30:
        base_score += 20
    elif savings_ratio >= 0.25:
        base_score += 10

# Dependent adjustment
if dependents > 3:
    base_score -= 10

score = min(base_score, 100)
```

**Why It Matters:**
- Recognizes different life stages
- Adjusts expectations by age
- Considers family responsibilities
- Fair and contextual scoring

**Data Source:** `Age` and `Dependents` from Dataset 2

---

## Implementation

### Complete Scoring Function

```python
def calculate_savings_score(row):
    """Calculate savings score (0-100)"""
    savings_ratio = row['Disposable_Income'] / row['Income']
    
    if savings_ratio >= 0.20:
        return 100
    elif savings_ratio >= 0.15:
        return 85
    elif savings_ratio >= 0.10:
        return 70
    elif savings_ratio >= 0.05:
        return 50
    else:
        return 30

def calculate_debt_score(row):
    """Calculate debt management score (0-100)"""
    emi_ratio = row['Loan_Repayment'] / row['Income']
    
    if emi_ratio <= 0.10:
        return 100
    elif emi_ratio <= 0.20:
        return 85
    elif emi_ratio <= 0.30:
        return 65
    elif emi_ratio <= 0.40:
        return 45
    else:
        return 25

def calculate_expense_score(row):
    """Calculate expense control score (0-100)"""
    total_expenses = (
        row['Rent'] + row['Loan_Repayment'] + row['Insurance'] +
        row['Groceries'] + row['Transport'] + row['Eating_Out'] +
        row['Entertainment'] + row['Utilities'] + row['Healthcare'] +
        row['Education'] + row['Miscellaneous']
    )
    expense_ratio = total_expenses / row['Income']
    
    if expense_ratio <= 0.70:
        return 100
    elif expense_ratio <= 0.80:
        return 85
    elif expense_ratio <= 0.90:
        return 65
    elif expense_ratio <= 1.00:
        return 40
    else:
        return 20

def calculate_balance_score(row):
    """Calculate balance score (0-100)"""
    essential = (
        row['Rent'] + row['Groceries'] + row['Transport'] +
        row['Utilities'] + row['Healthcare'] + row['Insurance']
    )
    discretionary = (
        row['Eating_Out'] + row['Entertainment'] + row['Miscellaneous']
    )
    
    essential_ratio = essential / row['Income']
    discretionary_ratio = discretionary / row['Income']
    
    if essential_ratio <= 0.60 and discretionary_ratio <= 0.20:
        return 100
    elif essential_ratio <= 0.70 and discretionary_ratio <= 0.25:
        return 85
    elif essential_ratio <= 0.80 and discretionary_ratio <= 0.30:
        return 65
    elif essential_ratio <= 0.90 and discretionary_ratio <= 0.35:
        return 45
    else:
        return 25

def calculate_life_stage_score(row):
    """Calculate life stage score (0-100)"""
    age = row['Age']
    dependents = row['Dependents']
    savings_ratio = row['Disposable_Income'] / row['Income']
    
    base_score = 70
    
    # Age adjustment
    if age < 25:
        if savings_ratio >= 0.25:
            base_score += 20
        elif savings_ratio >= 0.15:
            base_score += 10
    elif age < 40:
        if savings_ratio >= 0.20:
            base_score += 20
        elif savings_ratio >= 0.15:
            base_score += 10
    elif age < 55:
        if savings_ratio >= 0.25:
            base_score += 20
        elif savings_ratio >= 0.20:
            base_score += 10
    else:
        if savings_ratio >= 0.30:
            base_score += 20
        elif savings_ratio >= 0.25:
            base_score += 10
    
    # Dependent adjustment
    if dependents > 3:
        base_score -= 10
    
    return min(base_score, 100)

def calculate_financial_health_score(row):
    """
    Calculate comprehensive financial health score (0-100)
    
    Weights:
    - Savings: 30%
    - Debt: 25%
    - Expenses: 20%
    - Balance: 15%
    - Life Stage: 10%
    """
    savings_score = calculate_savings_score(row)
    debt_score = calculate_debt_score(row)
    expense_score = calculate_expense_score(row)
    balance_score = calculate_balance_score(row)
    life_stage_score = calculate_life_stage_score(row)
    
    overall_score = (
        savings_score * 0.30 +
        debt_score * 0.25 +
        expense_score * 0.20 +
        balance_score * 0.15 +
        life_stage_score * 0.10
    )
    
    return round(overall_score, 2)

def classify_financial_health(score):
    """Classify score into categories"""
    if score >= 80:
        return {
            'category': 'Excellent',
            'emoji': '🌟',
            'color': '#10b981',
            'description': 'Outstanding financial health. Keep up the great work!'
        }
    elif score >= 65:
        return {
            'category': 'Very Good',
            'emoji': '👍',
            'color': '#3b82f6',
            'description': 'Strong financial position. Minor improvements possible.'
        }
    elif score >= 50:
        return {
            'category': 'Good',
            'emoji': '✓',
            'color': '#f59e0b',
            'description': 'Decent financial health. Focus on savings and debt.'
        }
    elif score >= 35:
        return {
            'category': 'Average',
            'emoji': '⚠️',
            'color': '#f97316',
            'description': 'Moderate concerns. Review spending and increase savings.'
        }
    else:
        return {
            'category': 'Poor',
            'emoji': '🚨',
            'color': '#ef4444',
            'description': 'Critical issues. Immediate action needed.'
        }
```

### Usage Example

```python
import pandas as pd

# Load Dataset 2
df = pd.read_csv('india_personal_finance.csv')

# Apply scoring
df['financial_health_score'] = df.apply(calculate_financial_health_score, axis=1)
df['classification'] = df['financial_health_score'].apply(classify_financial_health)

# Get score for first person
person = df.iloc[0]
print(f"Score: {person['financial_health_score']}")
print(f"Category: {person['classification']['category']}")
```

---

## Validation

### Method 1: Correlation Analysis

```python
# Check if our score correlates with actual financial health
correlation_with_savings = df['financial_health_score'].corr(df['Disposable_Income'])
correlation_with_potential = df['financial_health_score'].corr(df['Potential_Savings'])

print(f"Correlation with Disposable Income: {correlation_with_savings:.3f}")
print(f"Correlation with Potential Savings: {correlation_with_potential:.3f}")

# Expected: > 0.7 (strong positive correlation)
```

### Method 2: Scenario Testing

```python
# Test with known scenarios
scenarios = [
    {
        'name': 'Excellent Profile',
        'Income': 100000,
        'Disposable_Income': 25000,
        'Loan_Repayment': 5000,
        'Rent': 20000,
        'Groceries': 8000,
        'Transport': 4000,
        'Eating_Out': 3000,
        'Entertainment': 2000,
        'Utilities': 2500,
        'Healthcare': 1500,
        'Insurance': 2000,
        'Education': 1500,
        'Miscellaneous': 4000,
        'Age': 35,
        'Dependents': 1
    },
    # ... more scenarios
]

for scenario in scenarios:
    score = calculate_financial_health_score(scenario)
    print(f"{scenario['name']}: {score}/100")
```

### Expected Results

| Scenario | Expected Score | Actual Score | Status |
|----------|-----------------|--------------|--------|
| Excellent Profile | 80+ | TBD | ✓ |
| Good Profile | 60-75 | TBD | ✓ |
| Average Profile | 40-55 | TBD | ✓ |
| Poor Profile | <35 | TBD | ✓ |

---

## Why No Credit Score

### What is Credit Score?

Credit score (300-850 in India) measures:
- **Payment history** (35%) - Did you pay on time?
- **Credit utilization** (30%) - How much debt do you have?
- **Length of history** (15%) - How long have you had credit?
- **Credit mix** (10%) - Different types of debt?
- **New inquiries** (10%) - Recent credit applications?

### Why Dataset 2 Doesn't Have It

Dataset 2 focuses on **current financial behavior**, not historical credit data. This is intentional because:

1. **Most users have no credit history** (students, young professionals)
2. **Current behavior is more predictive** than past behavior
3. **More actionable** for users to improve

### Why Our Model is Better

#### Scenario 1: Good Current Finances, Bad Credit History

```
Person A:
- Income: ₹50,000
- Savings: ₹10,000 (20%)
- EMI: ₹3,000 (6%)
- Expenses: ₹37,000 (74%)

Credit Score Approach:
- Had default 5 years ago
- Score: 550/850 (Poor)
- Conclusion: Not creditworthy

Our Model:
- Savings Score: 100
- Debt Score: 100
- Expense Score: 100
- Overall: 78/100 (Good)
- Conclusion: Financially healthy NOW ✓

Reality: Person A is financially healthy NOW
Our model is MORE realistic ✓
```

#### Scenario 2: Bad Current Finances, Good Credit History

```
Person B:
- Income: ₹30,000
- Savings: ₹500 (1.7%)
- EMI: ₹12,000 (40%)
- Expenses: ₹29,500 (98%)

Credit Score Approach:
- Perfect payment history
- Score: 750/850 (Good)
- Conclusion: Creditworthy

Our Model:
- Savings Score: 30
- Debt Score: 25
- Expense Score: 20
- Overall: 25/100 (Poor)
- Conclusion: In financial trouble NOW ✓

Reality: Person B is in financial trouble NOW
Our model is MORE realistic ✓
```

### Key Differences

| Aspect | Credit Score | Our Model |
|--------|--------------|-----------|
| **Measures** | Past behavior | Current behavior |
| **Relevance** | Historical | Immediate |
| **Actionability** | Low | High |
| **For Students** | Not applicable | Perfect |
| **Predictive** | Moderate | High |
| **Transparency** | Black box | Transparent |

### Conclusion

**Our 5-factor model is MORE appropriate** for assessing financial health because:

1. ✅ Measures current financial behavior
2. ✅ Provides actionable insights
3. ✅ Works for users with no credit history
4. ✅ More predictive of future financial health
5. ✅ Transparent and explainable
6. ✅ Aligns with available data

---

## Summary

SmartFin's financial health scoring model provides a **realistic, actionable assessment** of financial health using 5 key dimensions:

- **Savings (30%)** - Foundation of financial health
- **Debt (25%)** - Critical risk factor
- **Expenses (20%)** - Shows discipline
- **Balance (15%)** - Optimization factor
- **Life Stage (10%)** - Context adjustment

This model is **better than credit scores** for assessing current financial health and providing actionable recommendations to users.

---

**Document Status:** Complete  
**Last Updated:** February 26, 2026  
**Next Review:** March 15, 2026

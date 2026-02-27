# 8-Factor Financial Health Scoring - Weightage Methodology

## Overview

The weightages for each factor in our 8-factor enhanced model are **manually determined based on financial domain expertise and industry best practices**, not automatically learned by the ML algorithm.

---

## Current Weightage Distribution

| Factor | Weight | Rationale |
|--------|--------|-----------|
| **Savings** | 25% | Most important - indicates financial discipline and emergency fund capacity |
| **Debt Management (EMI)** | 20% | Critical - shows ability to manage obligations |
| **Expense Control** | 18% | Important - demonstrates spending discipline |
| **Balance Score** | 12% | Moderate - shows allocation between essential and discretionary spending |
| **Loan Diversity** | 10% | Moderate - indicates portfolio management |
| **Life Stage** | 8% | Minor - contextual factor for age-based expectations |
| **Payment History** | 5% | Minor - indicates past payment behavior |
| **Loan Maturity** | 2% | Minimal - indicates loan tenure status |
| **TOTAL** | **100%** | ✓ Sums to 100% |

---

## How Weightages Are Decided

### 1. **Domain Expertise Approach** (Current Method)
The weightages are set based on:
- **Financial industry standards** - What credit bureaus and banks consider important
- **Risk assessment principles** - Which factors best predict financial health
- **User impact** - Which factors users can most directly control

### 2. **Rationale for Each Factor**

#### Savings (25%) - HIGHEST WEIGHT
**Why?**
- Indicates financial discipline and planning
- Shows ability to build emergency funds
- Demonstrates surplus after expenses
- Most predictive of financial stability
- Users can directly improve this

**Scoring Logic:**
```python
if savings_ratio >= 0.30:
    return 100  # Excellent
elif savings_ratio >= 0.20:
    return 85   # Very Good
elif savings_ratio >= 0.10:
    return 70   # Good
elif savings_ratio >= 0.05:
    return 50   # Average
else:
    return 30   # Poor
```

#### Debt Management (20%) - SECOND HIGHEST
**Why?**
- EMI-to-income ratio is critical for creditworthiness
- Shows ability to service obligations
- Banks heavily weight this in lending decisions
- Directly impacts credit score

**Scoring Logic:**
```python
emi_ratio = emi / income
if emi_ratio <= 0.10:
    return 100  # Excellent (low debt burden)
elif emi_ratio <= 0.20:
    return 85
elif emi_ratio <= 0.30:
    return 65
elif emi_ratio <= 0.40:
    return 45
else:
    return 25   # Poor (high debt burden)
```

#### Expense Control (18%) - THIRD HIGHEST
**Why?**
- Shows spending discipline
- Indicates ability to live within means
- Affects savings capacity
- Controllable by user behavior

**Scoring Logic:**
```python
expense_ratio = expenses / income
if expense_ratio <= 0.50:
    return 100  # Excellent (low spending)
elif expense_ratio <= 0.65:
    return 85
elif expense_ratio <= 0.80:
    return 70
elif expense_ratio <= 0.90:
    return 50
else:
    return 30   # Poor (overspending)
```

#### Balance Score (12%) - MODERATE
**Why?**
- Shows allocation between essential and discretionary
- Indicates financial maturity
- Helps identify spending patterns

**Scoring Logic:**
```python
essential_ratio = (rent + food + emi) / total_spending
if essential_ratio >= 0.70:
    return 100  # Good balance
elif essential_ratio >= 0.60:
    return 85
elif essential_ratio >= 0.50:
    return 70
else:
    return 50   # Too much discretionary
```

#### Loan Diversity (10%) - MODERATE
**Why?**
- Shows portfolio management
- Indicates credit mix (important for credit score)
- Demonstrates ability to manage multiple obligations
- NEW factor added in enhanced model

#### Life Stage (8%) - MINOR
**Why?**
- Contextual factor for age-based expectations
- Young professionals have different patterns than established earners
- Helps normalize scores across age groups

**Scoring Logic:**
```python
if age < 25:
    return 60   # Building phase
elif age < 35:
    return 75   # Establishing
elif age < 50:
    return 85   # Peak earning
elif age < 65:
    return 80   # Pre-retirement
else:
    return 70   # Retirement
```

#### Payment History (5%) - MINIMAL
**Why?**
- Indicates past payment behavior
- Important for credit assessment
- Less directly controllable in short term
- NEW factor added in enhanced model

#### Loan Maturity (2%) - MINIMAL
**Why?**
- Indicates loan tenure status
- Shows progress in loan repayment
- Least impactful on overall health
- NEW factor added in enhanced model

---

## How the ML Model Uses These Weightages

### Important Distinction:

**The 8-factor weightages (25%, 20%, 18%, etc.) are NOT learned by the Gradient Boosting model.**

Instead:
1. **We manually calculate** each factor score (0-100) using domain rules
2. **We manually apply** the weightages to combine them into a single score (0-100)
3. **The Gradient Boosting model** learns from the raw features (income, expenses, savings, emi, age, etc.) to predict this combined score

### Why This Approach?

✅ **Interpretability** - We can explain why a score is what it is
✅ **Control** - We decide what matters, not the algorithm
✅ **Consistency** - Same rules applied to all users
✅ **Adjustability** - Easy to change weightages if needed
✅ **Compliance** - Transparent for regulatory requirements

---

## Feature Importance (What the ML Model Learned)

After training, the Gradient Boosting model shows which raw features are most predictive:

| Feature | Importance | Note |
|---------|-----------|------|
| EMI | 53.71% | Model learned EMI is most predictive |
| Savings | 17.97% | Second most predictive |
| Income | 13.66% | Supporting factor |
| Expenses | 12.95% | Supporting factor |
| Age | 1.15% | Minor factor |
| Loan Amount | 0.34% | Minimal |
| Interest Rate | 0.14% | Minimal |
| Has Loan | 0.08% | Minimal |

**Note:** These are different from our manual weightages! The model learned that EMI is more predictive (53.71%) than our manual weight of 20%.

---

## How to Adjust Weightages

If you want to change the importance of factors, modify the formula in `data/train_enhanced_model.py`:

```python
def calculate_financial_health_score_8factor(row):
    # ... calculate individual scores ...
    
    # MODIFY THESE WEIGHTS:
    score = (
        savings * 0.25 +           # Change this
        debt * 0.20 +              # Change this
        expense * 0.18 +           # Change this
        balance * 0.12 +           # Change this
        life_stage * 0.08 +        # Change this
        loan_diversity * 0.10 +    # Change this
        payment_history * 0.05 +   # Change this
        loan_maturity * 0.02       # Change this
    )
    
    return round(score, 2)
```

**Important:** Weights must sum to 1.0 (100%)

---

## Example Calculation

### User Profile:
- Income: ₹50,000/month
- Rent: ₹10,000
- Food: ₹5,000
- Travel: ₹2,000
- Shopping: ₹3,000
- EMI: ₹5,000
- Savings: ₹10,000
- Age: 30

### Step 1: Calculate Individual Scores

**Savings Score:**
- Savings ratio = 10,000 / 50,000 = 0.20 (20%)
- Score = 85 (Very Good)

**Debt Score:**
- EMI ratio = 5,000 / 50,000 = 0.10 (10%)
- Score = 100 (Excellent)

**Expense Score:**
- Total expenses = 10,000 + 5,000 + 2,000 + 3,000 = ₹20,000
- Expense ratio = 20,000 / 50,000 = 0.40 (40%)
- Score = 100 (Excellent)

**Balance Score:**
- Essential = 10,000 + 5,000 + 5,000 = ₹20,000
- Discretionary = 2,000 + 3,000 = ₹5,000
- Essential ratio = 20,000 / 25,000 = 0.80 (80%)
- Score = 100 (Good balance)

**Life Stage Score:**
- Age = 30
- Score = 75 (Establishing)

**Loan Diversity Score:**
- Has loan = true, EMI ratio = 0.10
- Score = 80 (Low debt burden)

**Payment History Score:**
- No credit score data, EMI ratio = 0.10
- Score = 80 (Manageable debt)

**Loan Maturity Score:**
- Has loan, EMI ratio = 0.10
- Score = 80 (Moderate)

### Step 2: Apply Weightages

```
Final Score = (85 × 0.25) + (100 × 0.20) + (100 × 0.18) + (100 × 0.12) + 
              (75 × 0.08) + (80 × 0.10) + (80 × 0.05) + (80 × 0.02)

            = 21.25 + 20 + 18 + 12 + 6 + 8 + 4 + 1.6
            = 90.85
```

**Final Score: 90.85 (Excellent)**

---

## Considerations for Future Adjustments

### When to Increase a Weight:
- Factor becomes more important for your use case
- User feedback indicates it matters more
- Industry standards change
- Regulatory requirements change

### When to Decrease a Weight:
- Factor becomes less relevant
- Data quality issues with that factor
- User feedback indicates it's less important
- New factors become available

### Validation:
After changing weights, retrain the model:
```bash
python data/train_enhanced_model.py
```

Monitor if R² score improves or degrades.

---

## Comparison with Industry Standards

### Credit Bureau Approach (CIBIL/Equifax):
- Payment History: 35%
- Credit Utilization: 30%
- Length of Credit History: 15%
- Credit Mix: 10%
- New Credit: 10%

### Our Approach:
- Savings: 25% (proactive financial health)
- Debt Management: 20% (similar to payment history)
- Expense Control: 18% (unique to our model)
- Balance Score: 12% (similar to credit mix)
- Loan Diversity: 10% (similar to credit mix)
- Life Stage: 8% (contextual)
- Payment History: 5% (less weight than bureaus)
- Loan Maturity: 2% (unique to our model)

**Key Difference:** We focus more on proactive financial health (savings, expense control) rather than reactive credit history.

---

## Summary

**Current Approach:**
- Weightages are **manually set** based on financial domain expertise
- Each factor has a **scoring rule** (0-100)
- Weightages are **combined** to create final score
- ML model **learns** from raw features to predict this score

**This is NOT:**
- Automatically learned by the algorithm
- Based on statistical correlation alone
- Changed during model training

**This IS:**
- Transparent and explainable
- Based on financial best practices
- Easily adjustable
- Compliant with regulatory requirements

---

## Related Documentation

- [01_financial_health_scoring_model.md](01_financial_health_scoring_model.md) - Overall scoring model
- [05_ml_model_training_process.md](05_ml_model_training_process.md) - Model training details
- [../MODEL_UPGRADE_SUMMARY.md](../MODEL_UPGRADE_SUMMARY.md) - Recent model upgrade

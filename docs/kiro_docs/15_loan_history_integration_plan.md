# Loan History Integration Plan

**Date:** February 26, 2026  
**Status:** Planning Phase  
**Objective:** Include loan history data in financial health scoring model NOW (not v2.0)

---

## Executive Summary

This document outlines a complete plan to integrate loan history data into SmartFin's financial health scoring model immediately. The plan includes data sourcing, model updates, backend changes, frontend modifications, and testing strategy.

**Expected Outcome:** Improve model accuracy from 65-70% R² to 72-78% R²

---

## Table of Contents

1. [Phase 1: Data Sourcing](#phase-1-data-sourcing)
2. [Phase 2: Data Structure Design](#phase-2-data-structure-design)
3. [Phase 3: Model Enhancement](#phase-3-model-enhancement)
4. [Phase 4: Backend Implementation](#phase-4-backend-implementation)
5. [Phase 5: Frontend Implementation](#phase-5-frontend-implementation)
6. [Phase 6: Testing & Validation](#phase-6-testing--validation)
7. [Timeline & Effort Estimate](#timeline--effort-estimate)
8. [Risk Assessment](#risk-assessment)

---

## Phase 1: Data Sourcing

### 1.1 Identify Loan Data Sources

**Option A: Kaggle Datasets (Recommended for MVP)**
- **Home Credit Default Risk Dataset**
  - 307,511 loan records
  - Contains: loan details, payment history, defaults
  - Pros: Free, comprehensive, ready-to-use
  - Cons: Not India-specific
  
- **LendingClub Dataset**
  - 2.2M loan records
  - Contains: loan details, interest rates, payment status
  - Pros: Real data, detailed
  - Cons: US-focused, large file size

**Option B: Synthetic Loan Data (Fastest)**
- Generate synthetic loan history for Dataset 2 users
- Pros: Complete control, India-specific, fast
- Cons: Not real data, may not reflect actual patterns

**Option C: Real Data Integration (Future)**
- CIBIL API integration
- Bank APIs
- Pros: Real data
- Cons: Requires partnerships, compliance, time

### 1.2 Recommended Approach for NOW

**Use Option B (Synthetic) + Option A (Kaggle) Hybrid:**

1. **For Dataset 2 users:** Generate synthetic loan history
   - Create realistic loan profiles
   - Vary loan types, amounts, payment history
   - Ensure India-specific patterns

2. **For model training:** Use Kaggle Home Credit dataset
   - Extract loan patterns
   - Learn payment history distributions
   - Validate model accuracy

3. **For production:** Start with synthetic, plan real data integration

---

## Phase 2: Data Structure Design

### 2.1 Loan Data Schema

```python
# Individual Loan Record
loan_record = {
    'loan_id': 'LOAN_001',                    # Unique identifier
    'user_id': 1,                             # Link to user
    'loan_type': 'home',                      # personal, home, auto, education, business
    'loan_amount': 2000000,                   # Principal amount (INR)
    'loan_tenure_months': 240,                # Total duration
    'loan_start_date': '2020-01-15',          # When loan started
    'loan_end_date': '2040-01-15',            # When loan ends
    'loan_remaining_months': 180,             # Months left
    'monthly_emi': 10000,                     # Monthly payment
    'interest_rate': 7.5,                     # Annual interest %
    'collateral_type': 'property',            # none, property, vehicle, etc.
    'loan_purpose': 'home_purchase',          # Description
    'default_status': 'active',               # active, closed, defaulted
    'created_at': '2020-01-15',
    'updated_at': '2026-02-26'
}

# Payment History Record
payment_record = {
    'payment_id': 'PAY_001',
    'loan_id': 'LOAN_001',
    'payment_date': '2020-02-15',
    'payment_amount': 10000,
    'payment_status': 'on_time',              # on_time, late, missed
    'days_overdue': 0,
    'created_at': '2020-02-15'
}

# Aggregate Loan Metrics (calculated)
loan_metrics = {
    'user_id': 1,
    'total_loans': 2,
    'total_debt': 2500000,
    'total_monthly_emi': 20000,
    'average_interest_rate': 8.2,
    'average_loan_remaining_months': 150,
    'on_time_payments': 72,
    'late_payments': 2,
    'missed_payments': 0,
    'payment_consistency_score': 97.3,       # % of on-time payments
    'has_default': False,
    'loan_diversity_score': 75,               # Calculated
    'payment_history_score': 85,              # Calculated
    'loan_maturity_score': 70,                # Calculated
    'calculated_at': '2026-02-26'
}
```

### 2.2 Database Schema

```sql
-- Loans table
CREATE TABLE loans (
    loan_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    loan_type TEXT NOT NULL,
    loan_amount REAL NOT NULL,
    loan_tenure_months INTEGER NOT NULL,
    loan_start_date TEXT NOT NULL,
    loan_end_date TEXT NOT NULL,
    loan_remaining_months INTEGER NOT NULL,
    monthly_emi REAL NOT NULL,
    interest_rate REAL NOT NULL,
    collateral_type TEXT,
    loan_purpose TEXT,
    default_status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Payment history table
CREATE TABLE loan_payments (
    payment_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    payment_date TEXT NOT NULL,
    payment_amount REAL NOT NULL,
    payment_status TEXT NOT NULL,
    days_overdue INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
);

-- Loan metrics cache (for performance)
CREATE TABLE loan_metrics (
    user_id INTEGER PRIMARY KEY,
    total_loans INTEGER,
    total_debt REAL,
    total_monthly_emi REAL,
    average_interest_rate REAL,
    average_loan_remaining_months REAL,
    on_time_payments INTEGER,
    late_payments INTEGER,
    missed_payments INTEGER,
    payment_consistency_score REAL,
    has_default INTEGER,
    loan_diversity_score REAL,
    payment_history_score REAL,
    loan_maturity_score REAL,
    calculated_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 2.3 Data Integration Points

```
Dataset 2 (User Financial Data)
        ↓
    + Loan History (New)
        ↓
    Combined Dataset
        ↓
    Feature Engineering
        ↓
    ML Model Training
        ↓
    Financial Health Score
```

---

## Phase 3: Model Enhancement

### 3.1 New Scoring Factors

#### Factor 1: Loan Diversity Score (10% weight)

```
Purpose: Assess portfolio quality
Range: 0-100

Logic:
- 0 loans: 100 (no debt)
- 1 loan: 50 (concentrated risk)
- 2-3 loans: 75 (good diversity)
- 4+ loans: 100 (excellent diversity)

Also consider:
- Loan type diversity (home + auto > home + home)
- Loan amount distribution
```

#### Factor 2: Payment History Score (5% weight)

```
Purpose: Measure financial discipline
Range: 0-100

Logic:
- Default status: 0 (critical)
- <80% on-time: 25 (poor)
- 80-89% on-time: 50 (fair)
- 90-94% on-time: 70 (good)
- 95-99% on-time: 85 (very good)
- 100% on-time: 100 (excellent)

Also consider:
- Trend (improving vs declining)
- Recent payment behavior
- Days overdue (max)
```

#### Factor 3: Loan Maturity Score (2% weight)

```
Purpose: Evaluate future burden
Range: 0-100

Logic:
- All loans ending <1 year: 100 (low burden)
- Mix of 1-3 years: 85 (moderate)
- Mix of 3-5 years: 70 (longer term)
- Long-term (5+ years): 50 (extended burden)

Also consider:
- Weighted by loan amount
- Concentration of maturity dates
```

#### Factor 4: Advanced Debt Analysis (Enhanced)

```
Purpose: Sophisticated debt burden assessment
Range: 0-100

Components:
1. EMI Ratio (50% weight)
   - Monthly EMI / Monthly Income
   - ≤10%: 100, ≤20%: 85, ≤30%: 65, >30%: 40

2. Debt-to-Income Ratio (30% weight)
   - Total Debt / Annual Income
   - ≤1.0: 100, ≤2.0: 85, ≤3.0: 65, >3.0: 40

3. Interest Rate Impact (20% weight)
   - Average weighted interest rate
   - ≤5%: 100, ≤10%: 85, ≤15%: 70, >15%: 50

Combined: (EMI × 0.5) + (DTI × 0.3) + (Interest × 0.2)
```

### 3.2 Updated Scoring Model

**Current Model (5 factors):**
```
Score = (S × 0.30) + (D × 0.25) + (E × 0.20) + (B × 0.15) + (L × 0.10)

Where:
S = Savings Score
D = Debt Management Score
E = Expense Control Score
B = Balance Score
L = Life Stage Score
```

**Enhanced Model (8 factors):**
```
Score = (S × 0.25) +      # Savings (reduced from 30%)
        (D × 0.20) +      # Debt (reduced from 25%)
        (E × 0.18) +      # Expenses (reduced from 20%)
        (B × 0.12) +      # Balance (reduced from 15%)
        (L × 0.08) +      # Life Stage (reduced from 10%)
        (LD × 0.10) +     # Loan Diversity (NEW)
        (PH × 0.05) +     # Payment History (NEW)
        (LM × 0.02)       # Loan Maturity (NEW)

Where:
S = Savings Score
D = Debt Management Score (now includes advanced analysis)
E = Expense Control Score
B = Balance Score
L = Life Stage Score
LD = Loan Diversity Score
PH = Payment History Score
LM = Loan Maturity Score
```

### 3.3 Weightage Justification

| Factor | Old | New | Reason |
|--------|-----|-----|--------|
| Savings | 30% | 25% | Still most important, but loan data provides more context |
| Debt | 25% | 20% | Now more sophisticated with advanced analysis |
| Expenses | 20% | 18% | Still important, slightly reduced |
| Balance | 15% | 12% | Still important, slightly reduced |
| Life Stage | 10% | 8% | Context adjustment, slightly reduced |
| Loan Diversity | - | 10% | NEW - portfolio quality assessment |
| Payment History | - | 5% | NEW - financial discipline indicator |
| Loan Maturity | - | 2% | NEW - future burden assessment |

---

## Phase 4: Backend Implementation

### 4.1 New Services

**LoanService** (similar to ProfileService)
```
Methods:
- create_loan(user_id, loan_data)
- get_loans(user_id)
- update_loan(loan_id, updates)
- delete_loan(loan_id)
- get_loan_metrics(user_id)
- calculate_loan_diversity_score(user_id)
- calculate_payment_history_score(user_id)
- calculate_loan_maturity_score(user_id)
```

**PaymentHistoryService**
```
Methods:
- add_payment(loan_id, payment_data)
- get_payment_history(loan_id)
- calculate_payment_consistency(loan_id)
- get_payment_status(loan_id)
```

### 4.2 New API Endpoints

```
POST /api/loans
- Create new loan
- Auth: JWT required
- Body: loan_data

GET /api/loans
- Get all loans for user
- Auth: JWT required
- Response: array of loans

PUT /api/loans/:id
- Update loan
- Auth: JWT required
- Body: updates

DELETE /api/loans/:id
- Delete loan
- Auth: JWT required

POST /api/loans/:id/payments
- Add payment record
- Auth: JWT required
- Body: payment_data

GET /api/loans/:id/payments
- Get payment history
- Auth: JWT required
- Response: array of payments

GET /api/loans/metrics
- Get aggregate loan metrics
- Auth: JWT required
- Response: loan_metrics
```

### 4.3 Updated Prediction Endpoint

```
POST /api/predict
- Calculate financial health score WITH loan data
- Auth: JWT required
- Body: {
    income, rent, food, travel, shopping, emi, savings,
    loans: [...]  # NEW
  }
- Response: {
    score: 75,
    breakdown: {
      savings_score: 80,
      debt_score: 70,
      expense_score: 75,
      balance_score: 72,
      life_stage_score: 68,
      loan_diversity_score: 75,      # NEW
      payment_history_score: 85,     # NEW
      loan_maturity_score: 70        # NEW
    }
  }
```

### 4.4 Database Migrations

```
Migration 1: Create loans table
Migration 2: Create loan_payments table
Migration 3: Create loan_metrics table
Migration 4: Add indexes for performance
Migration 5: Seed synthetic loan data (for testing)
```

---

## Phase 5: Frontend Implementation

### 5.1 New UI Components

**LoanManager Component**
```
Features:
- Display list of loans
- Add new loan form
- Edit loan form
- Delete loan with confirmation
- View payment history
- Display loan metrics summary
```

**LoanForm Component**
```
Fields:
- Loan Type (dropdown)
- Loan Amount (number)
- Loan Tenure (months)
- Monthly EMI (number)
- Interest Rate (%)
- Collateral Type (dropdown)
- Loan Purpose (text)
- Start Date (date picker)
```

**PaymentHistoryViewer Component**
```
Features:
- Timeline of payments
- Payment status indicators
- Days overdue display
- Payment consistency chart
- Export payment history
```

**LoanMetricsSummary Component**
```
Display:
- Total loans
- Total debt
- Average interest rate
- Payment consistency %
- Loan diversity score
- Payment history score
- Loan maturity score
```

### 5.2 Updated Dashboard

```
Current Dashboard:
- Financial Health Score
- Score Breakdown (5 factors)
- Spending Chart
- Goals

Enhanced Dashboard:
- Financial Health Score
- Score Breakdown (8 factors) ← UPDATED
- Spending Chart
- Loan Summary ← NEW
- Payment History ← NEW
- Goals
```

### 5.3 Updated Profile Page

```
Current Profile:
- Personal Info
- Risk Assessment
- Notification Preferences
- Profile Picture

Enhanced Profile:
- Personal Info
- Risk Assessment
- Notification Preferences
- Profile Picture
- Loan Management ← NEW
- Loan Metrics ← NEW
```

---

## Phase 6: Testing & Validation

### 6.1 Unit Tests

**LoanService Tests**
```
- Create loan with valid data
- Create loan with invalid data
- Get loans for user
- Update loan
- Delete loan
- Calculate loan diversity score
- Calculate payment history score
- Calculate loan maturity score
```

**PaymentHistoryService Tests**
```
- Add payment record
- Get payment history
- Calculate payment consistency
- Handle late payments
- Handle missed payments
- Handle defaults
```

### 6.2 Property-Based Tests

```
Property 1: Loan diversity score range
- For any number of loans, score is 0-100

Property 2: Payment history score consistency
- For any payment history, score reflects on-time %

Property 3: Loan maturity score validity
- For any loan tenure, score is 0-100

Property 4: Advanced debt score calculation
- For any debt configuration, score is 0-100

Property 5: Score improvement with loan data
- With loan data, R² score improves by 7-8%
```

### 6.3 Integration Tests

```
Test 1: Complete loan workflow
- Create loan → Add payments → Calculate metrics → Update score

Test 2: Multiple loans
- Create 3 loans → Calculate diversity → Verify score

Test 3: Payment history impact
- Create loan → Add on-time payments → Verify score increase
- Create loan → Add late payments → Verify score decrease

Test 4: Score comparison
- Calculate score without loan data
- Calculate score with loan data
- Verify improvement
```

### 6.4 Model Validation

```
Validation 1: Accuracy Improvement
- Train model with Dataset 2 only: R² = 65-70%
- Train model with Dataset 2 + Loan data: R² = 72-78%
- Verify improvement of 7-8%

Validation 2: Scenario Testing
- Test 10 different user scenarios
- Verify scores are realistic
- Verify loan data impacts score appropriately

Validation 3: Edge Cases
- User with no loans
- User with multiple loans
- User with defaults
- User with perfect payment history
```

---

## Phase 7: Data Generation Strategy

### 7.1 Synthetic Loan Data Generation

**For Dataset 2 users (20,000 records):**

```python
# Generate realistic loan profiles

For each user:
1. Decide number of loans (0-4)
   - 40% have 0 loans
   - 35% have 1 loan
   - 20% have 2 loans
   - 5% have 3+ loans

2. For each loan:
   - Loan type: weighted distribution
     - Home: 40%
     - Auto: 30%
     - Personal: 20%
     - Education: 10%
   
   - Loan amount: based on income
     - Home: 5-10x annual income
     - Auto: 0.5-2x annual income
     - Personal: 0.1-0.5x annual income
     - Education: 0.2-1x annual income
   
   - Tenure: based on loan type
     - Home: 180-240 months
     - Auto: 36-60 months
     - Personal: 12-36 months
     - Education: 60-120 months
   
   - Interest rate: based on loan type
     - Home: 6-8%
     - Auto: 8-12%
     - Personal: 12-18%
     - Education: 4-8%
   
   - Payment history: realistic distribution
     - 70% perfect (100% on-time)
     - 20% good (95-99% on-time)
     - 7% fair (85-94% on-time)
     - 2% poor (<85% on-time)
     - 1% default
```

### 7.2 Data Validation

```
Checks:
1. EMI ≤ 30% of income (realistic)
2. Total debt ≤ 5x annual income (realistic)
3. Payment history is consistent
4. Loan dates are logical
5. No negative values
6. All required fields present
```

---

## Timeline & Effort Estimate

### Phase Breakdown

| Phase | Tasks | Effort | Duration |
|-------|-------|--------|----------|
| 1 | Data Sourcing | 2 hours | 1 day |
| 2 | Data Structure Design | 3 hours | 1 day |
| 3 | Model Enhancement | 4 hours | 1 day |
| 4 | Backend Implementation | 8 hours | 2 days |
| 5 | Frontend Implementation | 6 hours | 1.5 days |
| 6 | Testing & Validation | 6 hours | 1.5 days |
| 7 | Documentation | 2 hours | 0.5 days |

**Total Effort:** ~31 hours  
**Total Duration:** ~8 days (working full-time)

### Detailed Timeline

**Day 1: Planning & Data**
- Phase 1: Data Sourcing (2 hours)
- Phase 2: Data Structure Design (3 hours)

**Day 2: Model Design**
- Phase 3: Model Enhancement (4 hours)

**Days 3-4: Backend**
- Phase 4: Backend Implementation (8 hours)

**Days 5-6: Frontend**
- Phase 5: Frontend Implementation (6 hours)

**Days 7-8: Testing**
- Phase 6: Testing & Validation (6 hours)
- Phase 7: Documentation (2 hours)

---

## Risk Assessment

### Risk 1: Data Quality

**Issue:** Synthetic loan data may not reflect real patterns  
**Probability:** Medium  
**Impact:** Model accuracy lower than expected  
**Mitigation:**
- Validate synthetic data against Kaggle datasets
- Use realistic distributions
- Test with real data later

### Risk 2: Model Complexity

**Issue:** 8-factor model may be harder to explain  
**Probability:** Low  
**Impact:** User confusion  
**Mitigation:**
- Provide clear score breakdown
- Add explanations for each factor
- Create user guide

### Risk 3: Performance Impact

**Issue:** Additional database queries may slow down API  
**Probability:** Low  
**Impact:** Slower response times  
**Mitigation:**
- Cache loan metrics
- Use database indexes
- Optimize queries

### Risk 4: Integration Issues

**Issue:** New loan data may conflict with existing code  
**Probability:** Low  
**Impact:** Bugs in existing features  
**Mitigation:**
- Comprehensive testing
- Backward compatibility
- Gradual rollout

### Risk 5: Accuracy Improvement Not Met

**Issue:** R² improvement may be less than 7-8%  
**Probability:** Medium  
**Impact:** Effort not justified  
**Mitigation:**
- Validate model early
- Adjust weights if needed
- Consider alternative approaches

---

## Success Criteria

### Must Have
- ✅ Loan data integrated into database
- ✅ 4 new scoring factors implemented
- ✅ API endpoints working
- ✅ Frontend UI for loan management
- ✅ All tests passing
- ✅ R² score improved to 72-78%

### Should Have
- ✅ Payment history tracking
- ✅ Loan metrics caching
- ✅ Comprehensive documentation
- ✅ User guide for loan management

### Nice to Have
- ✅ Real data integration plan
- ✅ Advanced analytics dashboard
- ✅ Loan recommendations

---

## Next Steps

1. **Approve Plan** - Get stakeholder approval
2. **Create Spec** - Create formal spec with requirements
3. **Start Phase 1** - Begin data sourcing
4. **Iterate** - Follow timeline and adjust as needed

---

## Questions to Answer Before Starting

1. **Data Source:** Use synthetic data or Kaggle dataset?
2. **Timeline:** Can we dedicate 8 days full-time?
3. **Testing:** How thorough should testing be?
4. **Rollout:** Gradual or all-at-once?
5. **Backward Compatibility:** Must old scores still work?

---

**Document Status:** Planning Complete  
**Ready to Start:** Yes  
**Approval Required:** Yes  
**Last Updated:** February 26, 2026


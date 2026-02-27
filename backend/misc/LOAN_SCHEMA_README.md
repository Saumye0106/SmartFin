# Loan History Database Schema

## Overview

This document describes the database schema for the Loan History Enhancement feature in SmartFin. The schema supports comprehensive loan tracking, payment history, and metrics calculation for the enhanced 8-factor financial health scoring model.

## Tables

### 1. loans

Stores comprehensive loan information for each user.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| loan_id | TEXT | PRIMARY KEY | Unique identifier (UUID) |
| user_id | INTEGER | NOT NULL, FK to users(id) | User who owns the loan |
| loan_type | TEXT | NOT NULL, CHECK IN ('personal', 'home', 'auto', 'education') | Type of loan |
| loan_amount | REAL | NOT NULL, CHECK > 0 | Principal amount borrowed |
| loan_tenure | INTEGER | NOT NULL, CHECK > 0 | Duration in months |
| monthly_emi | REAL | NOT NULL, CHECK > 0 | Monthly EMI payment |
| interest_rate | REAL | NOT NULL, CHECK 0-50 | Annual interest rate (%) |
| loan_start_date | TEXT | NOT NULL | ISO 8601 date string |
| loan_maturity_date | TEXT | NOT NULL | ISO 8601 date string |
| default_status | INTEGER | DEFAULT 0 | 0=active, 1=defaulted |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |
| deleted_at | TEXT | NULL | Soft delete timestamp |

**Indexes:**
- `idx_loans_user_id` - Fast lookup by user
- `idx_loans_loan_type` - Filter by loan type
- `idx_loans_default_status` - Filter by default status
- `idx_loans_deleted_at` - Filter active/deleted loans

**Business Rules:**
1. loan_maturity_date must be after loan_start_date
2. monthly_emi should be consistent with amortization formula
3. Cannot modify loan if default_status = 1
4. Cannot modify loan if deleted_at is not NULL
5. Soft delete only - preserve historical data

**Example:**
```sql
INSERT INTO loans (
    loan_id, user_id, loan_type, loan_amount, loan_tenure,
    monthly_emi, interest_rate, loan_start_date, loan_maturity_date
) VALUES (
    'uuid-123', 1, 'personal', 50000.00, 24,
    2291.67, 10.5, '2024-01-01', '2026-01-01'
);
```

---

### 2. loan_payments

Tracks payment history for each loan with status classification.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| payment_id | TEXT | PRIMARY KEY | Unique identifier (UUID) |
| loan_id | TEXT | NOT NULL, FK to loans(loan_id) | Associated loan |
| payment_date | TEXT | NOT NULL | ISO 8601 date string |
| payment_amount | REAL | NOT NULL, CHECK > 0 | Payment amount |
| payment_status | TEXT | NOT NULL, CHECK IN ('on-time', 'late', 'missed') | Payment classification |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes:**
- `idx_loan_payments_loan_id` - Fast lookup by loan
- `idx_loan_payments_payment_date` - Sort by date
- `idx_loan_payments_payment_status` - Filter by status

**Payment Status Classification:**
- **on-time**: payment_date within 5 days of due_date
- **late**: payment_date 5-30 days after due_date
- **missed**: payment_date > 30 days after due_date

**Business Rules:**
1. payment_date cannot be in the future
2. payment_amount cannot exceed remaining loan balance
3. Payment records are immutable once created
4. Cascade delete when loan is deleted

**Example:**
```sql
INSERT INTO loan_payments (
    payment_id, loan_id, payment_date, payment_amount, payment_status
) VALUES (
    'uuid-456', 'uuid-123', '2024-02-01', 2291.67, 'on-time'
);
```

---

### 3. loan_metrics

Caches calculated loan metrics for performance optimization.

**Columns:**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | INTEGER | PRIMARY KEY, FK to users(id) | User identifier |
| loan_diversity_score | REAL | CHECK 0-100 | Loan diversity metric |
| payment_history_score | REAL | CHECK 0-100 | Payment reliability metric |
| loan_maturity_score | REAL | CHECK 0-100 | Loan tenure metric |
| payment_statistics | TEXT | JSON string | Payment stats (on-time %, counts) |
| loan_statistics | TEXT | JSON string | Loan stats (totals, averages) |
| calculated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Calculation timestamp |

**JSON Structures:**

**payment_statistics:**
```json
{
    "on_time_payment_percentage": 95.5,
    "late_payment_count": 2,
    "missed_payment_count": 0,
    "total_payments": 44
}
```

**loan_statistics:**
```json
{
    "total_active_loans": 3,
    "total_loan_amount": 150000.00,
    "average_loan_tenure": 36,
    "weighted_average_tenure": 42.5,
    "loan_type_distribution": {
        "personal": 33.33,
        "home": 50.00,
        "auto": 16.67,
        "education": 0.00
    }
}
```

**Business Rules:**
1. Metrics are recalculated when loans or payments change
2. Cache invalidation on any loan/payment update
3. Default values used if no loan history exists
4. Cascade delete when user is deleted

---

## Relationships

```
users (1) ----< (N) loans
loans (1) ----< (N) loan_payments
users (1) ----< (1) loan_metrics
```

**Foreign Key Constraints:**
- `loans.user_id` → `users.id` (CASCADE DELETE)
- `loan_payments.loan_id` → `loans.loan_id` (CASCADE DELETE)
- `loan_metrics.user_id` → `users.id` (CASCADE DELETE)

---

## Migration

### Initial Setup

Run the migration script to create tables:

```bash
cd backend/misc
python migrate_add_loan_tables.py
```

### Verification

Verify tables were created successfully:

```bash
cd backend/misc
python verify_loan_tables.py
```

### Using Database Utilities

```python
from db_utils import init_loan_tables, verify_loan_tables, get_loan_table_stats

# Initialize tables
init_loan_tables()

# Verify tables
results = verify_loan_tables()
print(results)

# Get statistics
stats = get_loan_table_stats()
print(stats)
```

---

## Queries

### Common Queries

**Get all active loans for a user:**
```sql
SELECT * FROM loans
WHERE user_id = ? AND deleted_at IS NULL
ORDER BY loan_start_date DESC;
```

**Get payment history for a loan:**
```sql
SELECT * FROM loan_payments
WHERE loan_id = ?
ORDER BY payment_date DESC;
```

**Calculate on-time payment percentage:**
```sql
SELECT 
    COUNT(CASE WHEN payment_status = 'on-time' THEN 1 END) * 100.0 / COUNT(*) as on_time_percentage
FROM loan_payments
WHERE loan_id IN (
    SELECT loan_id FROM loans WHERE user_id = ?
);
```

**Get loan diversity (distinct types):**
```sql
SELECT COUNT(DISTINCT loan_type) as diversity_count
FROM loans
WHERE user_id = ? AND deleted_at IS NULL AND default_status = 0;
```

**Get loans maturing within 6 months:**
```sql
SELECT * FROM loans
WHERE user_id = ?
AND deleted_at IS NULL
AND date(loan_maturity_date) <= date('now', '+6 months')
ORDER BY loan_maturity_date ASC;
```

---

## Performance Considerations

1. **Indexes**: All foreign keys and frequently queried columns are indexed
2. **Caching**: loan_metrics table caches expensive calculations
3. **Soft Deletes**: Use deleted_at for historical data preservation
4. **JSON Storage**: Statistics stored as JSON for flexibility
5. **Cascade Deletes**: Automatic cleanup of related records

---

## Data Validation

### Application-Level Validation

The following validations should be enforced in the application layer:

1. **Loan Amount**: Must be positive and greater than zero
2. **Loan Tenure**: Must be positive integer (months)
3. **Interest Rate**: Must be between 0 and 50 percent
4. **Dates**: loan_maturity_date must be after loan_start_date
5. **EMI Calculation**: Verify monthly_emi matches amortization formula
6. **Payment Date**: Cannot be in the future
7. **Payment Amount**: Cannot exceed remaining balance

### Amortization Formula

```python
def calculate_emi(principal, annual_rate, tenure_months):
    """Calculate monthly EMI using standard amortization formula"""
    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        return principal / tenure_months
    
    emi = principal * monthly_rate * (1 + monthly_rate) ** tenure_months / \
          ((1 + monthly_rate) ** tenure_months - 1)
    return round(emi, 2)
```

---

## Backward Compatibility

The loan tables are optional and do not affect existing functionality:

1. Users without loan data continue using the 5-factor model
2. Default metric values used when no loan history exists:
   - loan_diversity_score: 50 (neutral)
   - payment_history_score: 70 (neutral for new loans)
   - loan_maturity_score: 50 (neutral)
3. Financial health score calculation handles missing loan data gracefully

---

## Next Steps

After database setup:

1. ✅ Database schema created
2. ⏭️ Implement Loan_History_System service (Task 2)
3. ⏭️ Implement Loan_Metrics_Engine service (Task 3)
4. ⏭️ Create API endpoints (Task 6)
5. ⏭️ Build frontend components (Tasks 9-12)

---

## Support

For issues or questions:
- Check migration logs in `backend/misc/`
- Run verification script: `python verify_loan_tables.py`
- Review database utilities: `backend/db_utils.py`

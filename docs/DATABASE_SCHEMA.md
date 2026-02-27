# SmartFin - Database Schema Documentation

**Date:** February 27, 2026  
**Database:** SQLite (auth.db)  
**Status:** Current Implementation

---

## Overview

SmartFin uses SQLite with **7 main tables** for data persistence. Financial health scores are **NOT stored** in the database but calculated on-the-fly using the ML model.

---

## Database Tables

### 1. users
**Purpose:** User authentication and account management

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone TEXT,
    email_verified INTEGER DEFAULT 0,
    email_verification_token TEXT,
    email_verification_expires TEXT,
    created_at TEXT NOT NULL
)
```

**Columns:**
- `id` - Unique user identifier
- `username` - Unique username for login
- `password_hash` - Bcrypt hashed password
- `phone` - User phone number
- `email_verified` - Email verification status (0/1)
- `email_verification_token` - Token for email verification
- `email_verification_expires` - Token expiration time
- `created_at` - Account creation timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `username`

---

### 2. password_reset_tokens
**Purpose:** Manage password reset requests

```sql
CREATE TABLE password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    reset_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

**Columns:**
- `id` - Token identifier
- `user_id` - Reference to user
- `reset_code` - Unique reset code
- `created_at` - Token creation time
- `expires_at` - Token expiration time
- `used` - Whether token was used (0/1)

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id`
- INDEX on `user_id`
- INDEX on `reset_code`

---

### 3. users_profile
**Purpose:** Store user profile information

```sql
CREATE TABLE users_profile (
    user_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 18 AND age <= 120),
    location TEXT NOT NULL,
    risk_tolerance INTEGER CHECK (risk_tolerance >= 1 AND risk_tolerance <= 10),
    profile_picture_url TEXT,
    notification_preferences TEXT DEFAULT '{"email": true, "push": false, "in_app": true, "frequency": "daily"}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

**Columns:**
- `user_id` - Reference to user (PRIMARY KEY)
- `name` - User's full name
- `age` - User's age (18-120)
- `location` - User's location
- `risk_tolerance` - Risk tolerance level (1-10)
- `profile_picture_url` - URL to profile picture
- `notification_preferences` - JSON with notification settings
- `created_at` - Profile creation time
- `updated_at` - Last update time

**Constraints:**
- Age: 18-120
- Risk tolerance: 1-10

**Indexes:**
- PRIMARY KEY on `user_id`
- FOREIGN KEY on `user_id`
- INDEX on `user_id`

---

### 4. financial_goals
**Purpose:** Track user financial goals

```sql
CREATE TABLE financial_goals (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    goal_type TEXT NOT NULL CHECK (goal_type IN ('short-term', 'long-term')),
    target_amount REAL NOT NULL CHECK (target_amount > 0),
    target_date TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users_profile(user_id) ON DELETE CASCADE
)
```

**Columns:**
- `id` - Unique goal identifier
- `user_id` - Reference to user
- `goal_type` - Type: short-term or long-term
- `target_amount` - Target amount (>0)
- `target_date` - Target completion date
- `priority` - Priority: low, medium, high
- `status` - Status: active, completed, cancelled
- `description` - Goal description
- `created_at` - Goal creation time
- `updated_at` - Last update time

**Constraints:**
- Goal type: short-term, long-term
- Priority: low, medium, high
- Status: active, completed, cancelled
- Target amount: >0

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id`
- INDEX on `user_id`
- INDEX on `priority`
- INDEX on `status`

---

### 5. loans
**Purpose:** Store loan records and details

```sql
CREATE TABLE loans (
    loan_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    loan_type TEXT NOT NULL CHECK (loan_type IN ('personal', 'home', 'auto', 'education')),
    loan_amount REAL NOT NULL CHECK (loan_amount > 0),
    loan_tenure INTEGER NOT NULL CHECK (loan_tenure > 0),
    monthly_emi REAL NOT NULL CHECK (monthly_emi > 0),
    interest_rate REAL NOT NULL CHECK (interest_rate >= 0 AND interest_rate <= 50),
    loan_start_date TEXT NOT NULL,
    loan_maturity_date TEXT NOT NULL,
    default_status INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

**Columns:**
- `loan_id` - Unique loan identifier
- `user_id` - Reference to user
- `loan_type` - Type: personal, home, auto, education
- `loan_amount` - Principal amount (>0)
- `loan_tenure` - Tenure in months (>0)
- `monthly_emi` - Monthly EMI (>0)
- `interest_rate` - Interest rate % (0-50)
- `loan_start_date` - Loan start date
- `loan_maturity_date` - Loan maturity date
- `default_status` - Default status (0/1)
- `created_at` - Record creation time
- `updated_at` - Last update time
- `deleted_at` - Soft delete timestamp

**Constraints:**
- Loan type: personal, home, auto, education
- Loan amount: >0
- Loan tenure: >0
- Monthly EMI: >0
- Interest rate: 0-50%

**Indexes:**
- PRIMARY KEY on `loan_id`
- FOREIGN KEY on `user_id`
- INDEX on `user_id`
- INDEX on `loan_type`
- INDEX on `default_status`
- INDEX on `deleted_at`

---

### 6. loan_payments
**Purpose:** Track loan payment history

```sql
CREATE TABLE loan_payments (
    payment_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    payment_date TEXT NOT NULL,
    payment_amount REAL NOT NULL CHECK (payment_amount > 0),
    payment_status TEXT NOT NULL CHECK (payment_status IN ('on-time', 'late', 'missed')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
)
```

**Columns:**
- `payment_id` - Unique payment identifier
- `loan_id` - Reference to loan
- `payment_date` - Payment date
- `payment_amount` - Payment amount (>0)
- `payment_status` - Status: on-time, late, missed
- `created_at` - Record creation time
- `updated_at` - Last update time

**Constraints:**
- Payment amount: >0
- Payment status: on-time, late, missed

**Indexes:**
- PRIMARY KEY on `payment_id`
- FOREIGN KEY on `loan_id`
- INDEX on `loan_id`
- INDEX on `payment_date`
- INDEX on `payment_status`

---

### 7. loan_metrics
**Purpose:** Cache calculated loan metrics for performance

```sql
CREATE TABLE loan_metrics (
    user_id INTEGER PRIMARY KEY,
    loan_diversity_score REAL CHECK (loan_diversity_score >= 0 AND loan_diversity_score <= 100),
    payment_history_score REAL CHECK (payment_history_score >= 0 AND payment_history_score <= 100),
    loan_maturity_score REAL CHECK (loan_maturity_score >= 0 AND loan_maturity_score <= 100),
    payment_statistics TEXT,
    loan_statistics TEXT,
    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

**Columns:**
- `user_id` - Reference to user (PRIMARY KEY)
- `loan_diversity_score` - Loan diversity score (0-100)
- `payment_history_score` - Payment history score (0-100)
- `loan_maturity_score` - Loan maturity score (0-100)
- `payment_statistics` - JSON with payment stats
- `loan_statistics` - JSON with loan stats
- `calculated_at` - Last calculation time

**Constraints:**
- Scores: 0-100

**Indexes:**
- PRIMARY KEY on `user_id`
- FOREIGN KEY on `user_id`

---

## Important: Financial Scores NOT Stored

**Financial health scores are NOT persisted in the database.**

### Why?
1. **Real-time Calculation** - Scores are calculated on-the-fly using the ML model
2. **Always Current** - Reflects latest user data
3. **No Storage Overhead** - Reduces database size
4. **Flexibility** - Can update scoring logic without data migration
5. **Performance** - Avoids stale data issues

### How Scores Are Generated
```
User Request (POST /api/predict)
    ↓
Extract financial data from request
    ↓
Load ML model
    ↓
Prepare features
    ↓
model.predict(features)
    ↓
Return score in response
```

### Score Response Example
```json
{
    "score": 79.2,
    "classification": "Very Good",
    "patterns": {...},
    "guidance": {...},
    "anomalies": [...],
    "investments": {...},
    "model_info": {
        "model_type": "8-factor enhanced",
        "accuracy": "95.85%",
        "average_error": "±1.0 points"
    }
}
```

---

## Database Relationships

```
users (1) ──────────────────────── (N) users_profile
  │
  ├─────────────────────────────── (N) password_reset_tokens
  │
  ├─────────────────────────────── (N) loans
  │                                  │
  │                                  └─ (N) loan_payments
  │
  └─────────────────────────────── (1) loan_metrics

users_profile (1) ────────────────── (N) financial_goals
```

---

## Query Examples

### Get User Profile
```sql
SELECT * FROM users_profile WHERE user_id = ?
```

### Get User Loans
```sql
SELECT * FROM loans WHERE user_id = ? AND deleted_at IS NULL
```

### Get Payment History
```sql
SELECT * FROM loan_payments 
WHERE loan_id = ? 
ORDER BY payment_date DESC
```

### Get Financial Goals
```sql
SELECT * FROM financial_goals 
WHERE user_id = ? AND status = 'active'
ORDER BY priority DESC
```

### Get Loan Metrics
```sql
SELECT * FROM loan_metrics WHERE user_id = ?
```

---

## Performance Considerations

### Indexes
- All foreign keys are indexed
- Status columns are indexed for filtering
- Date columns are indexed for range queries
- User ID is indexed for fast lookups

### Query Optimization
- Use indexes for WHERE clauses
- Avoid SELECT * when possible
- Use LIMIT for pagination
- Consider denormalization for frequently accessed data

### Scaling
- Archive old payments (>2 years)
- Partition large tables by user_id
- Use database replication for read scaling
- Implement caching layer (Redis)

---

## Backup & Recovery

### Backup Strategy
- Daily automated backups
- Point-in-time recovery capability
- Off-site backup storage
- Regular backup testing

### Recovery Procedures
- Restore from latest backup
- Verify data integrity
- Test in staging environment
- Document recovery time

---

## Security

### Data Protection
- Password hashing (bcrypt)
- Foreign key constraints
- Soft deletes (deleted_at)
- Audit timestamps (created_at, updated_at)

### Access Control
- User isolation (user_id filtering)
- Role-based access (recommended)
- API authentication (JWT)
- Input validation

---

## Summary

| Table | Purpose | Records | Indexes |
|-------|---------|---------|---------|
| users | Authentication | ~1000s | 2 |
| password_reset_tokens | Password reset | ~100s | 2 |
| users_profile | User profiles | ~1000s | 1 |
| financial_goals | Goals tracking | ~10000s | 3 |
| loans | Loan records | ~10000s | 4 |
| loan_payments | Payment history | ~100000s | 3 |
| loan_metrics | Metrics cache | ~1000s | 1 |

**Total Tables:** 7  
**Total Indexes:** 16  
**Database Type:** SQLite  
**File:** auth.db

---

**Document Status:** Complete  
**Last Updated:** February 27, 2026

# SmartFin — Agent Context File
> **Last Updated:** 2026-10-02
> **Purpose:** Master context document for any AI agent or IDE working on this project.
> Always read this file first before making any changes. Always update the relevant sections after completing work — and always update it again at the end of a session or after any significant change, even if the session isn't "done" with its broader task.

---

## 1. Project Overview

**SmartFin** is a personal finance management web application built as a portfolio/academic project. The goal is to demonstrate real, interview-worthy ML modules rather than fake heuristic models.

- **Stack:** Flask (Python) backend + React (Vite) frontend
- **Database:** SQLite (`auth.db`)
- **Auth:** Flask-JWT-Extended (Bearer tokens)
- **Port:** Backend → `5000`, Frontend (dev) → `5173`
- **Target Audience:** Students and early-career professionals in India
- **Elevator Pitch:** SmartFin helps users track money behavior, evaluate financial health, plan goals/retirement, and receive actionable recommendations.

---

## 2. How to Run

### Python Environment
The project `.venv` references Python 3.13 which is **no longer installed**. Use `C:\Python314\python.exe` directly (resolves as `python` from PATH).

```bash
# Backend
cd backend
python app.py          # starts Flask on port 5000

# Frontend (dev)
cd frontend
npm run dev            # Vite on port 5173

# Frontend (production build)
cd frontend
npm run build

# Quick launch (opens both)
START_SMARTFIN.bat     # from workspace root — spawns both terminals + browser
```

> **Important:** Flask and all backend packages are installed in the user site-packages: `C:\Users\saumy\AppData\Roaming\Python\Python314\site-packages`. Do NOT activate `.venv` — it is broken.

### Installed Backend Packages (Python 3.14)
- `flask`, `flask-cors`, `flask-jwt-extended`, `waitress`, `werkzeug`
- `scikit-learn==1.9.1`, `xgboost==3.4.1`, `scipy==1.18.1`
- `numpy`, `pandas`, `joblib`, `boto3`, `twilio`, `requests`, `python-dotenv`
- `yfinance` (Portfolio Optimizer real data), `pytest==8.3.4` (installed 2026-09-30; was in requirements.txt but missing)
- `marshmallow` **4.3.1** is installed even though requirements.txt used to pin 3.23.2. The pin is now `>=3.23.2,<5` and validators are written to work on both (see §15 #27). Installed versions generally drift ahead of `requirements.txt` (e.g. scikit-learn 1.9.1 vs pinned 1.8.0), so check `pip show <pkg>` before assuming the pinned version is what runs.

---

## 3. Directory Structure

> **Branch status (2026-10-02):** `refactor/app-blueprints` and `feature/portfolio-real-data` are both merged into `main`; the layout below is `main`.

```
smartfin-copy/
├── backend/
│   ├── app.py                          ← Flask app factory — config, CORS, DB init, blueprint registration ONLY (393 lines, zero @app.route left)
│   ├── db_core.py                      ← Shared SQLite helpers (get_db, execute_query, row_to_dict, rows_to_list) used by every blueprint
│   ├── auth.db                         ← SQLite database (users, expenses, loans, goals, etc.)
│   ├── auth/api.py                     ← Blueprint: register/login/refresh/protected, email verification, password reset, Twilio OTP (16 routes)
│   ├── profile_management/api.py       ← Blueprint: profile CRUD, picture upload/delete, goals CRUD (10 routes). Named _management to avoid shadowing stdlib `profile`
│   ├── budget/
│   │   ├── api.py                      ← Blueprint: monthly budget + expenses CRUD, summaries (8 routes)
│   │   └── service.py                  ← Shared budget helpers (build_budget_summary, etc.) — also used by legacy_scorer and chat_agent
│   ├── loans/api.py                    ← Blueprint: loan CRUD, payment recording/history, cached loan metrics (9 routes)
│   ├── chat/
│   │   ├── api.py                      ← Blueprint: AI chat agent endpoint + session list/history/rename/delete/clear (6 routes)
│   │   └── service.py                  ← Session-id scoping, title generation, conversation persistence
│   ├── calculators/api.py              ← Blueprint: SIP + lumpsum calculators (pure math, no DB/auth)
│   ├── legacy_scorer/
│   │   ├── model.py                    ← Loads enhanced_model.pkl at import time (model, feature_names, model_metadata)
│   │   ├── service.py                  ← classify_score, analyze_spending_patterns, generate_guidance, detect_anomalies, suggest_investments, run_prediction_analysis
│   │   └── api.py                      ← Blueprint: /, /api/predict, /api/predict/from-budget, /api/whatif, /api/model-info
│   ├── financial_health_scorer.py      ← OLD standalone scorer module — KEPT (not removed), rule-based heuristics. Distinct from legacy_scorer/ package above
│   ├── loan_metrics_engine.py          ← Loan EMI/amortization calculations
│   ├── loan_history_service.py         ← Loan CRUD business logic
│   ├── loan_data_serializer.py         ← Loan response formatting
│   ├── chat_agent.py                   ← AWS Bedrock (Nova model) chat agent with tool-calling. `execute_tool()` lazily imports model/scoring helpers from `legacy_scorer.model`/`legacy_scorer.service` and budget helpers from `budget.service` — update these imports if those modules move again
│   ├── guidance_engine.py              ← Rule-based + optional AI financial guidance
│   ├── goals_service.py                ← Goals CRUD logic
│   ├── profile_service.py              ← User profile management
│   ├── risk_assessment_service.py      ← Risk scoring engine
│   ├── twilio_service.py               ← SMS/OTP integration
│   ├── validation_schemas.py           ← Marshmallow input validation — has a known bug, see §14 item 8
│   ├── db_utils.py                     ← Loan-table-specific DB helpers (separate from db_core.py). Any SQL that interpolates a table name must go through `_safe_table_identifier()` (allowlist: `LOAN_TABLES`)
│   ├── retirement_planning/            ← Isolated domain package for retirement workflows
│   │   ├── api.py                      ← Blueprint at /api/retirement/
│   │   └── migrations.py              ← Creates retirement DB tables on startup
│   ├── portfolio_optimizer/            ← ✅ ML Module #1 (Markowitz + XGBoost) on REAL market data, 9 assets
│   │   ├── api.py                      ← Flask Blueprint at /api/portfolio/ (every response carries `data_source`)
│   │   ├── fetch_real_data.py          ← Real data: NSE indices/ETFs (yfinance), liquid-fund NAV (mfapi.in), COMEX silver×USD/INR; cleans splits/bad ticks
│   │   ├── data_loader.py              ← Loads returns; shrunk expected returns + weekly covariance (build_engine_inputs); synthetic fallback only if never fetched
│   │   ├── return_predictor.py         ← Per-asset XGBoost; predict() shrinks toward historical mean by out-of-fold R²
│   │   ├── markowitz_engine.py         ← SLSQP mean-variance optimizer, 35% per-asset cap (FD exempt), GMV-up frontier
│   │   ├── personalizer.py             ← Adjusts allocation based on user EMI/loans/goals/savings from DB
│   │   ├── train_model.py              ← Training script (`--refresh-data` re-fetches first)
│   │   ├── data/asset_returns.csv      ← REAL monthly returns (per-asset full history, NaN before inception)
│   │   ├── data/asset_returns_weekly.csv ← REAL weekly returns, used for the covariance matrix
│   │   ├── data/data_source.json       ← Manifest: tickers, per-asset date ranges, fetch time, FD caveat
│   │   └── models/                     ← return_predictor.pkl (models + scalers + blend weights) + model_metadata.json
│   └── nudge_engine/                   ← ✅ ML Module #2 (Isolation Forest)
│       ├── api.py                      ← Flask Blueprint at /api/nudges/
│       ├── feature_builder.py          ← Builds weekly expense feature matrix from DB
│       ├── anomaly_detector.py         ← Per-user Isolation Forest + RF budget-bust classifier
│       ├── nudge_generator.py          ← Converts anomaly scores → actionable nudge messages
│       └── demo_seeder.py              ← Seeds 16 weeks of realistic test expense data
├── frontend/src/
│   ├── App.jsx                         ← React Router routes (all behind ProtectedRoute)
│   ├── components/
│   │   ├── PortfolioOptimizer.jsx      ← ✅ NEW: Portfolio UI (risk slider, donut, frontier)
│   │   ├── PortfolioOptimizer.css      ← Glassmorphism dark design
│   │   ├── NudgeEngine.jsx             ← ✅ NEW: Nudge UI (anomaly cards, weekly timeline)
│   │   ├── NudgeEngine.css             ← Severity-colored card design
│   │   ├── Sidebar.jsx                 ← Nav — has Portfolio + Nudge Engine items
│   │   ├── MainDashboard.jsx           ← OLD dashboard with ScoreDisplay (still active)
│   │   ├── RetirementPlanner.jsx       ← Main orchestrator (13 retirement components total)
│   │   ├── ChatAgent.jsx               ← Chat UI — supports tool widgets (score, loans, goals)
│   │   └── ...                         ← All other existing components UNTOUCHED
│   └── services/api.js                 ← Axios client — has generic api.get() / api.post()
├── data/
│   ├── combined_dataset.csv            ← 52,424 records for health scorer training
│   ├── enhanced_model.pkl              ← Re-trained GradientBoosting (sklearn 1.9.1, R²=95.88%)
│   └── train_enhanced_model.py         ← Script to retrain enhanced_model.pkl
├── AGENTS.md                           ← ← THIS FILE — update after every change
└── docs/                               ← ← DELETED — all context consolidated here
```

---

## 4. Key Design Decisions

### What Was Changed vs What Was Kept

| Module | Status | Reason |
|---|---|---|
| `financial_health_scorer.py` | **KEPT** | Demoted, not deleted — backward compatible |
| `/api/predict` endpoint | **KEPT** | Old health score endpoint still live |
| `MainDashboard.jsx` ScoreDisplay | **KEPT** | Old dashboard still works as-is |
| `portfolio_optimizer/` | **NEW — Added** | Real ML: Markowitz + XGBoost |
| `nudge_engine/` | **NEW — Added** | Real ML: Isolation Forest |
| `PortfolioOptimizer.jsx` | **NEW — Added** | Route: `/portfolio` |
| `NudgeEngine.jsx` | **NEW — Added** | Route: `/nudges` |

### Frontend State Management
- **No Redux** — uses React `useState` hooks only (listed in package.json but not used)
- **Global state** lives in `AppContent` in `App.jsx`: `user`, `authLoading`, `loading`, `result`, `currentData`, `error`
- **Auth persistence:** Token stored as `sf_token`, userId as `userId`, email as `userEmail` in `localStorage`
- **State flow:** `handleAuth()` → sets user + token → navigate to `/dashboard`. `handleLogout()` → clears everything → navigate to `/`
- **ProtectedRoute** checks `api.getStoredToken()` + `localStorage.userId`; if no user but token exists, restores state from localStorage before redirecting

---

## 5. ML Module Details

### Legacy Module: Financial Health Scorer (OLD — still live)

**Files:** `backend/financial_health_scorer.py`, `backend/loan_metrics_engine.py`  
**Endpoints:** `/api/predict`, `/api/whatif`, `/api/model-info`, `/api/predict/from-budget`

**How it works (important for interviews):**
- An 8-factor rule-based heuristic formula generates synthetic training labels (not real financial data labels)
- A GradientBoosting Regressor learns to replicate those rule-based labels (R²=95.88%, MAE=1.03 points)
- The model *does* generalize, but it's learning human-defined heuristics, not discovering patterns in ground truth — this is the honest description
- Model config: `GradientBoostingRegressor(n_estimators=200, max_depth=10, learning_rate=0.1, random_state=42)`

**8-Factor Score Formula:**
```
Score = (Savings × 0.25) + (Debt × 0.20) + (Expense × 0.18) + (Balance × 0.12)
       + (LoanDiversity × 0.10) + (LifeStage × 0.08) + (PaymentHistory × 0.05) + (LoanMaturity × 0.02)
```

**Factor thresholds:**
- Savings: ≥30% income → 100; ≥20% → 85; ≥10% → 70; ≥5% → 50; else 30
- Debt (EMI): ≤10% income → 100; ≤20% → 85; ≤30% → 65; ≤40% → 45; else 25
- Expense: ≤50% income → 100; ≤65% → 85; ≤80% → 70; ≤90% → 50; else 30

**Feature importance:** EMI 53.7% · Savings 18.0% · Income 13.7% · Expenses 12.9% · Age 1.2%

**Training data:** `data/combined_dataset.csv` — 52,424 records (32,424 global + 20,000 India personal finance)
- Features mapped: income→Income, emi→Loan_Repayment, savings→Disposable_Income
- **Financial health scores are NOT stored in DB** — calculated on-the-fly per request

**Score classification:**
| Score | Category |
|---|---|
| 80-100 | Excellent 🌟 |
| 65-79 | Very Good ✨ |
| 50-64 | Good 👍 |
| 35-49 | Average ⚠️ |
| 0-34 | Poor 🚨 |

**Retrain if pkl breaks:**
```bash
python data/train_enhanced_model.py  # from workspace root
```

---

### Module 1: Portfolio Optimizer (real market data, 9-asset universe)

**Files:** `backend/portfolio_optimizer/`
**API Blueprint:** `/api/portfolio/` (registered in `app.py`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/portfolio/optimize` | POST | Optimal allocation for an amount + risk score (1–10), personalized to the user's loans/goals/savings |
| `/api/portfolio/frontier` | GET | Efficient frontier points + Min-Risk (GMV) and Best-Sharpe markers |
| `/api/portfolio/model-info` | GET | XGBoost metrics, blend weights, feature importance + full data-source manifest |
| `/api/portfolio/whatif` | POST | Compare allocations across several risk scores |

Every response carries `data_source` (`real_historical` vs `synthetic_fallback`).

**Pipeline (offline, run manually):** `fetch_real_data.py` → `data/asset_returns.csv` (monthly), `data/asset_returns_weekly.csv` (weekly), `data/data_source.json` (manifest) → `train_model.py` → `models/return_predictor.pkl` + `models/model_metadata.json`. Requests never touch the network.

**Data sources — each asset uses its longest clean real series (as of 2026-10-02 fetch):**
| Asset | Category | Source | History |
|---|---|---|---|
| Equity Large-Cap | Equity | `^NSEI` — NIFTY 50 index | 2007-10 → (228 mo) |
| Equity Mid-Cap | Equity | `^NSEMDCP50` — NIFTY MIDCAP 50 index | 2007-10 → (228 mo) |
| Equity Small-Cap | Equity | `NIFTYSMLCAP250.NS` — NIFTY SMALLCAP 250 index | 2005-05 → (257 mo) |
| International Equity | Equity | `MON100.NS` — Motilal Oswal Nasdaq-100 ETF (INR) | 2011-04 → (186 mo) |
| Short-Term Debt | Debt | mfapi.in scheme 100851 — Nippon India Liquid Fund, Growth NAV | 2006-05 → (245 mo) |
| Gold | Precious Metals | `GOLDBEES.NS` — Nippon India Gold BeES ETF | 2009-02 → (212 mo) |
| Silver | Precious Metals | `SI=F` × `USDINR=X` — COMEX silver futures in INR | 2004-01 → (273 mo) |
| REIT | Real Estate | `EMBASSY.NS` — Embassy Office Parks REIT | 2019-05 → (89 mo) |
| Fixed Deposit | FD / Cash | — flat 6.5%/yr assumption (FDs aren't traded) | full range |

- **Why indices / NAV / composite instead of ETFs:** the Mid-Cap and Small-Cap ETFs (`MIDCAPETF.NS`, `SMALLCAP.NS`) listed in 2024 and the Silver ETF in 2022. With 2–4.6 years of history, the 95% range of the true mean return was about ±24 points (Mid-Cap: −19%..+29%/yr), so the number was meaningless. The indices they track go back to 2005–07. `LIQUIDBEES.NS` pays its yield out as daily dividends, so its price barely moves and showed 3.0%/yr instead of ~6.8%. Yahoo's LIQUIDBEES series is also broken (first close ₹589 vs ₹1000 face value, NaN last close). A growth-plan NAV accumulates the yield.
- **Data cleaning in `fetch_real_data.py`:** (1) the liquid-fund NAV is rescaled ~100× once in 2012 (₹10 → ₹1000 units), so any daily move >50% is dropped; (2) Yahoo leaves unit splits unadjusted for a day or two (GOLDBEES 1:100 in Dec 2019, MON100 1:10 in Jun 2021), so prices >3× away from their 5-day median are dropped; (3) the in-progress month/week is cut so a 1-day partial period isn't treated as a full return.
- Gaps before an asset's history begins are left as NaN (never padded). pandas `mean`/`cov` skip NaN.
- The synthetic Gaussian generator in `data_loader.py` remains only as an offline fallback if real data was never fetched; `get_data_source_info()` reports which is in use.

**How the optimizer's inputs are estimated (`data_loader.build_engine_inputs`):**
- **Expected returns are shrunk toward a risk-based prior** (`estimate_annual_returns`): `prior = 6.5% + 0.3 × vol`, `w = (1/SE²)/(1/SE² + 1/5%²)` with `SE = vol/√years`, `expected = w × sample_mean + (1 − w) × prior`. Short or volatile histories lean on the prior; precise ones keep their own mean. Last run: International 24.7% → 18.2%, Silver 18.5% → 16.9%, Large-Cap 10.1% → 11.3%, Debt 6.8% unchanged (w ≈ 1). Fixed Deposit is exempt. Constants `RISK_FREE_RATE`, `PRIOR_SHARPE`, `PRIOR_SD` are in `data_loader.py`.
- **Covariance from weekly returns** (`estimate_annual_cov`, ×52), pairwise over overlapping weeks: ~4.3× more observations than monthly. Weekly rather than daily because Silver is priced off US futures; daily returns across different market hours bias correlations toward zero. Weekly vs monthly agree: vols within a few points, Gold–Silver correlation 0.56 vs 0.62.

**Model:**
- XGBoost Regressor trained **independently per asset on its own history** (a shared row-aligned matrix bottlenecked everything to the newest asset's window). Per-asset `TimeSeriesSplit`, `n_splits` 2–5 scaled to rows. Assets under 20 usable rows are skipped; Fixed Deposit is skipped as a constant target.
- Last training: **8/9 assets trained** (only FD skipped), overall out-of-fold R² = **−0.47**. Every model is worse than its own historical mean, a genuine Efficient-Market result on real prices.
- **Reliability-weighted blend:** `predict()` returns `w × ml + (1 − w) × shrunk_mean` with `w = clip(R², 0, 1) × min(1, months/120)`. All R² < 0, so all `w = 0` and allocations run on shrunk historical means. The UI shows "Historical avg" and "ML influence 0%". `predict(df, raw=True)` gives unblended values.
- **Markowitz (SLSQP):** 35% per-asset cap (`MAX_ASSET_WEIGHT`, FD exempt) on every solve. Covariance jitter scaled to the largest eigenvalue (FD's zero variance makes the matrix singular otherwise). The frontier is swept only from the GMV return up to the max return reachable under the caps (`_max_feasible_return`).
- **Risk-score mapping:** 1–2 → GMV; 3–10 → evenly along the efficient frontier. Risk 9–10 used to map to the Max-Sharpe portfolio, which sits mid-frontier, so "Ultra Aggressive" was less risky than "Aggressive". Max-Sharpe is now only a chart marker.
- **Resulting behavior (last run):** risk 1 → 6.5%/yr at 0.3% vol (FD 65% + liquid debt 35%); risk 5 → 11.1% at 5.9% vol (debt 35%, gold 22%, international 17%, FD 13%, small-cap 10%); risk 10 → 16.8% at 15.4% vol (small-cap 35%, international 35%, silver 23%, gold 7%). Volatility rises monotonically with risk score. Large-Cap and Mid-Cap usually get 0%: on this data Small-Cap + International dominate them on risk/return, and they're highly correlated with Small-Cap (0.85+).
- **Personalization** (`personalizer.py`) then shifts weight toward FD/debt for high EMI (>40% / >25% of income), 2+ active loans, a goal within 12 / 36 months, or savings <5% of income. Data is read from `monthly_budgets`, `loans`, `financial_goals`, `expense_entries`.

**Fetching real data / retraining:**
```bash
cd backend
python -X utf8 portfolio_optimizer/fetch_real_data.py              # refresh data only (needs internet: Yahoo + mfapi.in)
python -X utf8 portfolio_optimizer/train_model.py                  # train on whatever's cached
python -X utf8 portfolio_optimizer/train_model.py --refresh-data   # fetch + train in one step
```

---

### Module 2: Behavioral Nudge Engine (NEW — Real ML)

**Files:** `backend/nudge_engine/`  
**API Blueprint:** `/api/nudges/` (registered in `app.py`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/nudges/scan` | POST | Run anomaly scan for current user |
| `/api/nudges/history` | GET | Get past nudge history |
| `/api/nudges/patterns` | GET | Get weekly spending patterns |

**Dataset:** Live user transaction data from `auth.db` (`expenses` + `budget_categories` tables)

**Model:**
- Isolation Forest (200 estimators, 15% contamination) — per-user, trained on that user's own spending history
- Random Forest Classifier for budget-bust probability (requires ≥12 weeks of data)
- Features: weekly spend by category, income-normalized ratios, 4-week rolling averages, surge ratios

**Demo Seeding:**
```bash
cd backend
python nudge_engine/demo_seeder.py --user-id 1 --weeks 16
```
Seeds 16 weeks of realistic expense data with anomalous spikes at weeks 3 and 10.

---

## 6. Full Database Schema (SQLite `backend/auth.db`)

> Financial health scores are NOT stored — calculated on-the-fly per request.

### Core Auth Tables
```sql
users (id PK, username UNIQUE, password_hash, phone, email_verified, email_verification_token, email_verification_expires, created_at)
password_reset_tokens (id PK, user_id FK→users, reset_code, created_at, expires_at, used)
```

### Profile & Goals
```sql
users_profile (user_id PK FK→users, name, age CHECK(18-120), location, risk_tolerance CHECK(1-10), profile_picture_url, notification_preferences JSON, created_at, updated_at)
financial_goals (id PK UUID, user_id FK→users_profile, goal_type CHECK(short-term|long-term), target_amount CHECK(>0), target_date, priority CHECK(low|medium|high), status CHECK(active|completed|cancelled), description, created_at, updated_at)
```

### Budget & Expenses
```sql
monthly_budgets (id PK UUID, user_id FK, month TEXT 'YYYY-MM', monthly_income, planned_savings, created_at, updated_at)
budget_categories (id PK UUID, budget_id FK→monthly_budgets, category, planned_amount, created_at, updated_at)
expense_entries (id PK UUID, user_id FK, budget_id FK→monthly_budgets (nullable), expense_date TEXT 'YYYY-MM-DD', category, amount, note, created_at, updated_at)
-- NOTE: there is no users.income / users.emi / users.savings. Income lives in monthly_budgets,
-- EMI is SUM(loans.monthly_emi) over active loans, savings = income - that month's expense_entries.
-- Goals live in financial_goals (not 'goals'). Verified with PRAGMA table_info on 2026-10-02.
```

### Loans
```sql
-- 'active' loan = deleted_at IS NULL AND loan_maturity_date >= today; there is no loans.status column
loans (loan_id PK UUID, user_id FK→users, loan_type CHECK(personal|home|auto|education), loan_amount CHECK(>0), loan_tenure CHECK(>0), monthly_emi CHECK(>0), interest_rate CHECK(0-50), loan_start_date, loan_maturity_date, default_status, created_at, updated_at, deleted_at)
loan_payments (payment_id PK UUID, loan_id FK→loans, payment_date, payment_amount CHECK(>0), payment_status CHECK(on-time|late|missed), created_at, updated_at)
loan_metrics (user_id PK FK, loan_diversity_score(0-100), payment_history_score(0-100), loan_maturity_score(0-100), payment_statistics JSON, loan_statistics JSON, calculated_at) ← caching table
```

### Retirement (4 tables, created at startup by `RetirementPlanningMigrations`)
```sql
retirement_plans     ← input params + calculation results JSON + readiness assessment
retirement_scenarios ← what-if scenarios per plan, modified params + results JSON
retirement_action_plans ← prioritized recommendations per plan
retirement_plan_history  ← plan version snapshots for comparison
```

### Chat
```sql
chat_sessions (session_id PK, user_id FK, conversation_json, title, created_at, updated_at)
```

---

## 7. Full API Endpoint Map

### Financial Health (Legacy Scorer)
- `POST /api/predict` — predict score from form data
- `POST /api/predict/from-budget` — predict from budget module data
- `POST /api/whatif` — compare two scenarios, returns score delta
- `GET /api/model-info` — model metadata

### Auth & Account
- `POST /register`, `POST /login`, `GET /protected`, `POST /refresh`
- `POST /forgot-password`, `POST /verify-reset-code`, `POST /reset-password`
- `POST /update-phone`, `GET /get-phone`
- `POST /send-email-verification`, `POST /verify-email`, `GET /check-email-verification`
- `POST /send-otp`, `POST /verify-otp`, `POST /register-with-otp`, `POST /forgot-password-otp`

### Profile & Goals
- `POST /api/profile/create`, `GET /api/profile`, `PUT /api/profile/update`
- `POST /api/profile/upload-picture`, `DELETE /api/profile/delete-picture`
- `POST /api/profile/goals`, `GET /api/profile/goals`
- `PUT /api/profile/goals/<goal_id>`, `DELETE /api/profile/goals/<goal_id>`

### Budget
- `POST /api/budget/monthly`, `GET /api/budget/monthly`
- `POST /api/budget/expenses`, `GET /api/budget/expenses`
- `PUT /api/budget/expenses/<id>`, `DELETE /api/budget/expenses/<id>`
- `GET /api/budget/summary`, `GET /api/budget/analysis-input`

### Loans
- `POST /api/loans`, `GET /api/loans/user/<user_id>`, `GET /api/loans/<loan_id>`
- `PUT /api/loans/<loan_id>`, `DELETE /api/loans/<loan_id>`
- `POST /api/loans/<loan_id>/payments`, `GET /api/loans/<loan_id>/payments`
- `DELETE /api/loans/<loan_id>/payments/<payment_id>`
- `GET /api/loans/metrics/<user_id>`

### Calculators
- `POST /api/sip-calculator`, `POST /api/lumpsum-calculator`

### Retirement (prefix: `/api/retirement`)
- `POST /calculate`, `POST /plans`, `GET /plans/<user_id>`, `GET /plans/<plan_id>`
- `PUT /plans/<plan_id>`, `DELETE /plans/<plan_id>`
- `POST /scenarios`, `GET /scenarios/<plan_id>`, `PUT /scenarios/<scenario_id>`, `DELETE /scenarios/<scenario_id>`
- `POST /scenarios/compare`
- `POST /readiness`, `GET /recommendations/<plan_id>`, `POST /export`

### Portfolio Optimizer (prefix: `/api/portfolio`)
- `POST /optimize`, `GET /frontier`, `GET /model-info`, `POST /whatif`

### Nudge Engine (prefix: `/api/nudges`)
- `POST /scan`, `GET /history`, `GET /patterns`

### Chat
- `POST /api/chat`, `POST /api/chat/clear`, `GET /api/chat/sessions`
- `GET /api/chat/history`, `PUT /api/chat/session/title`, `DELETE /api/chat/session`

---

## 8. Frontend Routes (App.jsx)

| Route | Component | Protected |
|---|---|---|
| `/` | LandingPage | No |
| `/auth` | AuthPage | No |
| `/dashboard` | MainDashboard | Yes |
| `/portfolio` | PortfolioOptimizer | Yes |
| `/nudges` | NudgeEngine | Yes |
| `/budget` | BudgetManager | Yes |
| `/loans` | LoanManagementPage | Yes |
| `/goals` | GoalsManager | Yes |
| `/retirement` | RetirementPlanner | Yes |
| `/sip-calculator` | SIPCalculator | Yes |
| `/profile` | ProfilePage | Yes |
| `/chat` | ChatAgent | Yes |

---

## 9. Retirement Planner — Module Details

**Blueprint:** `/api/retirement/` (isolated package `backend/retirement_planning/`)  
**Integration points:**
- Pulls financial health score (20% weight in readiness) via `IntegrationManager.get_financial_health_score()`
- Pulls user loans (20% debt-burden weight in readiness) via `IntegrationManager.get_user_loans()`
- Pulls goals via `IntegrationManager.get_financial_goals()`
- Caches fetched data with 5-minute TTL

**13 Frontend Components:**
- `RetirementPlanner.jsx` — orchestrator
- `RetirementInputForm.jsx` — validated form
- `RetirementDashboard.jsx` — full dashboard
- `ScenarioComparison.jsx`, `ActionPlanView.jsx`, `GapAnalysisView.jsx`, `GoalIntegrationView.jsx`, `FinancialHealthIntegration.jsx`
- `RetirementGauge.jsx`, `CorpusComparison.jsx`, `SavingsProjection.jsx`, `ReadinessBreakdown.jsx`, `LoanPayoffTimeline.jsx`

**Loan payoff strategies available:** Snowball, Avalanche, Balanced

---

## 10. Chat Agent — Module Details

**File:** `backend/chat_agent.py`  
**Integration:** AWS Bedrock (Nova model)  
**Tool-calling:** The chat agent can call internal backend tools to fetch real user data:
- User profile, budget summary, loan list, goals, SIP/lumpsum projections
**Frontend:** `ChatAgent.jsx` supports dynamic tool widgets inline (score cards, what-if panels, retirement summaries, loan/goal widgets)

---

## 11. Auth & API Calls

- JWT token stored in `localStorage` key: `sf_token`
- Sent as `Authorization: Bearer <token>` via Axios interceptor in `services/api.js`
- Also stored: `userId`, `userEmail` in localStorage for session restore
- All protected backend endpoints use `@jwt_required()` decorator
- Generic helpers: `api.get(path)` and `api.post(path, data)` in `services/api.js`
- 401 interceptor: clears token and redirects to `/auth`

---

## 12. Pending Work (in priority order)

- [x] ~~Fetch real Indian market data via `yfinance` and retrain Portfolio Optimizer XGBoost~~ — done, see §5 Module 1. 9-asset universe, common real overlap 2024-07 to present; re-run `fetch_real_data.py` periodically as newer ETFs accrue history.
- [x] ~~Portfolio Optimizer `ml_predicted` mode producing extreme allocations~~ — done: reliability-weighted blend toward historical mean + 35% per-asset cap (see §5 Module 1)
- [x] ~~Fix `portfolio_optimizer/personalizer.py` DB queries~~ — done 2026-10-02, all 4 rules verified firing on real data (§15 #28)
- [x] ~~Merge `refactor/app-blueprints` and `feature/portfolio-real-data` into `main`~~ — done 2026-10-02 (§15 #26)
- [x] ~~Fix marshmallow bug in `POST /api/profile/goals`~~ — done 2026-10-02 (§15 #27)
- [ ] **Deferred by user (2026-10-02, "I'll come back to this"):** the Portfolio Optimizer's XGBoost return predictor has R² −0.47 and 0% influence, so it currently adds nothing. Plan: (1) replace it with a next-month **volatility** predictor (volatility clustering is genuinely predictable; it feeds the covariance, so ML would actually move allocations); (2) add a **walk-forward backtest** (rebuild yearly on past-only data; compare return/vol/max drawdown vs all-Nifty and 60/40), run with and without the vol model.
- [ ] **NEXT:** audit the Nudge Engine the way the Portfolio Optimizer was audited — does it run on real user data or demo-seeded spikes, does the Isolation Forest result hold up, is anything fabricated or silently broken?
- [ ] Replace `MainDashboard.jsx` health score widget with Portfolio Summary card (optional)
- [ ] Full removal of old scorer — `financial_health_scorer.py`, `ScoreDisplay.jsx`, `/api/predict` (optional)
- [ ] Run `demo_seeder.py` for a real user account to populate Nudge Engine data
- [ ] End-to-end test: login → /portfolio → set amount + risk → verify donut chart renders

### Feature ideas backlog (novelty — saved 2026-10-02, none started)

The project's unique asset is that one app holds a user's **real** spending, loans, goals and investments together. These ideas exploit that:

1. **Personal Inflation Rate** *(top pick)* — weight MOSPI CPI category sub-indices (food, housing, education, transport, …) by the user's own `expense_entries` category shares → "your inflation is 7.8%, not 5.1%", updated monthly. Feeds the retirement planner, goal targets and portfolio real returns, which all currently assume one flat inflation rate.
2. **Goal-Success Probability** — Monte Carlo that resamples the user's *own* monthly spending/savings plus portfolio returns → "73% chance you reach this goal by June; cutting food delivery by ₹1,500/mo raises it to 91%". Uses #1's personal inflation. #1 + #2 together = a "personal financial digital twin": SmartFin models *your* inflation and *your* savings variability, not averages.
3. **Present-Bias Score** — behavioural finance from transaction timing: share of discretionary spend in the 7 days after income lands, balance-drain speed → a per-user impatience score; time nudges to it (e.g. day 2 after payday). Natural novelty angle for the Nudge Engine.
4. **Tax-aware portfolio (India)** — old vs new regime, 80C/ELSS limit, ₹1.25L LTCG exemption harvesting in the optimizer. Practical; less novel since tax calculators exist.

**Standalone app ideas** (not tied to SmartFin's modules; each could be its own app): see [`STANDALONE_APP_IDEAS.md`](STANDALONE_APP_IDEAS.md). These are the No-Cost EMI / BNPL true-cost decoder *(top pick)*, the finfluencer & investment-scam checker (SEBI registry), the loan/insurance fine-print analyzer, and group expense settlement.

---

## 13. Interview / Presentation Talking Points

### The Honest Story on Enhanced Model (R²=95.88%)
> "We use a GradientBoosting Regressor trained on 52,424 records from two Kaggle datasets (global personal finance + India personal finance). The target labels are generated by an 8-factor rule-based formula we designed — savings behavior, debt burden, expense control, life stage, and loan metrics. The model learns to replicate that formula accurately. The key advantage: our scoring is fully transparent and explainable to users, while the ML layer enables fast generalization to new users without running the rule engine."

### Portfolio Optimizer Story
> "The core is Markowitz mean-variance optimization (SLSQP) over 9 Indian asset classes built from real data: NIFTY 50 / Midcap 50 / Smallcap 250 indices, a Nasdaq-100 ETF, a liquid fund's NAV, Gold ETF, COMEX silver in rupees, and a REIT. That's 7 to 23 years each, with Fixed Deposit as the one labeled assumption. Three estimation choices make it robust. First, sample means from short or lucky periods are shrunk toward a risk-based prior, so Silver's 2020s rally or Nasdaq's AI run don't dominate. Second, covariance comes from weekly returns for ~4× more data, weekly rather than daily because silver trades on US hours. Third, there's a 35% per-asset cap. XGBoost predicts next-month returns per asset, and its influence is weighted by its out-of-sample R². Every model scores below zero, so it currently has zero say. That's the Efficient Market Hypothesis showing up honestly on real prices. Along the way we found data problems you only catch by checking: unadjusted stock splits, a liquid ETF whose price ignores its own yield, and a NAV rescaled 100×."

### Nudge Engine Story
> "Isolation Forest runs per-user on their own 16+ week spending history. It doesn't need labeled anomaly data — it learns each user's baseline by itself (unsupervised). A spending week that is very different from that user's personal pattern gets flagged, regardless of whether it's 'expensive' by some global standard."

### Common Viva Q&A
| Question | Strong Answer |
|---|---|
| Why Flask not Django? | Flask gives faster API-centric development with lightweight control for custom ML/business logic |
| Why SQLite? | Zero admin overhead, easy local setup, sufficient for prototyping persistent relational workflows |
| Why GradientBoosting? | Handles non-linear financial relationships, robust to missing data, excellent feature importance analysis |
| How is security handled? | JWT auth, hashed passwords (werkzeug/bcrypt), protected routes, ownership checks, OTP/email verification |
| How do you prevent SQL injection? | Every query with user input uses `?` parameter binding, so values never become SQL. The few dynamically built queries only interpolate fixed column literals or `?` placeholder lists. Table names (which can't be bound) go through an allowlist check, `_safe_table_identifier()` in `db_utils.py`. Inputs are also type-cast (`float`/`int`/`strptime`), categories are allowlisted, and every update/delete is scoped with `AND user_id = ?` |
| How does what-if work? | Backend predicts both current and modified scenarios, returns score delta and impact label |
| How is explainability addressed? | Return classification labels, financial ratios, warnings, and guidance alongside prediction |
| Is this just ML demo? | No — complete user journey: auth, profile, budget, loans, goals, retirement planner, AI chat assistant |

---

## 14. Known Issues / Gotchas

1. **`.venv` is broken** — built against Python 3.13 (no longer installed). Never activate it. Use `python` from PATH (`C:\Python314\python.exe`).
2. **`enhanced_model.pkl` compatibility** — re-serialized 2026-09-21 for sklearn 1.9.1. If a different sklearn version loads the old pkl, it throws `ModuleNotFoundError: No module named _loss`. Fix: run `python data/train_enhanced_model.py` from workspace root.
3. **Windows encoding** — use `python -X utf8` flag for any scripts with emoji characters.
4. **Frontend Vite warning** — `default referenced in default didn't resolve at build time` is benign. Build still succeeds (683 modules, 0 errors).
5. **Two `auth.db` files** — one at workspace root (stale/empty), one at `backend/auth.db`. Flask uses `backend/auth.db`. The root one is the empty one that should be deleted if it reappears.
6. **app.py monolith — RESOLVED, merged to `main` 2026-10-02.** All routes live in blueprints (auth, profile_management, budget, loans, chat, calculators, legacy_scorer) following the retirement_planning/portfolio_optimizer/nudge_engine pattern; `app.py` is ~390 lines of setup/wiring. When moving code in future: grep for lazy `from app import <name>` (e.g. `chat_agent.py`'s `execute_tool()`) — that exact class of bug broke chat mid-refactor and was caught only by calling `/api/chat` on a live server, not by import checks.
7. **`retirement_planning/` integration_manager.py** — imports `financial_health_scorer` internally. Do not delete `financial_health_scorer.py` without updating `integration_manager.py` first.
8. **~~`validation_schemas.py` marshmallow bug~~ — FIXED 2026-10-02.** Marshmallow 4 passes `data_key=` to `@validates` methods; all validators now take `**kwargs` so they run on 3.x and 4.x. Any new `@validates` method needs `**kwargs` too.
9. **~~Personalizer DB queries didn't match `auth.db`~~ — FIXED 2026-10-02.** Fetchers now read `monthly_budgets`, `loans` (not deleted, not matured), `financial_goals`, `expense_entries`. Failures still fall back to "no adjustment" but are logged as `personalizer: ... failed` warnings. If personalization ever seems to do nothing again, grep the server log for that prefix first.
10. **Portfolio Optimizer re-fetch cadence:** the data files are snapshots. Re-run `fetch_real_data.py` + `train_model.py` periodically (needs internet: Yahoo Finance + mfapi.in). REIT is the only short history (2019+); its mean leans on the prior until it accrues more. If Yahoo changes a ticker or mfapi.in is down, `fetch_and_save()` raises and leaves the old CSVs untouched rather than writing partial data.
11. **Windows dev gotchas (from the verification runs):** use `C:\Python314\python.exe` explicitly, because a bare `python3` resolves to the Microsoft Store stub (exit code 49). `/tmp/...` paths inside Python on Windows don't match Git Bash's `/tmp`, so write scratch files to the working dir or the session scratchpad. To stop the dev servers, find the PID with `netstat -ano | grep :5000` and run `taskkill //PID <pid> //F`; `kill %1` doesn't reliably stop the Python child process.
12. **IDE red squiggles on `flask`/`flask_jwt_extended` imports** — the editor's Python language server doesn't know packages live in `C:\Users\saumy\AppData\Roaming\Python\Python314\site-packages` (see item 1). Fixed via `.vscode/settings.json` → `"python.defaultInterpreterPath": "C:\\Python314\\python.exe"`. If squiggles persist, reload the window or run "Python: Select Interpreter" and pick that path manually. Purely cosmetic — doesn't affect running the app.

---

## 15. Problems Faced & Solved (session log)

> Symptom → root cause → fix → how it was caught. Kept so future sessions don't re-debug the same things. Each entry notes the branch its fix lives on.

### Session 2026-09-27/28 — `app.py` → Flask blueprints (branch `refactor/app-blueprints`)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 1 | `app.py` was 3,600+ lines with every route in one file | Organic growth; only retirement/portfolio/nudge used blueprints | Extracted `auth`, `profile_management`, `budget`, `loans`, `chat`, `calculators`, `legacy_scorer` blueprints plus a shared `db_core.py`, one domain per commit. `app.py` → 393 lines, zero `@app.route` | Planned refactor |
| 2 | Circular import risk: blueprints needed `get_db()` from `app.py`, and `app.py` imports the blueprints | DB helpers lived in `app.py` | Moved `get_db`/`execute_query`/`row_to_dict`/`rows_to_list` into `db_core.py`, imported by both sides | Design, before writing code |
| 3 | A `profile/` package would shadow Python's stdlib `profile` module | Name collision | Named it `profile_management/` | Caught before first use |
| 4 | **`POST /api/chat` broke:** `cannot import name '_current_month_string' from 'app'` | `chat_agent.py` does a *lazy* `from app import ...` inside `execute_tool()`. The budget extraction renamed/moved those helpers, and import-time checks never execute that function body | Pointed the import at `budget.service` (and later `legacy_scorer.model`/`.service`) | Only by calling `/api/chat` on a live server, **two commits after it broke**. Lesson: grep for `from app import` across the repo before moving anything, and exercise lazy-import paths, not just `import app` |
| 5 | Old `twilio_verify` import left dangling in `app.py` | Leftover after auth extraction | Removed | Grep during loans extraction |
| 6 | Dead top-level imports (`joblib`, `numpy`, `pandas`, auth helpers…) after every route moved out | Expected end state of the refactor | Removed | Grep of remaining usages |
| 7 | `POST /api/profile/goals` → `validate_future_date() got an unexpected keyword argument 'data_key'` | Marshmallow version mismatch in `validation_schemas.py` | **Fixed 2026-10-02** (see #27). Confirmed pre-existing by reproducing on the pre-refactor commit | Live test of the profile blueprint |
| 8 | Red squiggles on every Flask import in the IDE | Language server can't see user site-packages (the `.venv` is broken) | `.vscode/settings.json` → `python.defaultInterpreterPath` (gitignored, per machine) | User report |

### Session 2026-09-28/29 — Portfolio Optimizer real data (branch `feature/portfolio-real-data`)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 9 | User: results "feel fabricated" | They were. `data_loader.py` generated all "market data" with `np.random.multivariate_normal()` from hand-picked assumptions, undisclosed anywhere | `fetch_real_data.py` pulls real prices via yfinance; `data_source` disclosed in every API response and in the UI | Code read of `data_loader.py` |
| 10 | Reported R² = −0.73 framed as "EMH talking point" | Meaningless: XGBoost was predicting IID noise from rolling stats of the same noise | Retrained on real prices. R² ≈ −0.44 is now a genuine out-of-sample result | Code review |
| 11 | Module felt "basic" (5 assets) | Thin asset menu | 9 assets / 5 categories: added Small-Cap, Nasdaq-100 ETF, Silver, REIT | User request |
| 12 | `NIFTYMID50.NS` (the ticker pre-planned in the old AGENTS.md) returns no data | Yahoo coverage of NSE tickers is inconsistent | Probed candidates live; picked `MIDCAPETF.NS`, `SMALLCAP.NS` by history length and volume. Rejected `MID150BEES.NS` (listed only 5 days earlier) | Live yfinance probe before writing the fetcher |
| 13 | New ETFs have 2–4 years of history vs Nifty's 19 | Different listing dates | Kept each asset's full history with NaN before inception (no truncation, no backfill). pandas `mean`/`cov`/`corr` are NaN-safe by default, so no downstream change was needed. Checked the pairwise covariance is PSD | Measured per-ticker history first |
| 14 | Shared XGBoost feature matrix left **15** training rows total | A global `dropna()` across 54 columns bottlenecks every asset to the newest ETF's window | Rewrote `return_predictor.py` to train per asset on its own history (Nifty: 216 rows). Assets under 20 rows are skipped and use their historical mean, recorded in metadata | Printed row counts before training |
| 15 | Top-feature importances all `NaN`, plus a `RuntimeWarning` | `Fixed_Deposit` is a constant series, so XGBoost importances were all 0 and dividing by their sum gave NaN, which poisoned the average | Skip training for zero-variance targets (`status: constant_target`) | Training output |
| 16 | Efficient frontier chart jagged, non-monotonic | `efficient_frontier()` swept targets from `mu.min()`, so it also solved the dominated **lower** branch below GMV. Sorting by risk then interleaved both branches. Invisible on old synthetic data (no negative-return asset), exposed when Gold's predicted return went negative | Sweep only from the GMV return upward, the actual definition of an efficient frontier | Playwright screenshot of the Frontier tab. A first guess (solver drift) was ruled out by printing per-target solver output |
| 17 | Covariance matrix singular | `Fixed_Deposit`'s exactly-zero variance gives a zero eigenvalue. The existing `1e-8` jitter was ~7 orders of magnitude too small against a trace of 0.34 | Jitter scaled to the matrix's own max eigenvalue (`1e-4 × λ_max`) | Eigenvalue check while debugging #16 |
| 18 | Allocations of ~95% Silver, "+80%/yr" expected return | Raw predictions from negative-R², thin-history models fed straight into mean-variance optimization ("error maximizer") | Reliability-weighted shrinkage toward historical mean (`w = clip(R²,0,1) × min(1, months/120)`, currently 0 for all), plus a 35% per-asset cap (FD exempt), plus a feasible frontier upper bound under the caps. UI now says "Historical avg" / "ML influence 0%" instead of claiming "🤖 ML" | curl + screenshots after the real-data switch |
| 19 | Personalization rules silently never fire | `personalizer.py` queries `users.income/emi/savings`, `loans.status`, and a `goals` table; none exist in `auth.db` (the real names are in §6). A bare `try/except` swallows the errors | **Fixed 2026-10-02** (see #28). Rule logic was first verified with mocked fetchers | Tried to trigger rules via a real test user; the schema didn't match |
| 20 | Playwright check landed on the login page | The test script's env vars weren't passed, so `sf_token` was literally `"undefined"` | Pass `SF_TOKEN`/`SF_USER_ID`/`SF_EMAIL` explicitly and seed `localStorage` before navigating to `/portfolio` | Logged `localStorage` values in the script |
| 21 | `chromium-cli` not available for the browser check | Not installed on this machine | `npx playwright install chromium` plus a small Node driver script in the session scratchpad | During verification |

### Session 2026-09-28 — security audit (no branch, read-only)

| # | Question | Finding |
|---|---|---|
| 22 | Is the backend vulnerable to SQL injection? | No live risk. All queries use `?` parameter binding. The 3 f-string SQL sites are safe: `budget/api.py` UPDATE builds column names only from fixed literals; `retirement_planning/repositories.py` builds `IN (?,?,…)` placeholder lists; `db_utils.py` interpolates table names only from a hardcoded list and isn't reachable from any route. No `+`/`%`/`.format()` SQL anywhere. `limit` is `int()`-cast. Nit: add an allowlist in `db_utils.py` if that function is ever reused with caller input |

### Session 2026-09-30 — SQL-injection hardening + housekeeping (branch `refactor/app-blueprints`, now in `main`)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 23 | `db_utils.py` built PRAGMA/COUNT queries with an f-string table name | Table names can't be bound as `?`; safe only because the names were hardcoded | `LOAN_TABLES` allowlist + `_safe_table_identifier()` (raises on anything else, quotes the name) + a regression test with an injection payload | Follow-up to the #22 audit |
| 24 | `pytest` missing though `requirements.txt` lists it | Local env drift | Installed `pytest==8.3.4`; `unit_test/test_loan_schema.py` 12/12 pass | Trying to run the loan tests |
| 25 | Folders like `backend/auth/` held only `__pycache__/*.pyc` files, so it looked like the code had been "converted" | Not a code problem: on a branch where a package doesn't exist, git removes the tracked `.py` files but leaves the git-ignored `__pycache__`. Python never imports from an orphaned `.pyc` | None needed; it goes away once the branch with the `.py` files is checked out or merged. To clean manually: `find backend -name __pycache__ -type d -exec rm -rf {} +` | User question |

### Session 2026-10-02 — merge + two long-standing bugs (`main`)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 26 | Work split across two unmerged branches | Each piece of work was done on its own branch off `main` | Fast-forwarded `main` to `refactor/app-blueprints`, then `--no-ff` merged `feature/portfolio-real-data`. Only `AGENTS.md` conflicted (header, known-issues list, change log); resolved by keeping both sides and cleaning up stale "not yet merged"/"synthetic data" notes | Planned. Merged tree verified: all blueprints return 200, 9-asset optimize works, `chat_agent` tool path resolves, loan tests 12/12 |
| 27 | **No user could create a financial goal** (`POST /api/profile/goals` → 500) | `requirements.txt` pinned marshmallow 3.23.2 but 4.3.1 is installed; v4 passes `data_key=` to every `@validates` method. The profile `notification_preferences` validators had the same latent break | Added `**kwargs` to all 4 validators (works on 3.x and 4.x); relaxed the pin to `>=3.23.2,<5` | Found during the 09-28 refactor. Fix verified live: goal create/list/update/delete OK; past dates and bad frequencies still rejected with 400 |
| 28 | Portfolio personalization never applied (see #19) | Queries against non-existent `users.income/emi/savings`, `loans.status`, `goals`; a bare `except: pass` hid it. Likely origin: §6 documented the budget tables with columns that don't exist | Rewrote the 4 fetchers against the real tables (§6, now corrected); failures are logged instead of swallowed | Verified live with data created through the API: 47% EMI ratio, 2 loans, goal in 6 months, 2.5% savings → all 4 rules fire, equity 25.3% → 14.7%; a user with no data gets no adjustments |
| 29 | §6 schema docs were wrong for `monthly_budgets`/`budget_categories`/`expense_entries` | Written from memory, never checked against the DB | Rewritten from `PRAGMA table_info`; added notes on where income/EMI/savings/goals actually live | Cross-checking while fixing #28 |

### Session 2026-10-02 (cont.) — Portfolio Optimizer data quality (`main`)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 30 | Mid-Cap, Small-Cap and Silver means were meaningless (Mid-Cap 95% range −19%..+29%/yr) | ETF proxies listed 2022–24, only 2–4.6 years of data | Switched to `^NSEMDCP50`, `NIFTYSMLCAP250.NS`, COMEX silver × USD/INR → 19–23 years each | User asked if the data is sufficient; computed per-asset standard errors |
| 31 | Debt showed 3.0%/yr, so it got 0% in every portfolio | `LIQUIDBEES` pays its yield as daily dividends, so the price barely moves; Yahoo's series is also broken (₹589 first close, NaN last) | Nippon India Liquid Fund growth NAV via mfapi.in (6.8%/yr, 20 years). Debt now gets 23–35% | Same review: 3% is implausible for a liquid fund |
| 32 | Liquid-fund NAV implied a 34%/yr return | One ~100× jump in 2012 (unit face value ₹10 → ₹1000) | Drop any daily NAV move >50% as a rescale | Sanity-checked the CAGR before using it |
| 33 | Weekly volatility of 2383% (Gold) and 233% (International); Gold–Silver correlation 0.03 | Yahoo left the GOLDBEES 1:100 (Dec 2019) and MON100 1:10 (Jun 2021) splits unadjusted for 1–2 days. Monthly sampling hid it because both days fell inside one month | Drop prices >3× away from their 5-day median. Weekly and monthly estimates now agree | Compared weekly vs monthly vols before trusting weekly |
| 34 | Last month for Silver was a 1-day partial period | Fetched on Oct 1, so October had 1 trading day | Cut every series at the last complete month (and the weekly series too) | Spotted a 2026-10-31 row in the output |
| 35 | Lucky-period means (International 24.7%, Silver 18.5%) would dominate allocations | Sample means are noisy; the optimizer amplifies noise | Shrinkage toward `6.5% + 0.3 × vol` weighted by each mean's standard error; the predictor's fallback/blend target uses the same shrunk means | Planned (fix #3 of 4) |
| 36 | **Risk 9 portfolio was less risky than risk 7** | Risk 9–10 mapped to Max-Sharpe, which sits mid-frontier. Hidden earlier because inflated Silver put Max-Sharpe at the top | Risk 3–10 now map evenly along the frontier; volatility verified monotonic from 0.3% (risk 1) to 15.4% (risk 10) | Printed all 10 risk scores after the data change |
| 37 | UI said "via yfinance" and listed FD as "not enough history" | Debt now comes from mfapi.in; FD is skipped as a constant, not for lack of data | Banner lists source types and years of history; skipped assets show their actual reason | Playwright screenshot review |

---

## 16. Change Log (most recent first)

| Date | Agent/Tool | Change |
|---|---|---|
| 2026-10-02 | Claude Code (Opus 5.5) | Portfolio Optimizer data quality: Mid/Small-cap → NIFTY indices, Silver → COMEX×USD/INR, Debt → liquid-fund growth NAV (mfapi.in), giving 7–23 years per asset. Cleaned unadjusted splits / NAV rescale / partial months. Expected returns shrunk toward a risk-based prior; covariance from weekly returns. Risk scores 3–10 now map evenly along the frontier (risk 9 was safer than risk 7). Retrained: 8/9 models, R² −0.47, ML weight 0. Verified live: all 4 endpoints, monotonic risk 1→10 (0.3%→15.4% vol), Playwright UI check with 0 console errors. §15 #30–#37 |
| 2026-10-02 | Claude Code (Opus 5.5) | Merged `refactor/app-blueprints` (fast-forward) and `feature/portfolio-real-data` (`--no-ff`, only AGENTS.md conflicted) into `main`. Fixed goal creation (marshmallow 4 `data_key` kwarg; all `@validates` methods now take `**kwargs`; pin relaxed to `>=3.23.2,<5`). Fixed the portfolio personalizer to read the real schema (`monthly_budgets`, `loans`, `financial_goals`, `expense_entries`) and log lookup failures instead of swallowing them; all 4 rules verified firing on real data for the first time. Corrected the §6 budget-table schema docs. Added §15 entries #23–#29. Next: Nudge Engine audit |
| 2026-09-30 | Claude Code (Opus 5.5) | SQL-injection audit of the whole backend: no live risk (all user input uses `?` binding; see the Q&A row in §13). Hardened the one theoretical gap: the `db_utils.py` helpers interpolated table names into SQL with f-strings (safe only because the names were hardcoded). Added a `LOAN_TABLES` allowlist and a `_safe_table_identifier()` validator that raises on anything else, plus a regression test in `unit_test/test_loan_schema.py` (12/12 pass). Installed `pytest==8.3.4`, which was already in requirements.txt but missing locally |
| 2026-09-29 | Claude Code (Opus 5.5) | On `feature/portfolio-real-data`: fixed extreme allocations from noisy ML predictions. `predict()` now shrinks each prediction toward the asset's historical mean, weighted by out-of-fold R² and training length (currently 0 for every asset, since all R² < 0). Added a 35% per-asset weight cap (Fixed Deposit exempt) and a cap-aware frontier upper bound. UI shows "Historical avg" / "ML influence 0%" instead of implying the ML drives allocations. Verified via curl on all endpoints plus a Playwright check (monotonic frontier, max non-FD weight 0.35, zero console errors). Added §15 "Problems Faced & Solved" covering all sessions |
| 2026-09-29 | Claude Code (Sonnet 5) | On branch `feature/portfolio-real-data` (branched from `main`): replaced the Portfolio Optimizer's fully-fabricated Gaussian-noise data with real historical market data via `yfinance`, and expanded the asset universe from 5 to 9 (added Small-Cap Equity, International Equity via Nasdaq-100 ETF, Silver, REIT). New: `fetch_real_data.py`. Rewrote `return_predictor.py` to train each asset independently on its own real history (a shared matrix would have bottlenecked all 9 assets to ~15 training rows total, driven by the newest-listed ETF). Fixed two real numerical bugs surfaced by the wider real-data mu range: (1) the efficient frontier swept target returns below the GMV return, incorrectly including the dominated lower branch of the mean-variance boundary and producing a jagged, non-monotonic chart — fixed by only sweeping from GMV upward, the correct definition of "efficient frontier"; (2) the covariance matrix's fixed `1e-8` regularization jitter was 6+ orders of magnitude too small against real covariance scales, so `Fixed_Deposit`'s exactly-zero real variance created a true singular direction that let SLSQP land on different non-global optima across the frontier sweep — fixed by scaling the jitter to the matrix's own eigenvalue range. Extended `personalizer.py`'s 4 rules to cover the new asset buckets (verified via mocked unit tests) and found, but did not fix, a separate pre-existing bug: `personalizer.py`'s DB queries reference a schema that doesn't match `auth.db`, so all 4 rules likely never fire in production (see §14 item 8). Verified end-to-end via live server + curl on all 4 endpoints, a Playwright visual check of the actual UI (screenshots, zero console errors), and a full frontend production build. |
| 2026-09-28 | Claude Code (Sonnet 5) | Added `.vscode/settings.json` → `python.defaultInterpreterPath` pointing at `C:\Python314\python.exe`, to fix editor red-squiggles on Flask imports (cosmetic, no functional change) |
| 2026-09-28 | Claude Code (Sonnet 5) | On branch `refactor/app-blueprints` (7 commits, not yet merged to `main`): split monolithic `app.py` (3600+ lines) into Flask blueprints — `auth` (16 routes), `profile_management` (10), `budget` (8), `loans` (9), `chat` (6), `calculators` (2), `legacy_scorer` (5) — plus shared `db_core.py`. `app.py` is now 393 lines, zero `@app.route` left. Every step verified with a live server boot + real curl round-trips, not just import checks. Caught and fixed a real regression mid-refactor: `chat_agent.py`'s lazy `from app import ...` in `execute_tool()` still referenced budget helpers by names the budget-blueprint commit had renamed/moved — fixed by pointing it at `budget.service` and, in the final commit, at `legacy_scorer.model`/`legacy_scorer.service` too. Also found (but did not fix) a pre-existing marshmallow bug in `POST /api/profile/goals` — see §14 item 8 |
| 2026-09-21 | Antigravity (Claude) | Merged all docs/ into AGENTS.md as legacy data, deleted docs/ tree |
| 2026-09-21 | Antigravity (Claude) | Workspace cleanup — deleted ~60 files: aurabuildtemp/, stale docs/, backlog/, scripts/, applied migrations, debug test files, large raw CSVs (13 MB), orphaned frontend components, CLAUDE.md/.windsurfrules |
| 2026-09-21 | Antigravity (Claude) | Created AGENTS.md context file |
| 2026-09-21 | Antigravity (Gemini) | Re-trained `enhanced_model.pkl` for sklearn 1.9.1 (R²=95.88%) |
| 2026-09-21 | Antigravity (Gemini) | Installed Flask + all backend packages into Python 3.14 user site-packages |
| 2026-09-20 | Antigravity (Gemini) | Added `nudge_engine/` (Isolation Forest anomaly detection) |
| 2026-09-20 | Antigravity (Gemini) | Added `portfolio_optimizer/` (Markowitz + XGBoost), trained models |
| 2026-09-20 | Antigravity (Gemini) | Added PortfolioOptimizer.jsx, NudgeEngine.jsx to frontend |
| 2026-09-20 | Antigravity (Gemini) | Added /portfolio and /nudges routes to App.jsx |
| 2026-09-20 | Antigravity (Gemini) | Added Portfolio + Nudge Engine to Sidebar.jsx |
| 2026-09-20 | Antigravity (Gemini) | Added api.get() and api.post() helpers to services/api.js |

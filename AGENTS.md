# SmartFin — Agent Context File
> **Last Updated:** 2026-09-30
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
│   │   ├── fetch_real_data.py          ← Pulls real prices via yfinance → data/asset_returns.csv + data/data_source.json
│   │   ├── data_loader.py              ← Loads cached returns; get_data_source_info(); synthetic Gaussian fallback only if never fetched
│   │   ├── return_predictor.py         ← Per-asset XGBoost; predict() shrinks toward historical mean by out-of-fold R²
│   │   ├── markowitz_engine.py         ← SLSQP mean-variance optimizer, 35% per-asset cap (FD exempt), GMV-up frontier
│   │   ├── personalizer.py             ← Adjusts allocation based on user EMI/loans/goals/savings from DB
│   │   ├── train_model.py              ← Training script (`--refresh-data` re-fetches first)
│   │   ├── data/asset_returns.csv      ← REAL monthly returns (per-asset full history, NaN before inception)
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

### Module 1: Portfolio Optimizer (Real market data via yfinance, 9-asset universe)

**Files:** `backend/portfolio_optimizer/`
**API Blueprint:** `/api/portfolio/` (registered in `app.py`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/portfolio/optimize` | POST | Returns optimal allocation for given amount + risk score |
| `/api/portfolio/frontier` | GET | Returns efficient frontier data points |
| `/api/portfolio/model-info` | GET | Returns XGBoost metrics + feature importance + data source |
| `/api/portfolio/whatif` | POST | What-if scenario comparison |

**Dataset — real, not synthetic:**
- `fetch_real_data.py` pulls real daily closes via `yfinance` for 7 tradeable proxies, resampled to monthly returns. Each asset keeps its **own full available history** (not truncated to a shared window) — e.g. Nifty 50 goes back to 2007 (228 months) while newer ETFs only as far as they've been listed. Gaps before an asset's inception are left as `NaN`; pandas' `mean()`/`cov()`/`corr()` already skip NaN by default, so risk/return stats use each asset's full real history, and only the shared XGBoost feature matrix is bottlenecked to the common overlap window.
- Common overlap window across all 9 assets (as of last fetch): **2024-07-31 to 2026-09-30** (~27 months) — set by Mid-Cap ETF's short listing history. Re-run `fetch_real_data.py` periodically; this window grows over time as the newer ETFs accumulate history.
- `Fixed_Deposit` has no market price series (FDs aren't traded) — the only assumption-based column, flat 6.5%/year, clearly labeled as such in `data/data_source.json` and surfaced in the API/UI. All 8 other assets are real market data.
- The synthetic Gaussian generator in `data_loader.py` (`generate_return_series()`) still exists as an offline fallback if `fetch_real_data.py` has never been run (e.g. fresh clone, no internet) — `get_data_source_info()` is the single source of truth for which one is actually in use, surfaced in every API response as `data_source.type` (`real_historical` vs `synthetic_fallback`).

**Asset universe (9 assets, 5 categories):**
| Asset | Category | Ticker | History (last fetch) |
|---|---|---|---|
| Equity Large-Cap | Equity | `^NSEI` (Nifty 50) | 2007-10 → present (228 mo) |
| Equity Mid-Cap | Equity | `MIDCAPETF.NS` | 2024-07 → present (27 mo) |
| Equity Small-Cap | Equity | `SMALLCAP.NS` | 2024-04 → present (30 mo) |
| International Equity | Equity | `MON100.NS` (Nasdaq 100 ETF) | 2011-04 → present (186 mo) |
| Short-Term Debt | Debt | `LIQUIDBEES.NS` | 2009-02 → present (212 mo) |
| Gold | Precious Metals | `GOLDBEES.NS` | 2009-02 → present (212 mo) |
| Silver | Precious Metals | `SILVERBEES.NS` | 2022-03 → present (55 mo) |
| REIT | Real Estate | `EMBASSY.NS` (Embassy Office Parks REIT) | 2019-05 → present (89 mo) |
| Fixed Deposit | FD / Cash | — (assumption-based) | full range |

**Model:**
- XGBoost Regressor, trained **independently per asset on that asset's own available history** (not one shared row-aligned matrix — see `return_predictor.py`'s module docstring for why: a shared matrix bottlenecks every asset to the newest asset's ~27-month window, which measured out to only 15 usable training rows total). Per-asset `TimeSeriesSplit` CV, `n_splits` scaled to available rows (2–5).
- Assets with fewer than 20 usable rows after feature/target construction (Mid-Cap, Small-Cap — both real, just newly listed) are skipped for training; `predict()` falls back to that asset's own historical mean instead of a trained model. `Fixed_Deposit` is also skipped (constant target, zero variance — nothing for a model to learn).
- As of last training: **6/9 assets trained**, overall R² = **-0.44** (genuinely negative now, not tautological — earlier synthetic-data version's R²=-0.73 was predicting noise from noise; this version predicts real next-month returns from real momentum/vol features and still can't beat the mean, a legitimate EMH result).
- Markowitz optimizer: `scipy.optimize.minimize` with SLSQP → returns GMV, Max-Sharpe, risk-score-matched portfolios. Covariance matrix is regularized (jitter scaled to the matrix's own eigenvalue range, not a fixed `1e-8`) — `Fixed_Deposit`'s exactly-zero real variance creates a true zero eigenvalue otherwise, which let SLSQP land on different non-global optima across the frontier sweep and produce a jagged, non-monotonic chart. `efficient_frontier()` also only sweeps target returns from the GMV return upward (the true efficient/upper branch) — sweeping below GMV, as the old code did, computes the dominated lower branch instead, invisible with the old synthetic data (no negative-return assets) but exposed once Gold's real ML-predicted return went negative.
- **Prediction shrinkage (reliability-weighted blend):** `predict()` does not feed raw XGBoost outputs to the optimizer. Each asset's expected return is `w × ml_prediction + (1 − w) × historical_mean`, with `w = clip(out-of-fold R², 0, 1) × min(1, training_months / 120)`, computed at training time and stored in the model artifact and `model_metadata.json` (`per_asset_metrics[asset].ml_weight`, `blend.avg_ml_weight`). A model that doesn't beat the historical mean out-of-sample gets zero say. As of last training every model has R² < 0, so **all weights are 0** and allocations run on real historical means. The UI's Engine chip reads "Historical avg" and the model card states "ML influence on expected returns: 0%" and why. As assets accrue history or models improve, ML influence rises on its own, with no code change. `predict(df, raw=True)` still returns unblended predictions for inspection.
- **Why it was needed:** the raw predictions were fed straight into mean-variance optimization, producing ~95% Silver allocations and a +80%/yr Silver "expected return" off only 43 months of data. This is the classic "Markowitz is an error-maximizer" failure: the optimizer concentrates in whichever estimate is most overstated.
- **Per-asset weight cap:** `MAX_ASSET_WEIGHT = 0.35` in `markowitz_engine.py`, applied as SLSQP bounds in every solve (min-variance, GMV, max-Sharpe). `Fixed_Deposit` is exempt (`UNCAPPED_ASSETS`) so conservative portfolios can still be mostly cash. `efficient_frontier()`'s upper target is `_max_feasible_return()`, the best return reachable under the caps (greedy fill by descending return); `mu.max()` isn't reachable once assets are capped.
- **Resulting behavior (last run):** risk 1 → 5.7%/yr at 0.3% vol (mostly FD + liquid debt); risk 5 → 13.5% at 6.6% vol; risk 9–10 → 19.2% at 11.8% vol with International Equity at the 35% cap. Best-Sharpe 1.07, down from an inflated 2.95.

**Fetching real data / retraining:**
```bash
cd backend
python -X utf8 portfolio_optimizer/fetch_real_data.py   # fetch/refresh real data only
python -X utf8 portfolio_optimizer/train_model.py        # train on whatever's cached
python -X utf8 portfolio_optimizer/train_model.py --refresh-data  # fetch + train in one step
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
monthly_budgets (id PK, user_id FK, month, year, total_budget, created_at)
budget_categories (id PK, user_id FK, category_name, monthly_limit)
expense_entries / expenses (id PK, user_id FK, category, amount, date)
```

### Loans
```sql
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
- [ ] Fix `portfolio_optimizer/personalizer.py` DB queries to use the real `auth.db` schema (see §14 item 9) — until then, personalization rules never fire
- [ ] Merge `refactor/app-blueprints` and `feature/portfolio-real-data` into `main` (both branched from `main`; they touch disjoint files except AGENTS.md — expect a conflict only there)
- [ ] Fix pre-existing marshmallow bug in `POST /api/profile/goals` (`validate_future_date() got an unexpected keyword argument 'data_key'`) — found during the blueprint refactor, documented on that branch
- [ ] Replace `MainDashboard.jsx` health score widget with Portfolio Summary card (optional)
- [ ] Full removal of old scorer — `financial_health_scorer.py`, `ScoreDisplay.jsx`, `/api/predict` (optional)
- [ ] Run `demo_seeder.py` for a real user account to populate Nudge Engine data
- [ ] End-to-end test: login → /portfolio → set amount + risk → verify donut chart renders

---

## 13. Interview / Presentation Talking Points

### The Honest Story on Enhanced Model (R²=95.88%)
> "We use a GradientBoosting Regressor trained on 52,424 records from two Kaggle datasets (global personal finance + India personal finance). The target labels are generated by an 8-factor rule-based formula we designed — savings behavior, debt burden, expense control, life stage, and loan metrics. The model learns to replicate that formula accurately. The key advantage: our scoring is fully transparent and explainable to users, while the ML layer enables fast generalization to new users without running the rule engine."

### Portfolio Optimizer Story
> "The core optimization is Markowitz Mean-Variance (SLSQP) over 9 real asset classes — Nifty 50, Mid-Cap, Small-Cap, Nasdaq 100 (via an NSE-listed ETF), short-term debt, gold, silver, and a REIT, all fetched via yfinance, plus Fixed Deposit as the one openly-assumption-based column since FDs aren't traded. XGBoost predicts next-month returns per asset from its own real momentum/volatility history, and overall R²≈-0.44 — genuinely negative, consistent with the Efficient Market Hypothesis, not a tautology: earlier versions of this module used fabricated Gaussian-noise 'market data,' where a negative R² just meant noise can't predict noise. This version predicts real prices and still can't beat the mean, which is the actual EMH result. Two newly-listed assets (Mid-Cap, Small-Cap ETFs) don't have enough real history yet to train reliably, so they're transparently skipped and fall back to their historical mean — disclosed in the API and UI, not hidden. Crucially, the ML only influences allocations as much as it has earned: each prediction is blended with the historical mean, weighted by its out-of-sample R², so today it has zero say. Feeding raw predictions in gave 95% Silver, the classic 'Markowitz as error-maximizer' failure. Plus a 35% per-asset cap for diversification."

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
8. **`validation_schemas.py` marshmallow bug** — `POST /api/profile/goals` (and likely other schema validators using the same pattern) throws `GoalCreateSchema.validate_future_date() got an unexpected keyword argument 'data_key'` — a marshmallow version mismatch (validator signature expects an older/newer marshmallow API). Confirmed present both before and after the blueprint refactor, so it's a pre-existing bug, not a regression. Not yet fixed. **(see §15 — scheduled for fix)**
9. **`portfolio_optimizer/personalizer.py`'s DB queries reference a schema that doesn't match `auth.db`** — `_get_emi_ratio()`/`_get_savings_ratio()` query `users.income`/`users.emi`/`users.savings`, which don't exist on the `users` table (that data lives in `financial_goals`/`monthly_budgets`/`users_profile` — see §6 schema); `_get_active_loans_count()` queries `loans.status = 'active'` but the real column is `default_status`; `_get_shortest_goal_months()` queries a `goals` table that doesn't exist (the real table is `financial_goals`). Every one of these silently fails and is swallowed by a bare `try/except`, meaning all 4 personalization rules likely never fire in production — found while testing the portfolio optimizer's 9-asset expansion, not something that session introduced or fixed. The rule *logic* itself (which assets get shifted) was verified correct via mocked unit tests bypassing these broken DB calls; the DB integration itself needs a real fix (point the queries at the actual schema) before personalization can work end-to-end.
10. **Portfolio Optimizer re-fetch cadence:** `data/asset_returns.csv` is a snapshot. Re-run `fetch_real_data.py` + `train_model.py` periodically. Mid-Cap and Small-Cap ETFs cross the 20-usable-row training threshold around early 2027 and will then start training instead of falling back to historical mean.
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
| 7 | `POST /api/profile/goals` → `validate_future_date() got an unexpected keyword argument 'data_key'` | Marshmallow version mismatch in `validation_schemas.py` | **Not fixed.** Confirmed pre-existing by reproducing on the pre-refactor commit | Live test of the profile blueprint |
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
| 19 | Personalization rules silently never fire | `personalizer.py` queries `users.income/emi/savings`, `loans.status`, and a `goals` table; none exist in `auth.db` (the real names are in §6). A bare `try/except` swallows the errors | **Not fixed.** Rule logic verified with mocked fetchers; queries need rewriting (see §12) | Tried to trigger rules via a real test user; the schema didn't match |
| 20 | Playwright check landed on the login page | The test script's env vars weren't passed, so `sf_token` was literally `"undefined"` | Pass `SF_TOKEN`/`SF_USER_ID`/`SF_EMAIL` explicitly and seed `localStorage` before navigating to `/portfolio` | Logged `localStorage` values in the script |
| 21 | `chromium-cli` not available for the browser check | Not installed on this machine | `npx playwright install chromium` plus a small Node driver script in the session scratchpad | During verification |

### Session 2026-09-28 — security audit (no branch, read-only)

| # | Question | Finding |
|---|---|---|
| 22 | Is the backend vulnerable to SQL injection? | No live risk. All queries use `?` parameter binding. The 3 f-string SQL sites are safe: `budget/api.py` UPDATE builds column names only from fixed literals; `retirement_planning/repositories.py` builds `IN (?,?,…)` placeholder lists; `db_utils.py` interpolates table names only from a hardcoded list and isn't reachable from any route. No `+`/`%`/`.format()` SQL anywhere. `limit` is `int()`-cast. Nit: add an allowlist in `db_utils.py` if that function is ever reused with caller input |

---

## 16. Change Log (most recent first)

| Date | Agent/Tool | Change |
|---|---|---|
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

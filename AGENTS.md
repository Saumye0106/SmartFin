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

> **⚠️ Branch note:** The `backend/` blueprint layout below (auth/, profile_management/, budget/, loans/, chat/, calculators/, legacy_scorer/, db_core.py) reflects the `refactor/app-blueprints` branch, not yet merged to `main`. If you're on `main`, `app.py` is still the pre-refactor 3600+ line monolith described in the old layout — check `git branch` / `git log` before assuming this structure is present. See section 14 item 6 and the change log for details.

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
│   ├── validation_schemas.py           ← Marshmallow input validation — has a known bug, see section 14 item 8
│   ├── db_utils.py                     ← Loan-table-specific DB helpers (separate from db_core.py). Any SQL that interpolates a table name must go through `_safe_table_identifier()` (allowlist: `LOAN_TABLES`)
│   ├── retirement_planning/            ← Isolated domain package for retirement workflows
│   │   ├── api.py                      ← Blueprint at /api/retirement/
│   │   └── migrations.py              ← Creates retirement DB tables on startup
│   ├── portfolio_optimizer/            ← ✅ ML Module #1 (Markowitz + XGBoost)
│   │   ├── api.py                      ← Flask Blueprint at /api/portfolio/
│   │   ├── data_loader.py              ← Generates Indian market monthly return series
│   │   ├── return_predictor.py         ← XGBoost return prediction (one model per asset)
│   │   ├── markowitz_engine.py         ← Scipy SLSQP Markowitz mean-variance optimizer
│   │   ├── personalizer.py             ← Adjusts allocation based on user EMI/goals from DB
│   │   ├── train_model.py              ← Training script
│   │   ├── data/asset_returns.csv      ← 84-month Indian market return series (GENERATED, not real)
│   │   └── models/                     ← Trained XGBoost pkl + model_metadata.json
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

### Module 1: Portfolio Optimizer (NEW — Real ML)

**Files:** `backend/portfolio_optimizer/`  
**API Blueprint:** `/api/portfolio/` (registered in `app.py`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/portfolio/optimize` | POST | Returns optimal allocation for given amount + risk score |
| `/api/portfolio/frontier` | GET | Returns efficient frontier data points |
| `/api/portfolio/model-info` | GET | Returns XGBoost metrics + feature importance |
| `/api/portfolio/whatif` | POST | What-if scenario comparison |

**Dataset:**
- Source: Statistically generated using `data_loader.py` — calibrated to real 10-year Indian market benchmarks
- 84 months (7 years) of monthly returns saved to `portfolio_optimizer/data/asset_returns.csv`
- **⚠️ PENDING:** Switch to real `yfinance` data — user agreed, not yet done

**Asset Classes:**
1. Equity Large-Cap (Nifty 50 proxy): 12% annual return, 18% vol
2. Equity Mid-Cap (Nifty Midcap proxy): 14% annual return, 22% vol
3. Short-Term Debt (CRISIL proxy): 6.5% annual, 2% vol
4. Gold (domestic INR): 8% annual, 14% vol
5. Fixed Deposit: 6.5% annual, 0.5% vol

**5×5 Correlation Matrix (empirical):** LargeCap–MidCap=0.85, Equity–Debt=-0.10, Debt–FD=0.70, Gold–Equity=0.05

**Model:**
- XGBoost Regressor (one model per asset class), TimeSeriesSplit CV (n_splits=5)
- Features: rolling 3m/6m/12m returns, volatility, Sharpe ratio per asset
- Overall R² = -0.73 (expected per Efficient Market Hypothesis — strong interview talking point)
- Markowitz optimizer: `scipy.optimize.minimize` with SLSQP → returns GMV, Max-Sharpe, risk-score-matched portfolios

**Training:**
```bash
cd backend
python -X utf8 portfolio_optimizer/train_model.py
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

- [ ] Fetch real Indian market data via `yfinance` (`^NSEI`, `GOLDBEES.NS`, `NIFTYMID50.NS`, `LIQUIDBEES.NS`) and retrain Portfolio Optimizer XGBoost
- [ ] Replace `MainDashboard.jsx` health score widget with Portfolio Summary card (optional)
- [ ] Full removal of old scorer — `financial_health_scorer.py`, `ScoreDisplay.jsx`, `/api/predict` (optional)
- [ ] Run `demo_seeder.py` for a real user account to populate Nudge Engine data
- [ ] End-to-end test: login → /portfolio → set amount + risk → verify donut chart renders

---

## 13. Interview / Presentation Talking Points

### The Honest Story on Enhanced Model (R²=95.88%)
> "We use a GradientBoosting Regressor trained on 52,424 records from two Kaggle datasets (global personal finance + India personal finance). The target labels are generated by an 8-factor rule-based formula we designed — savings behavior, debt burden, expense control, life stage, and loan metrics. The model learns to replicate that formula accurately. The key advantage: our scoring is fully transparent and explainable to users, while the ML layer enables fast generalization to new users without running the rule engine."

### Portfolio Optimizer Story
> "The core optimization is Markowitz Mean-Variance (SLSQP), which finds the efficient frontier of Indian asset classes. XGBoost predicts next-period returns, but R²=-0.73 is expected under the Efficient Market Hypothesis — stocks are hard to predict. The model's real value is in momentum and volatility features that inform asset weight constraints, not in beating the market."

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
6. **app.py monolith — RESOLVED on `refactor/app-blueprints` branch, not yet merged to `main`.** All routes have been split into blueprints (auth, profile_management, budget, loans, chat, calculators, legacy_scorer) following the pattern retirement_planning/portfolio_optimizer/nudge_engine already used. `app.py` is now 393 lines of pure setup/wiring. If you're reading this from `main`, the split hasn't landed yet — check which branch you're on before assuming this structure exists. When merging, watch for: any lazy `from app import <name>` elsewhere in the codebase (e.g. `chat_agent.py`'s `execute_tool()`) that still points at a name that moved — this exact class of bug broke chat mid-refactor and was caught only by manually testing `/api/chat`, not by import checks alone.
7. **`retirement_planning/` integration_manager.py** — imports `financial_health_scorer` internally. Do not delete `financial_health_scorer.py` without updating `integration_manager.py` first.
8. **`validation_schemas.py` marshmallow bug** — `POST /api/profile/goals` (and likely other schema validators using the same pattern) throws `GoalCreateSchema.validate_future_date() got an unexpected keyword argument 'data_key'` — a marshmallow version mismatch (validator signature expects an older/newer marshmallow API). Confirmed present both before and after the blueprint refactor, so it's a pre-existing bug, not a regression. Not yet fixed.
9. **IDE red squiggles on `flask`/`flask_jwt_extended` imports** — the editor's Python language server doesn't know packages live in `C:\Users\saumy\AppData\Roaming\Python\Python314\site-packages` (see item 1). Fixed via `.vscode/settings.json` → `"python.defaultInterpreterPath": "C:\\Python314\\python.exe"`. If squiggles persist, reload the window or run "Python: Select Interpreter" and pick that path manually. Purely cosmetic — doesn't affect running the app.

---

## 15. Change Log (most recent first)

| Date | Agent/Tool | Change |
|---|---|---|
| 2026-09-30 | Claude Code (Opus 5.5) | SQL-injection audit of the whole backend: no live risk (all user input uses `?` binding; see the Q&A row in §13). Hardened the one theoretical gap: the `db_utils.py` helpers interpolated table names into SQL with f-strings (safe only because the names were hardcoded). Added a `LOAN_TABLES` allowlist and a `_safe_table_identifier()` validator that raises on anything else, plus a regression test in `unit_test/test_loan_schema.py` (12/12 pass). Installed `pytest==8.3.4`, which was already in requirements.txt but missing locally |
| 2026-09-28 | Claude Code (Sonnet 5) | Added `.vscode/settings.json` → `python.defaultInterpreterPath` pointing at `C:\Python314\python.exe`, to fix editor red-squiggles on Flask imports (cosmetic, no functional change) |
| 2026-09-28 | Claude Code (Sonnet 5) | On branch `refactor/app-blueprints` (7 commits, not yet merged to `main`): split monolithic `app.py` (3600+ lines) into Flask blueprints — `auth` (16 routes), `profile_management` (10), `budget` (8), `loans` (9), `chat` (6), `calculators` (2), `legacy_scorer` (5) — plus shared `db_core.py`. `app.py` is now 393 lines, zero `@app.route` left. Every step verified with a live server boot + real curl round-trips, not just import checks. Caught and fixed a real regression mid-refactor: `chat_agent.py`'s lazy `from app import ...` in `execute_tool()` still referenced budget helpers by names the budget-blueprint commit had renamed/moved — fixed by pointing it at `budget.service` and, in the final commit, at `legacy_scorer.model`/`legacy_scorer.service` too. Also found (but did not fix) a pre-existing marshmallow bug in `POST /api/profile/goals` — see section 14 item 8 |
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

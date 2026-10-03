# SmartFin — Agent Context File
> **Last Updated:** 2026-10-04
> **Purpose:** Master context document for any AI agent or IDE working on this project.
> Always read this file first before making any changes. Always update the relevant sections after completing work — and always update it again at the end of a session or after any significant change, even if the session isn't "done" with its broader task.

---

## 1. Project Overview

**SmartFin** is a personal finance management web application built as a portfolio/academic project. The goal is to demonstrate real, interview-worthy ML modules rather than fake heuristic models.

- **Stack:** Flask (Python) backend + React (Vite) frontend
- **Database:** SQLite (`auth.db`) locally by default; **PostgreSQL** when `DATABASE_URL` is set (containers, AWS). Same code and SQL for both, via `backend/dbapi.py`
- **Auth:** Flask-JWT-Extended (Bearer tokens)
- **Port:** Backend → `5000`, Frontend (dev) → `5173`
- **Target Audience:** Students and early-career professionals in India
- **ML that is real (as of 2026-10-03):** the health score (XGBoost on real borrower outcomes, beats its baseline), the Nudge Engine's Isolation Forest (unaudited), the portfolio return predictor (trained on real prices, 0% influence).
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

```bash
# Whole app in containers (same images that get deployed); needs Docker Desktop running
set JWT_SECRET_KEY=<random 32+ chars>      # PowerShell: $env:JWT_SECRET_KEY = "..."
docker compose up --build                  # http://localhost:8088 (empty database in a Docker volume)
docker build --target test backend         # runs the test suite inside the Linux image
```

> **Important:** Flask and all backend packages are installed in the user site-packages: `C:\Users\saumy\AppData\Roaming\Python\Python314\site-packages`. Do NOT activate `.venv` — it is broken.

### Installed Backend Packages (Python 3.14)
- `flask`, `flask-cors`, `flask-jwt-extended`, `waitress`, `werkzeug`
- `scikit-learn==1.9.1`, `xgboost==3.4.1`, `scipy==1.18.1`
- `numpy`, `pandas`, `joblib`, `boto3`, `twilio`, `requests`, `python-dotenv`
- `yfinance` (Portfolio Optimizer real data), `pytest==8.3.4` (installed 2026-09-30; was in requirements.txt but missing)
- `pdfplumber`, `openpyxl`, `xlrd` (statement import: PDF / XLSX / XLS). `reportlab` is dev-only, used by `unit_test/fixtures/statements/make_fixtures.py` to generate sample PDFs; not in requirements.txt.
- `backend/requirements.txt` is now **pinned to the versions that actually run** (Python 3.14, Flask 3.1.3, scikit-learn 1.9.1, xgboost 3.4.1 / `xgboost-cpu` on Linux, pandas 3.0.6, numpy 2.5.2, marshmallow 4.3.1 …); test tooling is in `requirements-dev.txt`. The root `requirements.txt` and `backend/runtime.txt` (python-3.11.9) are older leftovers and are not used by the Docker build.

---

## 3. Directory Structure

> **Branch status (2026-10-02):** `refactor/app-blueprints` and `feature/portfolio-real-data` are both merged into `main`; the layout below is `main`.

```
smartfin-copy/
├── backend/
│   ├── app.py                          ← Flask app factory — config, CORS, DB init, blueprint registration ONLY (393 lines, zero @app.route left)
│   ├── db_core.py                      ← Request-scoped connection + helpers (get_db, execute_query, row_to_dict, rows_to_list); DATA_DIR / DB_PATH / UPLOAD_DIR
│   ├── dbapi.py                        ← **The only place a database is opened.** `connect(path)` → SQLite, or a PostgreSQL connection that behaves like sqlite3 when `DATABASE_URL` is set
│   ├── auth.db                         ← SQLite database (users, expenses, loans, goals, etc.)
│   ├── auth/api.py                     ← Blueprint: register/login/refresh/protected, email verification, password reset, Twilio OTP (16 routes)
│   ├── profile_management/api.py       ← Blueprint: profile CRUD, picture upload/delete, goals CRUD (10 routes). Named _management to avoid shadowing stdlib `profile`
│   ├── budget/
│   │   ├── api.py                      ← Blueprint: monthly budget + expenses CRUD, summaries (8 routes)
│   │   ├── service.py                  ← Shared budget helpers (build_budget_summary, etc.) — also used by legacy_scorer and chat_agent
│   │   └── data_management.py          ← delete_month / delete_all / data_overview for one user's budget history (conn-based, unit-tested)
│   ├── loans/api.py                    ← Blueprint: loan CRUD, payment recording/history, cached loan metrics (9 routes)
│   ├── chat/
│   │   ├── api.py                      ← Blueprint: AI chat agent endpoint + session list/history/rename/delete/clear (6 routes)
│   │   └── service.py                  ← Session-id scoping, title generation, conversation persistence
│   ├── calculators/api.py              ← Blueprint: SIP + lumpsum calculators (pure math, no DB/auth)
│   ├── legacy_scorer/                  ← Health-score ROUTES + rule-based advice. Name is historical: the score now comes from risk_scorer/
│   │   ├── model.py                    ← Thin handle on the risk model (model_data, model_metadata, feature_names); no longer loads enhanced_model.pkl
│   │   ├── service.py                  ← score_request, run_prediction_analysis(data, history), classify_score + rule-based patterns/guidance/alerts/investments
│   │   └── api.py                      ← Blueprint: /, /api/predict, /api/predict/from-budget, /api/whatif, /api/model-info
│   ├── risk_scorer/                    ← ✅ Financial-distress risk model trained on REAL borrower outcomes (replaced the formula-copying scorer 2026-10-03)
│   │   ├── fetch_data.py               ← Downloads Give Me Some Credit (150k borrowers) from OpenML id 46929, no login. CSV is git-ignored
│   │   ├── features.py                 ← The 5 features, monotone constraints, age bands, training-frame cleaning, build_features()
│   │   ├── train_model.py              ← 5-fold CV vs logistic baseline, calibration check, final fit → models/
│   │   ├── model.py                    ← RiskModel: probability, 0-100 score (percentile within age band), drivers (TreeSHAP)
│   │   ├── service.py                  ← assess_request(form, history) with confidence levels, assess_user(conn, user_id) from records, user_history, get/save_risk_profile
│   │   ├── migrations.py               ← risk_profile table (saved credit-card limit and balance)
│   │   └── models/                     ← risk_model.json (XGBoost native format, not a pickle) + model_metadata.json
│   ├── loan_metrics_engine.py          ← Loan EMI/amortization calculations
│   ├── loan_history_service.py         ← Loan CRUD business logic
│   ├── loan_data_serializer.py         ← Loan response formatting
│   ├── chat_agent.py                   ← AWS Bedrock (Nova model) chat agent with tool-calling. `execute_tool()` lazily imports model/scoring helpers from `legacy_scorer.model`/`legacy_scorer.service` and budget helpers from `budget.service` — update these imports if those modules move again
│   ├── guidance_engine.py              ← Rule-based + optional AI financial guidance
│   ├── goals_service.py                ← Goals CRUD logic
│   ├── profile_service.py              ← User profile management
│   ├── risk_assessment_service.py      ← Risk scoring engine
│   ├── twilio_service.py               ← SMS/OTP integration
│   ├── validation_schemas.py           ← Marshmallow input validation (the old `data_key` bug is fixed, §14 item 8)
│   ├── db_utils.py                     ← Loan-table-specific DB helpers (separate from db_core.py). Any SQL that interpolates a table name must go through `_safe_table_identifier()` (allowlist: `LOAN_TABLES`)
│   ├── statement_import/               ← Bank statement import (CSV/XLS/XLSX/PDF) → categorized transactions → budget expenses
│   │   ├── parser.py                   ← Keyword-based header/column detection (bank-agnostic), day-first dates, PDF passwords; no narration column → description = mode + name columns
│   │   ├── categorizer.py              ← Merchant extraction from UPI/NEFT/IMPS/POS narrations + Indian-merchant rulebook + user rules
│   │   ├── service.py                  ← preview → confirm → undo; dedupe hashes; learned rules; sync_income; recurring_summary
│   │   ├── recurring.py                ← Recurring-stream detection (gap cadence + amount stability, amount-cluster and calendar-month fallbacks) and salary-income per month
│   │   ├── api.py                      ← Blueprint at /api/import/
│   │   └── migrations.py               ← bank_transactions, merchant_category_overrides, expense_entries.source
│   ├── unit_test/fixtures/statements/  ← SAMPLE statements (HDFC/SBI/Axis/ICICI layouts, protected PDF, 6-month HDFC) + make_fixtures.py
│   ├── credit_report/                  ← Credit bureau report (PDF) → loans, payment history, card details
│   │   ├── parser.py                   ← Label-based text parser (bureau-agnostic); two payment-history layouts; PDF passwords
│   │   ├── service.py                  ← preview → confirm → undo; account identity hash; DPD → on-time/late/missed; EMI formula
│   │   ├── api.py                      ← Blueprint at /api/import/credit-report
│   │   └── migrations.py               ← credit_report_imports, credit_accounts, credit_account_history
│   ├── unit_test/fixtures/credit_reports/ ← SAMPLE reports (CIBIL-style, Experian-style, protected PDF, txt) + make_fixtures.py
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
│   │   ├── StatementImport.jsx         ← Import modal (opened from BudgetManager): upload → password → preview/edit → import → undo
│   │   ├── RecurringPayments.jsx       ← Budget-page card: detected income / fixed costs / investing per month + each stream
│   │   ├── BudgetDataManager.jsx       ← Budget-page "Manage data" card: past imports (undo), delete this month, delete all (typed DELETE)
│   │   ├── CreditReportImport.jsx      ← Import dialog on the Loans page (portal on <body>): upload → password → preview/edit → import → undo
│   │   └── ...                         ← All other existing components UNTOUCHED
│   └── services/api.js                 ← Axios client — has generic api.get() / api.post()
├── docker-compose.yml                  ← backend + frontend containers for local runs (port 8088, named volume for data)
├── backend/Dockerfile, .dockerignore   ← python:3.14-slim; stages base → test (pytest in-image) → runtime (non-root, /data volume, waitress)
├── frontend/Dockerfile                 ← node build → nginx; nginx.conf.template forwards API paths to ${BACKEND_URL}
├── STANDALONE_APP_IDEAS.md             ← Saved ideas for separate apps (EMI decoder, scam checker, …)
├── .gitattributes                      ← Marks pdf/xlsx/xls/pkl/images binary (autocrlf=true would corrupt them)
├── AGENTS.md                           ← ← THIS FILE — update after every change
└── docs/                               ← ← DELETED — all context consolidated here
```

---

## 4. Key Design Decisions

### What Was Changed vs What Was Kept

| Module | Status | Reason |
|---|---|---|
| `financial_health_scorer.py`, `data/enhanced_model.pkl`, `data/train_enhanced_model.py`, `data/combined_dataset.csv` | **DELETED 2026-10-04** | Old formula-based scorer; nothing referenced them. Recoverable from git history |
| `/api/predict` endpoint | **KEPT** | Old health score endpoint still live |
| `MainDashboard.jsx` ScoreDisplay | **KEPT** | Old dashboard still works as-is |
| `risk_scorer/` | **NEW 2026-10-03** | Replaced the health score: XGBoost on real borrower outcomes; `/api/predict`, `/api/whatif`, `/api/model-info` kept, same response shape plus `risk` |
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

### Financial Health Score — risk model on real outcomes (LIVE since 2026-10-03)

**Files:** `backend/risk_scorer/` (model), `backend/legacy_scorer/` (routes + rule-based advice)
**Endpoints (unchanged paths):** `/api/predict`, `/api/predict/from-budget`, `/api/whatif`, `/api/model-info`. Responses keep `score`, `classification`, `patterns`, `guidance`, `anomalies`, `investments` and add `risk` {risk_probability, score, age_band, average_risk, drivers[], features, inputs_missing, history_source} and a new `model_info`.

**What it is:** an XGBoost classifier that predicts the probability of serious payment distress (90+ days past due within 2 years), trained on **Give Me Some Credit**: 149,999 real US borrowers, 10,026 of whom ended up in distress (6.68%). Labels are real outcomes, not a formula.

**Features (5), chosen because SmartFin can supply them and their meaning transfers:**
| Feature | From SmartFin |
|---|---|
| `age` | request, else `users_profile.age`, else 30 (the model was never trained on a missing age) |
| `debt_ratio` | (EMI + rent) / income |
| `times_late` | request, else `loan_payments.payment_status = 'late'` in the last 730 days |
| `times_seriously_late` | request, else `'missed'` in the last 730 days |
| `utilization` | optional: card balance / card limit; NaN when no card |

Left out on purpose: `MonthlyIncome` (US dollars; income still enters via the ratio), open credit lines and real-estate loans (in US data zero lines = 21% distress because lines include cards; it would tell users with no loans to borrow), dependents (+0.001 AUC).

**Results (5-fold stratified CV, out-of-fold):**
| Model | AUC | PR-AUC | Brier |
|---|---|---|---|
| Always predict the base rate | 0.500 | 0.067 | 0.0624 |
| Logistic regression (baseline) | 0.836 | 0.360 | 0.0517 |
| **XGBoost** | **0.858** | **0.391** | **0.0497** |
| Logistic, no card data | 0.820 | 0.356 | 0.0517 |
| XGBoost, card data hidden | 0.828 | 0.364 | 0.0509 |
| Reference: XGBoost on all 10 raw columns | 0.866 | 0.401 | 0.0490 |

- Calibrated without post-processing: predicted vs observed distress per decile agree (e.g. 4.2% vs 4.2%, 11.1% vs 11.5%, 37.1% vs 36.0%).
- The ML gain is real but depends on card data: +0.022 AUC with utilization, only +0.008 without. Age and debt ratio alone give 0.66, so a user with no payment history and no card gets a weak score. Say this plainly if asked.
- Feature importance (gain): late payments 40%, missed payments 38%, utilization 13%, age 6%, debt ratio 3%.
- **One model for both cases:** utilization is hidden for a random half of the training rows, so the same model handles users with and without a card.
- **Monotone constraints** on debt ratio, late, missed and utilization (cost: 0.002 AUC), so a what-if can never reward paying late or borrowing more.
- **Score (0-100)** = share of reference borrowers **in the user's own age band** (18-29, 30-39, 40-49, 50-59, 60+) with a higher predicted risk, compared like-for-like (with/without card data). The absolute probability is shown next to it. Classification bands unchanged (80/65/50/35).
- **Drivers** = XGBoost `pred_contribs` (TreeSHAP), so the explanation is what the model computed. `shap` is not a dependency.
- **Caveats shown in the UI:** US borrowers from 2011, not Indian users (ranking of risk factors transfers better than absolute probabilities); the label is credit distress, not overall wellbeing.
- Guidance, alerts, spending patterns and investment suggestions around the score are **still hand-written rules**.
- **Confidence (2026-10-04):** every assessment carries `confidence` + `missing[]`. `good` = payment history (stated, or ≥1 payment on record) or card data known; `limited` = only the debt ratio known (UI shows an amber low-confidence banner); `insufficient` = none of them → `score` and `risk_probability` are `null`, classification is "Not enough data", and the UI lists what to add. An empty payment record is not treated as a clean one. The rule-based advice gets a neutral 50 in that case (`NEUTRAL_RULE_SCORE`).
- **Saved card details:** `risk_profile(user_id, card_limit, card_balance)`. Typing a card limit into the score form while logged in saves it; the form pre-fills it next time; `GET/PUT /api/risk-profile` (PUT with `card_limit: null` clears).
- **Payment history from a credit report (2026-10-04):** `user_history` = `loan_payments` of the user's loans (which include payments created by a credit-report import) **plus** `credit_account_history` of accounts that did not become loans (cards, closed loans, loans missing details), last 730 days. Days past due map the way the model's inputs are defined: <30 → on-time, 30–89 → late, 90+ → missed. Open cards' total limit and balance become `risk_profile`. Known limit: each reported *month* at 90+ counts once, so a loan stuck in default for many months counts many times; the training data's "number of times" may count such a spell less.
- **`assess_user(conn, user_id)`** scores from records alone: income = latest budget with income, EMI = sum of active loans' `monthly_emi`, rent = detected recurring rent (else latest month's rent expenses), plus history and saved card. The **retirement planner** uses it for the 20% financial-health part of readiness; with insufficient data it raises and the planner falls back to its neutral 50.

**Retrain:**
```bash
cd backend
python -X utf8 risk_scorer/train_model.py                 # downloads the data on first run
python -X utf8 risk_scorer/train_model.py --refresh-data
```

---

### Legacy Module: 8-factor scorer (RETIRED from the score endpoints 2026-10-03)

> Historical description only. All of its files were deleted on 2026-10-04 (`financial_health_scorer.py`, `enhanced_model.pkl`, its training script and dataset); the retirement planner now uses `risk_scorer`. `loan_metrics_engine.py` stays: the loans module uses it.

**Files:** `backend/financial_health_scorer.py`, `backend/loan_metrics_engine.py`, `data/enhanced_model.pkl`, `data/train_enhanced_model.py`

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

### Statement import (created at startup by `statement_import/migrations.py`)
```sql
bank_transactions (id PK UUID, user_id FK, txn_date 'YYYY-MM-DD', description, merchant, amount CHECK(>0),
                   direction CHECK(debit|credit), balance, category, expense_id (→ expense_entries, nullable),
                   import_batch_id, txn_hash, created_at, UNIQUE(user_id, txn_hash))
merchant_category_overrides (user_id, merchant (lowercase), category, updated_at, PK(user_id, merchant))  ← learned from user corrections
-- expense_entries.source: 'manual' (default) | 'import'
-- monthly_budgets.income_source: 'manual' (default; set by the budget form) | 'import' (filled from salary credits).
--   Imports never overwrite non-zero 'manual' income; 'import' income is re-synced on every import/undo.
-- bank_transactions.category also allows 'income', 'transfer', 'investment' (never become expenses)
```

### Credit report import (created at startup by `credit_report/migrations.py`)
```sql
credit_report_imports (batch_id PK, user_id, bureau, score, accounts, prev_card_limit, prev_card_balance, card_details_set, imported_at)
credit_accounts (id PK UUID, user_id, account_hash, lender, account_type, kind CHECK(loan|card), account_number, opened, closed,
                 sanctioned, balance, overdue, emi, tenure_months, interest_rate, loan_id (→ loans, nullable), import_batch_id,
                 created_at, updated_at, UNIQUE(user_id, account_hash))
credit_account_history (account_id, month 'YYYY-MM', dpd, PK(account_id, month))   -- days past due per reported month
risk_profile (user_id PK, card_limit, card_balance, updated_at)                     -- from risk_scorer/migrations.py
-- account_hash = sha256(lender | type | account number | opened), lowercased alphanumerics only, so the same account matches across bureaus' layouts
-- Imported loans are ordinary rows in `loans`; their monthly history becomes `loan_payments` (payment_date = first of the month, amount = EMI)
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
- `GET /api/risk-profile`, `PUT /api/risk-profile` — saved credit-card limit/balance for the risk model (JWT)

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
- `GET /api/budget/data` — counts of what is stored for the user (expenses, budgets, imported transactions, learned rules, date range)
- `DELETE /api/budget/month/<YYYY-MM>` — removes that month's expenses, imported transactions, budget and planned categories
- `DELETE /api/budget/all` — body `{"confirm": "DELETE"}` required (400 otherwise); removes all expenses, budgets, imported transactions and learned category rules for the user. Loans, goals, profile untouched

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

### Statement Import (prefix: `/api/import`)
- `POST /statement/preview` — multipart `file` (+ optional `password`) → parsed rows with suggested categories and duplicate flags. 422 + `password_required` for locked PDFs
- `POST /statement/confirm` — `{rows}` (all preview rows, edited; `include:false` to skip) → imports, creates budget expenses for debits, learns category corrections
- `GET /transactions?month=YYYY-MM` — imported transactions
- `GET /recurring` — detected recurring streams (kind, cadence, typical/monthly amount, next date, active) + monthly totals (income / fixed costs / investing)
- `GET /batches` — past imports (batch id, imported date, period, counts, totals), so an import can be undone later
- `DELETE /batch/<batch_id>` — undo one import (removes its transactions and the expenses it created, re-syncs import-set income)
- `confirm` also returns `income_set` {month: amount} and `income_kept_manual` [months]

### Credit Report Import (prefix: `/api/import/credit-report`)
- `POST /preview` — multipart `file` (+ optional `password`) → accounts with history, 24-month late/missed counts, how each will be imported and what it still `needs`. 422 + `password_required` for locked PDFs. Saves nothing
- `POST /confirm` — `{rows, bureau, score}` (rows as edited; `include:false` to skip) → loans, payments, history, card details. Server re-validates and recomputes everything
- `GET ` (no suffix) — past imports + stored accounts with their 24-month counts
- `DELETE /<batch_id>` — undo: removes the accounts that import added, with their loans and payments; restores the previous saved card details

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
- [x] ~~Replace the formula-copying health scorer with a model trained on real outcomes~~ — done 2026-10-03 (§5, §15 #55–#60). Follow-ups:
  - [x] Retirement planner switched to `risk_scorer.assess_user` (2026-10-04).
  - [x] Old model files and `financial_health_scorer.py` deleted (2026-10-04).
  - [x] Card limit/balance saved per user in `risk_profile` (2026-10-04).
  - [x] "Not enough data" / low-confidence states instead of a score from age alone (2026-10-04).
  - [ ] Guidance/investment rules use score thresholds (35/50/65/80) tuned for the old score; they now receive a percentile. Review them.
  - [ ] The dashboard form still asks for food/travel/shopping/savings, which only feed the rule-based panels. Split or relabel it.
  - [ ] No UI to clear saved card details (API only: `PUT /api/risk-profile` with `card_limit: null`).
  - [ ] The user's real statement leaves most spending in "other" and detects no income/rent/EMI, so the model lacks a debt ratio for them. Payment history for the model would come from a credit report (roadmap Phase 3).
  - [ ] Look for Indian outcome data (the model is trained on US borrowers).
- [ ] **ACTIVE ROADMAP — automatic data entry → Financial Digital Twin** (agreed 2026-10-02). Manual entry is why finance apps get abandoned, and the digital twin needs real history:
  1. [x] **Bank statement import** (CSV/XLS/XLSX/PDF incl. password-protected) → preview → categorize → budget expenses. Done 2026-10-02, see §15 #38–#44. ⚠️ Built and tested on SAMPLE statements only; validate with a real, redacted statement from the user before relying on it for a given bank.
  2. [x] **Recurring detection + income** — done 2026-10-02 (§15 #45–#49). Rent/EMI/SIP/bills/salary detected from ≥3 occurrences; monthly income filled from salary credits; new `investment` category; Recurring payments card on the Budget page.
  3. [~] **Credit report → loans** — done 2026-10-04 (§15 #70–#73): bureau PDF → loans + payment history + card details, feeding the risk model. ⚠️ Built on SAMPLE reports in two approximated layouts; needs a real redacted report per bureau. **CAS → mutual funds** (`casparser`) not started.
  4. [ ] **Chat quick-entry** — `add_expense` tool on the chat agent ("spent 450 on lunch").
  5. [ ] **Financial Digital Twin** — safe-to-spend, goal-success probability (Monte Carlo on the user's own history), personal inflation, what-if sliders (see Feature ideas backlog #1–#2).
  6. [ ] **Account Aggregator sandbox** (Setu) — consent flow; the production path (real AA access needs a regulated FIU).
  - Rules: parse in memory, never store files or passwords; always preview before saving; no claimed ML accuracy — categorization is rules + learned user corrections; train a classifier only once real corrections exist.
- [ ] **DEPLOYMENT to AWS (started 2026-10-04, see §17).** Phases 1–2 done (app configurable, containerized, verified locally). Next: Terraform → Ansible (k3s) → Kubernetes manifests → CI/CD → operations. **Nothing has been created on AWS; applying Terraform costs money and needs the user's go-ahead.**
- [ ] **Deferred by user (2026-10-02, "I'll come back to this"):** the Portfolio Optimizer's XGBoost return predictor has R² −0.47 and 0% influence, so it currently adds nothing. Plan: (1) replace it with a next-month **volatility** predictor (volatility clustering is genuinely predictable; it feeds the covariance, so ML would actually move allocations); (2) add a **walk-forward backtest** (rebuild yearly on past-only data; compare return/vol/max drawdown vs all-Nifty and 60/40), run with and without the vol model.
- [ ] **NEXT:** audit the Nudge Engine the way the Portfolio Optimizer was audited — does it run on real user data or demo-seeded spikes, does the Isolation Forest result hold up, is anything fabricated or silently broken?
- [ ] Replace `MainDashboard.jsx` health score widget with Portfolio Summary card (optional)
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

### Financial Health Score Story
> "The health score is a gradient-boosted model trained on 150,000 real borrowers, labelled by whether they actually fell 90 days behind on a payment in the following two years. I picked only inputs my app can supply and whose meaning carries over: age, debt-to-income, late and missed payments, and optional credit-card utilization. In 5-fold cross-validation it reaches AUC 0.858 against 0.836 for logistic regression, and its probabilities are calibrated: when it says 4%, about 4% defaulted. Three design choices matter. I dropped the 'number of credit lines' column because in US data having none signals risk, which would tell a student with no loans to borrow. I added monotone constraints so a what-if can never reward paying late. And the 0-100 score ranks you against borrowers your own age, because the training population is much older than my users. The limits are stated in the UI: it's US data from 2011, and without payment history or card data the model is weak (AUC 0.66). The earlier version of this module trained a model to copy a formula I wrote myself and reported R² 96%, which measured nothing. Replacing it is the part of the project I'd point to."

### Portfolio Optimizer Story
> "The core is Markowitz mean-variance optimization (SLSQP) over 9 Indian asset classes built from real data: NIFTY 50 / Midcap 50 / Smallcap 250 indices, a Nasdaq-100 ETF, a liquid fund's NAV, Gold ETF, COMEX silver in rupees, and a REIT. That's 7 to 23 years each, with Fixed Deposit as the one labeled assumption. Three estimation choices make it robust. First, sample means from short or lucky periods are shrunk toward a risk-based prior, so Silver's 2020s rally or Nasdaq's AI run don't dominate. Second, covariance comes from weekly returns for ~4× more data, weekly rather than daily because silver trades on US hours. Third, there's a 35% per-asset cap. XGBoost predicts next-month returns per asset, and its influence is weighted by its out-of-sample R². Every model scores below zero, so it currently has zero say. That's the Efficient Market Hypothesis showing up honestly on real prices. Along the way we found data problems you only catch by checking: unadjusted stock splits, a liquid ETF whose price ignores its own yield, and a NAV rescaled 100×."

### Nudge Engine Story
> "Isolation Forest runs per-user on their own 16+ week spending history. It doesn't need labeled anomaly data — it learns each user's baseline by itself (unsupervised). A spending week that is very different from that user's personal pattern gets flagged, regardless of whether it's 'expensive' by some global standard."

### Common Viva Q&A
| Question | Strong Answer |
|---|---|
| Why Flask not Django? | Flask gives faster API-centric development with lightweight control for custom ML/business logic |
| Why SQLite? | Zero admin overhead, easy local setup, sufficient for prototyping persistent relational workflows |
| Why gradient boosting for the health score? | It beat the logistic baseline on held-out data (AUC 0.858 vs 0.836), handles missing inputs natively (no income, no card), supports monotone constraints, and gives exact per-prediction explanations (TreeSHAP) |
| Isn't US data wrong for Indian users? | Partly, and the UI says so. Ratios and payment behaviour have no currency; dollar income and the count of credit lines don't transfer, so they were excluded. Probabilities are indicative; the ranking of what hurts you is the reliable part |
| How is security handled? | JWT auth, hashed passwords (werkzeug/bcrypt), protected routes, ownership checks, OTP/email verification |
| How do you prevent SQL injection? | Every query with user input uses `?` parameter binding, so values never become SQL. The few dynamically built queries only interpolate fixed column literals or `?` placeholder lists. Table names (which can't be bound) go through an allowlist check, `_safe_table_identifier()` in `db_utils.py`. Inputs are also type-cast (`float`/`int`/`strptime`), categories are allowlisted, and every update/delete is scoped with `AND user_id = ?` |
| How do users get data in without typing everything? | Upload a bank/UPI statement (CSV/Excel/PDF, even password-protected). A bank-agnostic parser finds the transaction table by column meaning, a rulebook of Indian merchants categorizes UPI narrations, the user reviews a preview, and corrections are learned per merchant. Re-uploads are de-duplicated by transaction hash; any import can be undone. Production path: RBI's Account Aggregator framework |
| Where does the risk model get payment history? | From a credit bureau report the user uploads: each account's month-by-month days past due. The parser finds fields by label rather than by position, so one parser reads different bureaus' layouts; open loans become loans with a payment per month, cards give the utilization, and re-uploading a newer report updates accounts instead of duplicating them. I only had sample reports to build against, and I say so |
| How does what-if work? | Backend predicts both current and modified scenarios, returns score delta and impact label |
| How is explainability addressed? | Return classification labels, financial ratios, warnings, and guidance alongside prediction |
| Is this just ML demo? | No — complete user journey: auth, profile, budget, loans, goals, retirement planner, AI chat assistant |

---

## 14. Known Issues / Gotchas

1. **`.venv` is broken** — built against Python 3.13 (no longer installed). Never activate it. Use `python` from PATH (`C:\Python314\python.exe`).
2. **~~`enhanced_model.pkl` compatibility~~ — OBSOLETE 2026-10-03.** Nothing loads that pickle any more. The risk model is saved in XGBoost's native JSON format, which doesn't break across library versions. If `risk_scorer/models/` is missing, run `python -X utf8 risk_scorer/train_model.py` from `backend/`.
3. **Windows encoding** — use `python -X utf8` flag for any scripts with emoji characters.
4. **Frontend Vite warning** — `default referenced in default didn't resolve at build time` is benign. Build still succeeds (683 modules, 0 errors).
5. **Two `auth.db` files** — one at workspace root (stale/empty), one at `backend/auth.db`. Flask uses `backend/auth.db`. The root one is the empty one that should be deleted if it reappears.
6. **app.py monolith — RESOLVED, merged to `main` 2026-10-02.** All routes live in blueprints (auth, profile_management, budget, loans, chat, calculators, legacy_scorer) following the retirement_planning/portfolio_optimizer/nudge_engine pattern; `app.py` is ~390 lines of setup/wiring. When moving code in future: grep for lazy `from app import <name>` (e.g. `chat_agent.py`'s `execute_tool()`) — that exact class of bug broke chat mid-refactor and was caught only by calling `/api/chat` on a live server, not by import checks.
7. **`retirement_planning/integration_manager.py`** gets the health score from `risk_scorer.service.assess_user` (reads `backend/auth.db` by its own path, not `db_core.DB_PATH`). It raises `IntegrationError` when there isn't enough data; `retirement_planning/api.py` then uses 50.
8. **~~`validation_schemas.py` marshmallow bug~~ — FIXED 2026-10-02.** Marshmallow 4 passes `data_key=` to `@validates` methods; all validators now take `**kwargs` so they run on 3.x and 4.x. Any new `@validates` method needs `**kwargs` too.
9. **~~Personalizer DB queries didn't match `auth.db`~~ — FIXED 2026-10-02.** Fetchers now read `monthly_budgets`, `loans` (not deleted, not matured), `financial_goals`, `expense_entries`. Failures still fall back to "no adjustment" but are logged as `personalizer: ... failed` warnings. If personalization ever seems to do nothing again, grep the server log for that prefix first.
10. **Portfolio Optimizer re-fetch cadence:** the data files are snapshots. Re-run `fetch_real_data.py` + `train_model.py` periodically (needs internet: Yahoo Finance + mfapi.in). REIT is the only short history (2019+); its mean leans on the prior until it accrues more. If Yahoo changes a ticker or mfapi.in is down, `fetch_and_save()` raises and leaves the old CSVs untouched rather than writing partial data.
11. **Windows dev gotchas (from the verification runs):** use `C:\Python314\python.exe` explicitly, because a bare `python3` resolves to the Microsoft Store stub (exit code 49). `/tmp/...` paths inside Python on Windows don't match Git Bash's `/tmp`, so write scratch files to the working dir or the session scratchpad. To stop the dev servers, find the PID with `netstat -ano | grep :5000` and run `taskkill //PID <pid> //F`; `kill %1` doesn't reliably stop the Python child process.
12. **IDE red squiggles on `flask`/`flask_jwt_extended` imports** — the editor's Python language server doesn't know packages live in `C:\Users\saumy\AppData\Roaming\Python\Python314\site-packages` (see item 1). Fixed via `.vscode/settings.json` → `"python.defaultInterpreterPath": "C:\\Python314\\python.exe"`. If squiggles persist, reload the window or run "Python: Select Interpreter" and pick that path manually. Purely cosmetic — doesn't affect running the app.
13. **Global checkbox CSS:** `frontend/src/components/ProfileEditForm.css` sets `input[type="checkbox"] { appearance: none }` globally (Vite bundles it app-wide) and only styles the checked state. Any checkbox without explicit size/border classes is **invisible** when unchecked. Give new checkboxes classes like `w-4 h-4 rounded border border-white/30 bg-white/5` (as `StatementImport.jsx` does), or scope that rule to the profile form.
14. **Binary files and git:** `core.autocrlf=true`. `.gitattributes` marks pdf/xlsx/xls/pkl/images as binary. Add new binary extensions there, or git will CRLF-convert and corrupt them on checkout.
15. **Statement import is validated on SAMPLE files plus one real-shaped export** (`unit_test/fixtures/statements/` are generated samples; on 2026-10-03 the user's `bankstatements.csv`, a 509-row pre-processed export with `date,DrCr,amount,balance,mode,name` columns, failed and was fixed — §15 #50–#54). It is still not a raw bank download. Before trusting a new bank's format, test with a real redacted statement. The parser raises a clear error if it can't find the transaction table rather than guessing. The strongest check on a real file: every row's balance must equal the previous balance ± the amount. The user's file is not committed (real names); tests use a small synthetic CSV in the same layout.
16. **The 422 on `/api/import/statement/preview` is intentional** (password-protected PDF). The browser logs it as a console error; it isn't a JS error.
17. **Pre-existing: 8 test files in `backend/unit_test/` fail at collection** (e.g. `test_profile_service.py`, `test_retirement_repositories.py`, `test_risk_assessment_service.py`), so a bare `pytest unit_test` aborts. Not investigated yet. Run `pytest unit_test/test_statement_import.py unit_test/test_loan_schema.py` (65 pass).
18. **Recurring detection can return two streams for one merchant** (amount clusters), so never key on merchant alone (`RecurringPayments.jsx` keys on merchant + direction + typical amount; `detect_monthly_income` matches merchant + amount range).
19. **Risk-model training data is not in the repo** (`backend/risk_scorer/data/` is git-ignored; 150k rows from OpenML). The trained model and its metadata are committed, so the app runs without it. Training needs internet once.
20. **Health score inputs:** only EMI, rent, income, age, late/missed payments and card utilization move the score. Food, shopping, travel and savings don't (they still feed the rule-based spending charts and advice). The What-If Simulator therefore changes EMI and rent.
21. **Logging — FIXED 2026-10-04.** `app.py` used to log everything at DEBUG, so `pdfminer` wrote every token of an uploaded statement (narrations, amounts, balances) and `botocore` wrote the Bedrock `Authorization: Bearer …` header into `backend.log`, and PDF imports crawled. Now: level INFO by default (`SMARTFIN_LOG_LEVEL=DEBUG` to override), and `NOISY_LOGGERS` (pdfminer, pdfplumber, botocore, boto3, urllib3, s3transfer, PIL, matplotlib) are pinned to WARNING regardless. Add any new library that handles user data or credentials to that tuple. **Old `backend/backend.log` files still contain the key and statement contents**: delete them (stop the server first; Windows locks the file) and rotate the key.
22. **Verifying UI changes while the user's servers are running:** don't kill their port-5000 backend. Start a second copy on 5001 (`waitress.serve(app, port=5001)`) and use Playwright `page.route` to rewrite `:5000` → `:5001`; Vite on 5173 already serves the new frontend code via HMR. The user must restart their own backend to pick up backend changes.
23. **Never test delete flows against `backend/auth.db`.** Set `db_core.DB_PATH` to a copy *before* `from app import app` (see §15 #63) and run that on port 5001. Check the real row counts before and after.
24. **Two processes can listen on port 5000 at once on Windows** (both bind `0.0.0.0:5000`), and the older one keeps answering. If a restart seems to have no effect, run `netstat -ano | grep :5000` and look for more than one PID; `curl localhost:5000/` shows which model is answering.
25. **Never define a component inside another component and render it as JSX.** `ProtectedRoute` lived inside `AppContent`, so every state change made it a new component type and React remounted the whole page, wiping form state (§15 #68). It is now called as a plain function: `element={ProtectedRoute({ children: (...) })}`.
26. **Playwright checks: assert on something that can only appear if the feature worked.** A `waitForSelector('text=Credit-card utilization')` passed while the card data was never submitted, because that driver row is always rendered. Log the request body or assert the value.
27. **Credit report import is validated on SAMPLE reports only** (`unit_test/fixtures/credit_reports/`, generated; the CIBIL-style and Experian-style layouts are approximations from general knowledge, not copied from real reports). Expect to adjust `_LABELS` in `credit_report/parser.py` for a real report: it is a list of label synonyms, so adding one is a one-line change. The parser raises a clear error when it finds no accounts. Never ask the user to paste a real report into the chat; ask for the error and the label wording.
28. **Modals must be portalled to `<body>`** (`createPortal`). The page layouts create stacking contexts, so a `fixed z-50` dialog rendered inside a page sits *below* the site footer (`z-20` in a higher context), which then swallows clicks on the dialog's buttons (§15 #72). `StatementImport.jsx` is not portalled and happens to work on the Budget page; portal it if it ever misbehaves.
29. **Never call `sqlite3.connect` directly in backend code; use `dbapi.connect(path)`.** Otherwise that code silently keeps using a local file when the app runs on PostgreSQL. New SQL must run on both: no `INSERT OR IGNORE/REPLACE`, `PRAGMA`, `sqlite_master`, `date('now')`/`strftime` in SQL, boolean `SUM(...)`, or `ROUND(float, n)`; PostgreSQL also rejects double-quoted string literals and non-aggregated columns missing from `GROUP BY`. Add a call to `unit_test/api_walkthrough.py` for any new endpoint so both databases are compared.
30. **Unknown URLs used to return 500** (the catch-all error handler swallowed 404/405). Fixed 2026-10-04: HTTP errors keep their status. Also: the Nudge Engine has no `POST /api/nudges/scan`; the scan is `GET /api/nudges/` (§5 and §7 list it wrongly).

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

### Session 2026-10-02 (cont.) — automatic data entry, Phase 1: bank statement import (`main`)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 38 | Users must type every expense and loan by hand | No import path existed; manual entry kills adoption | Statement import (CSV/XLS/XLSX/PDF) with preview, auto-categorization, dedupe and undo | User raised it while discussing the digital twin |
| 39 | Every bank's statement layout is different | No shared format (HDFC/SBI/Axis/ICICI differ in headers, date formats, Dr/Cr style, preambles, wrapped rows) | One parser that finds the header row by keyword and maps columns by meaning; day-first dates only; header rows repeated per PDF page skipped; continuation rows rejoined | Designed up front; tested on 4 layouts + a protected PDF, all matching totals exactly |
| 40 | Missing/wrong PDF password produced "Could not open the PDF" instead of a password prompt | pdfplumber wraps pdfminer's `PDFPasswordIncorrect` in its own exception | Detect the wrapped cause → `StatementPasswordRequired` → API 422 + `password_required` → UI shows a password field | First fixture run |
| 41 | `emi` matched "pr**emi**um", `rent` matched "cur**rent**", masked card numbers leaked into merchant names | Substring matching; no token filtering | Whole-word keyword matching; drop tokens with 3+ digits or `XXX` masking | Hand-checked categorization of realistic narrations before writing tests |
| 42 | Re-uploading the same period (even as a different file type) would double-count, but two real ₹568 Zomato orders on the same day must both count | Need stable identity without a bank-provided transaction ID | SHA-256 of date, direction, amount, normalized description and balance, plus an occurrence counter within a file. `UNIQUE(user_id, txn_hash)` + `INSERT OR IGNORE`. The client sends all rows back so the server recomputes identical hashes | Tests: same data as CSV then PDF → 19/19 flagged; identical Zomato rows kept |
| 43 | Include/exclude checkboxes were invisible | `ProfileEditForm.css` globally sets `appearance:none` on all checkboxes and only styles the checked state | Explicit size/border classes on the new checkboxes; documented as gotcha §14 #13 | Playwright screenshot review |
| 44 | Git would corrupt the binary PDF fixtures (and `.pkl` models) on checkout | `core.autocrlf=true`, no `.gitattributes`, so git treated the PDFs as text | `.gitattributes` marking binaries; verified by deleting and re-checking-out the fixtures and rerunning tests | Git's "LF will be replaced by CRLF" warning on commit |

### Session 2026-10-02 (cont.) — automatic data entry, Phase 2: recurring payments + income (`main`)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 45 | After importing, the budget still showed Income ₹0 | Imported credits were stored but nothing turned salary into budget income | `detect_monthly_income` (monthly income streams + salary/stipend/payroll narrations; refunds, cashback and interest excluded) → `sync_income` fills budgets on import, re-syncs on undo. `income_source` column so typed income is never overwritten | Phase 1 browser test (Income ₹0) |
| 46 | SIPs would be booked as loan EMIs | NACH mandates collect both SIPs and loan EMIs, and the rulebook matched "nach" → `emi` | New non-expense `investment` category checked before `emi` (SIP/MF/Zerodha/Groww/Kuvera/NPS/PPF/RD); "RD installment" moved there from "transfer" | Designing the 6-month sample |
| 47 | Monthly totals off (salary ₹44,187/mo) and next dates drifting (Netflix 15th → 16th) | Scaled every stream by 30.44/median-gap and added the median gap to the last date | Calendar-monthly streams (median gap ≥29 days) count 1×/month and repeat on the same day next month (month-end clamped, leap-safe); fixed-length cycles (28-day prepaid) are scaled | First run on the 6-month sample |
| 48 | Salary paid on 30 May made May ₹90,000 and June ₹0 | Income attributed by credit date | A payer's credit in the last 5 days of a month, with none from that payer next month, counts toward next month; `_touched_months` includes following months so June's budget gets it | Same run |
| 49 | Heredoc patch commands failed with "unexpected EOF" | The shell tool chokes on apostrophes inside heredoc bodies (e.g. "month's"), even with a quoted delimiter | Write patch scripts to the session scratchpad with the Write tool and run them | Tooling; nothing had been modified, which was confirmed with `git diff --stat` |

### Session 2026-10-03 — first real-shaped statement (`bankstatements.csv`, 509 rows, Jan 2022 – Oct 2023)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 50 | User's CSV was rejected: "Couldn't find the transaction table" | Header `DrCr` wasn't in the Dr/Cr spellings (only `dr/cr`, `dr|cr`, …), and the file has no narration column, which the parser required: the description is split across `mode` (UPI/ATM/NEFT) and `name` | Dr/Cr headers compared with non-letters stripped; with no narration column, description = mode + counterparty columns | User report; reproduced on the file. Verified: 509 rows, running balance reconciles on every row |
| 51 | Known merchants fell into "other" (`DOMINOSP`, `AMAZONPAY`, `HESCOMBI`) | Whole-word keyword matching (added in #41) can't match names that are run together or cut short | Single-word keywords of 6+ characters also match as a word prefix; short ones (`emi`, `rent`, `jio`, `chai`) stay whole-word. Added `hescom`, `jioinapp`, `bajajfin`, `sbint` | Dry run of the file through the categorizer |
| 52 | Salary not detected, budget income stayed ₹0 | Salary arrives as a bare `NEFT` with no payer name, sharing one merchant bucket with unrelated NEFT credits, so the bucket failed the stable-amount test | When a bucket isn't recurring as a whole, split it into amount clusters (neighbours within 15%) and test each; income counts only credits inside the stream's amount range | Same dry run: `detect_monthly_income` returned `{}` |
| 53 | Salary cluster still rejected | Real pay days move (3rd, 21st, 7th…): only 68% of gaps were 25–36 days, below the 75% bar | Monthly streams also qualify if they appear in ≥75% of the calendar months they span, about once a month | Computed the gaps by hand |
| 54 | Irregular Uber rides became a "monthly bill" | #52 + #53 together: slicing random spending by amount manufactures a once-a-month pattern | Amount clusters need a tighter amount spread (CV ≤ 0.15 instead of 0.35) | Existing test `test_detects_exactly_the_recurring_streams` failed |

Result on the file: salary ~₹52k/month, a ₹26,286 monthly debit to `HDFCBANK`, an ₹11,500 monthly credit; income filled for 21 months; re-upload 509/509 duplicates; undo clean. Limit that rules can't fix: ~99% of the money out is person-to-person UPI, cheques and ATM cash with 8-character names, so it stays "other" until the user categorizes it in the preview (corrections are learned per merchant).

### Session 2026-10-03 (cont.) — health score replaced with a real-outcome risk model (`main`, uncommitted)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 55 | User: "sick of this", wants ML that is genuine | The health scorer learned labels produced by our own formula; R² 96% measured only how well it copied us | New `risk_scorer/`: XGBoost on 150k real borrowers with real distress labels, evaluated against a logistic baseline | User request |
| 56 | "Number of open credit lines" would punish users with no loans | US lines include credit cards; zero lines is a rare, risky group there (21% distress vs 5–6%) | Excluded it and real-estate loans; dollar income excluded too (enters only via the ratio) | Tabulated distress rate per feature value before training |
| 57 | With the 4 inputs SmartFin had, ML barely beat the baseline (0.828 vs 0.820) | Payment counts carry most of the signal and are nearly linear | Added optional card utilization (0.858 vs 0.836); one model trained with utilization hidden on half the rows so users without a card still work | Feature-set comparison across 7 sets × 3 models |
| 58 | A 22-year-old with a clean record scored 19/100 | Score was a percentile against the whole reference population, whose median age is 52 and where young borrowers are riskier | Score = percentile within the user's own age band; absolute risk shown separately | Scored a set of realistic profiles before integrating |
| 59 | A user with no age scored 85 | The training data has no missing ages, so the tree's default branch for a missing age is arbitrary | Age is never passed as missing: request → profile → 30 | Same profile check ("nothing known" came out best) |
| 60 | What-If Simulator would always show "no change" | Its two inputs were shopping and savings, which the new model doesn't use | Simulator now changes EMI and rent | Read the component after the model's inputs were fixed |

### Session 2026-10-03 (cont.) — stale server, deleting budget history (`main`, uncommitted)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 61 | After restarting the backend the user was still scored by the old 8-factor model | Two Python processes were bound to port 5000: the user's fresh one and a stale one from hours earlier that kept answering | Killed the stale PID; `GET /` then reported the XGBoost model | `curl localhost:5000/` returned "8-factor enhanced"; `netstat` showed two listeners |
| 62 | A user could not delete budget history: only one expense at a time, and an import could be undone only on the screen shown right after importing | No bulk-delete endpoints; no list of past imports | `budget/data_management.py` + `DELETE /api/budget/month/<m>`, `DELETE /api/budget/all` (typed confirmation), `GET /api/budget/data`, `GET /api/import/batches`; `BudgetDataManager.jsx` card | User asked before importing a real statement |
| 63 | UI check of destructive actions risked the real database | The verification backend would normally open `backend/auth.db` | Served a copy: set `db_core.DB_PATH` before importing `app`; real DB row counts identical before and after (404 / 27 / 509) | Planned |
| 64 | Deleting a month but leaving its imported transactions would make a re-import skip them as duplicates | Dedupe is by `bank_transactions.txn_hash` | Month delete removes that month's `bank_transactions` too; test confirms the month re-imports cleanly | Design review; covered by `test_deleted_month_can_be_imported_again` |

Privacy answer given to the user (2026-10-03): statement files and PDF passwords are not stored; transactions are stored unencrypted in `backend/auth.db`; `auth.db`, `.env`, `*.log` are git-ignored; the import makes no network calls; the chat agent and advice panels would send expense data to AWS Bedrock if the key worked; the backend binds `0.0.0.0`. Offered and not yet done: bind to `127.0.0.1`, git-ignore statement files, lower the log level.

### Session 2026-10-04 — debug logging leaked statement contents (`main`, uncommitted)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 65 | Importing a real PDF statement flooded the console and `backend.log` with thousands of `pdfminer ... DEBUG` lines, including the transactions themselves, and was slow | Root logger at DEBUG with a file handler; third-party libraries inherit it | Default INFO via `LOG_LEVEL`; data/secret-handling libraries pinned to WARNING in `NOISY_LOGGERS`. Sample PDF preview: 0 pdfminer lines, 0 `Bearer` occurrences, 0.24 s | User pasted the log output |

### Session 2026-10-04 (cont.) — finishing the risk model (`main`, uncommitted)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 66 | "Run Analyzer from This Month" gave the user "Excellent 88.6" on their real data | That month had no income and nothing categorized as rent/EMI, no loan payments, no card: the model had only age, and an empty payment record was read as a clean one | Button removed (user's request). Model side: `confidence` levels; no score when payment history, card data and debt ratio are all unknown | Ran the endpoint on the user's month and read the features it was given |
| 67 | Card details had to be retyped for every score | Nowhere to store them | `risk_profile` table + `GET/PUT /api/risk-profile`; the score form saves and pre-fills them | Planned follow-up |
| 68 | **Dashboard form was wiped after every "Analyze"**, so a second analysis never submitted (required fields empty, browser validation blocked it silently) | `ProtectedRoute` was a component defined inside `AppContent`; each `loading`/`result` state change produced a new component type and React remounted the page. Pre-existing, on all 13 protected routes | Call it as a plain function. Added `key={result.timestamp}` to `WhatIfSimulator`, whose stale state the remount had been hiding | Playwright: step 3 of the state check produced no `POST /api/predict` at all; request logging showed two posts for three clicks |
| 69 | Retirement readiness used the old 8-factor rule formula for 20% of its score | `integration_manager` called `FinancialHealthScorer` | Uses `assess_user`; old scorer, its test, the pickle, training script and dataset deleted | Planned follow-up |

### Session 2026-10-04 (cont.) — credit report import, roadmap Phase 3 (`main`, uncommitted)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 70 | The risk model's main inputs (late/missed payments, card utilization) had to be typed by hand, and a user with no loan records got "not enough data" | Nothing brought credit history into SmartFin | `credit_report/`: bureau PDF → accounts → loans + `loan_payments` + `credit_account_history` + `risk_profile`; `user_history` reads all of it | Planned (roadmap Phase 3) |
| 71 | Bureaus use different layouts and no real report was available | — | One label-driven text parser (synonym list per field, account starts at each lender label) that handles both a status-row-over-month-row history and a year × month grid; verified to extract identical accounts from both sample layouts | Designed up front |
| 72 | Dialog buttons unclickable on the Loans page | Footer overlaid the dialog (stacking context, §14 #28) | `createPortal(..., document.body)` | Playwright: "footer intercepts pointer events" |
| 73 | Re-uploading a report (or the same person's report from another bureau) would duplicate loans and double-count late payments | Needs account identity across files | `account_hash` on normalized lender/type/number/opening date; existing accounts are updated and only new months added | Test: Experian-layout file after the CIBIL-layout one → 0 added, 5 updated, 0 new payments |

Also this session: 5 commits on `main` (statement-import fixes, risk model, budget data management, remount fix, docs); deleted `backend/backend.log` and a 167 MB `backend.log` at the repo root that held the Bedrock key and a full pdfminer trace of the user's statement. **The user still has to rotate the Bedrock key.**

### Session 2026-10-04 (cont.) — deployment, phases 1–2 (`main`, uncommitted)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 74 | The database path was hardcoded in six places relative to `backend/` | Each module computed its own `auth.db` path | One `SMARTFIN_DATA_DIR` in `db_core` (`DATA_DIR`, `DB_PATH`, `UPLOAD_DIR`); the other five sites import it | grep for `auth.db` before containerizing |
| 75 | `/forgot-password` and `/verify-email` are both React pages and backend POST routes | Auth routes live at the top level, not under `/api` | nginx forwards those two by method (non-GET → backend) and the other top-level routes by an exact list; `test_deployment.py` fails if a backend route is missing from the list | Compared Flask's `url_map` with the React routes |
| 76 | Reloading a deep link (`/profile/edit`) would 404 its scripts | Vite `base: './'` (for GitHub Pages) makes asset paths relative | `VITE_BASE=/` in the container build; default unchanged | Reasoned from the config, then checked the built `index.html` in the container |
| 77 | Three components called `http://127.0.0.1:5000` directly | Bypassed `API_BASE_URL` | Export `API_BASE_URL` from `api.js` and use it; `??` instead of `||` so an empty value means "same address" | grep for hardcoded hosts |
| 78 | Port 8080 on this machine is taken by another program on `[::1]` | — | Compose publishes 8088; test with `127.0.0.1`, not `localhost` | `netstat` before starting the stack |

### Session 2026-10-04 (cont.) — PostgreSQL migration (`main`, uncommitted)

| # | Problem | Root cause | Fix | How it was caught |
|---|---|---|---|---|
| 79 | The app could only run on a SQLite file | 23 direct `sqlite3.connect` calls, a few SQLite-only statements | `dbapi.py` adapter + portable SQL (§17) | Planned; user decided on PostgreSQL/RDS |
| 80 | **On PostgreSQL every statement was committed immediately**; `rollback()` did nothing, so a failed multi-step import would have left partial data | The per-statement savepoint used psycopg's `connection.transaction()`, which is a full transaction (commit on exit) when none is open | Savepoints issued as plain SQL (`SAVEPOINT` / `RELEASE` / `ROLLBACK TO`) inside the implicit transaction | My own test asserted a table created before `rollback()` was gone, and it wasn't. The 75-call walkthrough had passed identically: it has no failing multi-step write |
| 81 | Unknown URLs answered 500 | Catch-all `@app.errorhandler(Exception)` also caught `NotFound` | Pass `HTTPException` through with its own status | A wrong path in the walkthrough returned 500 |
| 82 | A Dockerfile line ended in a literal `\n` | Wrote the edit through a shell heredoc that didn't interpret the escape | Fixed with the Edit tool | Read the file back |

---

## 17. Deployment (AWS) — plan and status

**Decisions (user, 2026-10-04):** Kubernetes on EC2 using **k3s** (not EKS: about $20–40/month instead of $130–160, and Ansible gets a real job); chosen to learn/show the tools, not because the app needs it. ~~SQLite on a persistent volume, one backend replica~~ → **changed the same day: "we will migrate to postgres, so plan accordingly"**. PostgreSQL is now part of the deployment and comes **before** Terraform/Kubernetes, because it changes what gets provisioned. No custom domain yet.

**Tools on the user's machine:** Docker Desktop 29.5 (must be started), `kubectl`, Terraform, AWS CLI with working credentials, WSL Ubuntu (for Ansible; not installed yet). No helm/k3d/kind.

| Phase | What | Status |
|---|---|---|
| 1 | App configurable from the environment | ✅ 2026-10-04 |
| 2 | Docker images + compose, tests inside the image | ✅ 2026-10-04 |
| 3 | **PostgreSQL migration** | ✅ 2026-10-04 (details below) |
| 4 | Uploads (profile pictures) to S3, so more than one backend replica can run | ⬜ |
| 5 | Terraform: VPC, EC2, security groups, ECR, **RDS PostgreSQL** (or none if Postgres runs in-cluster), S3 (uploads, backups, Terraform state), IAM role (Bedrock, ECR pull, S3), secrets | ⬜ |
| 6 | Ansible: install/harden k3s on the instance | ⬜ |
| 7 | Kubernetes manifests: backend Deployment (**2 replicas**, no data volume, probes on `/healthz`), frontend Deployment, Services, Ingress, Secret with `DATABASE_URL` | ⬜ |
| 8 | GitHub Actions: tests on SQLite **and** PostgreSQL → build → push to ECR → roll out | ⬜ (existing `deploy.yml` publishes the frontend to GitHub Pages) |
| 9 | Operations: CloudWatch logs/alarms, database restore test, teardown script, HTTPS | ⬜ |

**PostgreSQL migration — done 2026-10-04.** Measured scope beforehand: 21 files importing `sqlite3`, 23 connect sites, 244 SQL statements, 21 tables. It turned out far smaller than estimated because almost all of the SQL was already portable; the work was one adapter plus eight statement rewrites.

How it works (`backend/dbapi.py`):
- `dbapi.connect(path)` is the only way a database is opened (all 23 former `sqlite3.connect` sites call it). With `DATABASE_URL=postgresql://…` and `path` being the app's database it returns a `PgConnection`; any other path (tests' temp files) still gets plain SQLite.
- `PgConnection`/`PgCursor` make psycopg 3 look like `sqlite3`: `?` placeholders (literal `%` escaped, `?` inside quotes left alone), rows readable by index and by name, `lastrowid` (via `lastval()`), `executescript`, `True/False` → `1/0`, `Decimal` → `float`.
- Errors are re-raised as the `sqlite3` classes the code already catches (40 `except sqlite3.Error`, the duplicate-user `IntegrityError`), so no handler changed. A unique violation's message starts with "UNIQUE constraint failed".
- **Each statement runs inside a savepoint**, so a failed statement doesn't abort the whole transaction (SQLite semantics; code such as `user_history` relies on carrying on after a missing-table error). The savepoints are issued as plain SQL: psycopg's `connection.transaction()` *commits* when used outside a transaction, which silently turned every statement into its own commit in the first version (§15 #80).
- `CREATE TABLE` written for SQLite is translated: `INTEGER PRIMARY KEY [AUTOINCREMENT]` → identity column, `REAL` → `DOUBLE PRECISION` (PostgreSQL's `REAL` is 4 bytes, too coarse for money), `DEFAULT CURRENT_TIMESTAMP` → the same `YYYY-MM-DD HH:MM:SS` text SQLite produces. Dates and timestamps stay ISO text on both.
- Helpers for the genuinely different bits: `table_exists`, `table_names`, `column_names`, `add_column_if_missing`, `is_postgres`.

Statements rewritten to portable SQL: `INSERT OR IGNORE` ×2 → `ON CONFLICT (…) DO NOTHING`; `INSERT OR REPLACE` → `ON CONFLICT (user_id) DO UPDATE`; `SUM(a >= b)` ×2 → `SUM(CASE WHEN … THEN 1 ELSE 0 END)`; `ROUND(SUM(…), 2)` → `ROUND(CAST(… AS NUMERIC), 2)`; `date('now')` ×2 → a bound parameter; `PRAGMA table_info` / `sqlite_master` → the helpers.

What changes on PostgreSQL: the 17 foreign keys and all `CHECK` constraints are enforced (SQLite never enforced the foreign keys), and money columns are 8-byte floats on both.

Verification: `unit_test/api_walkthrough.py` drives 75 API calls as one user (auth, profile, goals, budget, statement import + undo, delete month/all, loans + payments + metrics, credit report import + re-import + undo, score/what-if, portfolio, nudges, retirement, calculators). `unit_test/test_postgres.py` runs it on SQLite and on PostgreSQL and requires the transcripts to be **identical**: they are, with the same 21 tables on both. The compose stack (PostgreSQL container) passes the same black-box check as before and keeps its data across `down`/`up`.

Run the PostgreSQL tests locally (they **empty the target database's `public` schema**):
```bash
docker start smartfin-pg || docker run -d --name smartfin-pg -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=smartfin -p 127.0.0.1:55432:5432 postgres:17-alpine
set TEST_DATABASE_URL=postgresql://postgres:dev@127.0.0.1:55432/smartfin
python -X utf8 -m pytest unit_test/test_postgres.py
```

Not done / known limits:
- **No connection pool**: one PostgreSQL connection per request. Fine locally; on RDS (TLS handshake per request) add `psycopg_pool` before load matters.
- The savepoint per statement costs two extra round trips per query.
- The conn-based unit tests (statement import, credit report, budget data) still run on SQLite only; PostgreSQL coverage of those paths is through the walkthrough.
- No copy of existing local data into PostgreSQL (deployments start empty by design).
- Chat with Bedrock was not exercised on either database (no working key).

**Decided by the user (2026-10-04):** PostgreSQL runs on **RDS**; region **ap-south-1** (Mumbai). SQL over NoSQL was discussed and settled (relational, transactional data; JSONB for the few free-form fields). Local development keeps SQLite as the default.

**Environment variables the backend reads**
| Variable | Meaning |
|---|---|
| `DATABASE_URL` | `postgresql://user:password@host:5432/db` to use PostgreSQL. Unset = SQLite file in the data folder |
| `SMARTFIN_DATA_DIR` | Folder for `auth.db` (SQLite only) and `uploads/`. Default: `backend/`. In the image: `/data` (a volume) |
| `SMARTFIN_ENV` | `production` makes the app refuse to start without a real `JWT_SECRET_KEY` (32+ chars, not the dev default) |
| `JWT_SECRET_KEY` | Signs login tokens |
| `SMARTFIN_CORS_ORIGINS` | Extra allowed origins, comma-separated. Not needed when site and API share an address |
| `SMARTFIN_LOG_FILE` | Log file path; empty = stdout only (containers). Default `backend.log` |
| `SMARTFIN_LOG_LEVEL` | Default `INFO` |
| `AWS_REGION`, `AWS_BEARER_TOKEN_BEDROCK`, `BEDROCK_MODEL_ID`, `SMARTFIN_AI_GUIDANCE_ENABLED`, `TWILIO_*` | Optional integrations |

Frontend build-time: `VITE_API_BASE_URL` (empty string = same address), `VITE_BASE` (`/` in the container). Frontend run-time: `BACKEND_URL` (nginx upstream).

**How requests flow in the containers:** browser → frontend nginx (port 80) → static files, or → backend:5000 for `/api/*`, `/uploads/*`, the top-level auth routes and `/healthz`. The backend is never exposed directly. In Kubernetes the Ingress will point only at the frontend Service.

**Verified 2026-10-04 (local Docker):** 147 tests pass inside the Linux image; through `http://127.0.0.1:8088`: site, deep link, cached assets with no localhost address baked in, `/healthz`, GET vs POST on `/forgot-password`, register → login → `/api/predict` (risk model) → portfolio frontier (real data files present) → 401 without a token; data survives `docker compose down/up`; the backend runs as a non-root user; the image contains no `auth.db`, `.env`, key file or logs.

**Rules**
- The local `backend/auth.db` holds the user's real bank statement. It must never enter an image, the repo or AWS; deployments start with an empty database. `backend/.dockerignore` enforces this for images: keep it that way.
- More than one backend replica needs PostgreSQL (done) **and** uploads on S3 (phase 4, not done): until then keep one replica.
- Backend image is about 1 GB (pandas, scipy, scikit-learn, xgboost, yfinance). Fine for now; trim later if pulls are slow.

---

## 16. Change Log (most recent first)

| Date | Agent/Tool | Change |
|---|---|---|
| 2026-10-04 | Claude Code (Opus 5.5) | PostgreSQL migration (deployment phase 3). New `backend/dbapi.py`: one `connect()`; with `DATABASE_URL` set, a psycopg 3 connection that behaves like `sqlite3` (placeholders, rows by name, `lastrowid`, sqlite3 exception classes, per-statement savepoints, DDL translation). All 23 connect sites use it; 8 SQLite-only statements rewritten. `unit_test/api_walkthrough.py` (75 API calls) gives identical transcripts on SQLite and PostgreSQL; `test_postgres.py` enforces that. Compose now runs a PostgreSQL container; stack re-verified. Fixed 404→500 handler. `psycopg[binary]==3.3.6` added. 157 tests (155 + 2 PostgreSQL-only that skip without `TEST_DATABASE_URL`; 10/10 with it). Earlier: phases 1–2 committed as `ab8ebae`; decisions RDS + ap-south-1. Not committed. §1, §3, §14 #29–#30, §15 #79–#82, §17 |
| 2026-10-04 | Claude Code (Opus 5.5) | Plan change, no code: the user decided to migrate to PostgreSQL. §17 re-ordered (migration and S3 uploads now come before Terraform/Ansible/Kubernetes) and the migration's scope measured (21 files, 23 connect sites, 244 statements, ~26 tables, 53 test files). Deployment phases 1–2 are still uncommitted |
| 2026-10-04 | Claude Code (Opus 5.5) | Deployment phases 1–2 (§17). App made configurable (`SMARTFIN_DATA_DIR`, `SMARTFIN_ENV` + JWT secret check, `SMARTFIN_CORS_ORIGINS`, `SMARTFIN_LOG_FILE`, `/healthz`), hardcoded DB paths and frontend hosts removed, `backend/requirements.txt` pinned to what runs. Added `backend/Dockerfile` (test + runtime stages, non-root), `frontend/Dockerfile` + `nginx.conf.template` (serves the app, forwards API routes), `docker-compose.yml`, `.dockerignore` files, `unit_test/test_deployment.py`. 147 tests pass in the image; stack verified end to end on port 8088. Nothing created on AWS. Also committed the credit report import (`67c7e47`). §2, §3, §12, §15 #74–#78, §17 |
| 2026-10-04 | Claude Code (Opus 5.5) | The user's real CIBIL report failed to import: the PDF is image-only (4.8 MB, 20 characters of text), so no label fix can help; it needs OCR, which is not installed (no Tesseract, no OCR Python package; `pypdfium2` and `PIL` are present for rendering). Added `CreditReportNoTextError` with a plain message instead of "couldn't find any credit accounts", and `credit_report/describe_layout.py`: a CLI the user runs locally that prints a REDACTED layout skeleton (digits → 9, non-vocabulary words → x) or, for image PDFs, page/picture/text-object counts. Use it whenever a real report or its labels are needed; never ask for the report itself. 46 credit-report tests (145 total). OCR support is an open decision for the user |
| 2026-10-04 | Claude Code (Opus 5.5) | Credit report import (roadmap Phase 3, loans half). `backend/credit_report/` (parser, service, api, migrations), `CreditReportImport.jsx` + button on the Loans page, 4 client calls in `api.js`, `risk_scorer.user_history` extended to count imported account history. Password-protected PDFs, preview with editable EMI/tenure/rate, server-side re-validation, re-import updates, undo restores previous card details. 44 new tests (143 pass) on generated SAMPLE reports in two layouts; browser-verified on a DB copy (before: "not enough data"; after import: scored from 5 late + 1 missed + 28% utilization with nothing typed; undo clean; 0 console errors). Earlier in the session: committed all prior work in 5 commits, deleted the old logs. §3, §5, §6, §7, §12, §14 #27–#28, §15 #70–#73 |
| 2026-10-04 | Claude Code (Opus 5.5) | Risk model finished: confidence levels (`good`/`limited`/`insufficient`, no score from age alone) across `/api/predict`, `/api/whatif` (shared `compare_scores`) and the chat tools; saved card details (`risk_profile`, `GET/PUT /api/risk-profile`, form pre-fill); `assess_user` from records and the retirement planner switched to it; deleted `financial_health_scorer.py`, its test and `data/` (old pickle, training script, dataset). Fixed a pre-existing remount bug (`ProtectedRoute` defined inside `AppContent`) that wiped the dashboard form after every analysis. 99 tests pass (10 new). Verified through the real app on a DB copy and in a browser: three score states, card save + reload, all 10 pages render, logged-out redirect intact, 0 page errors. §5, §7, §12, §14 #7 #25 #26, §15 #66–#69 |
| 2026-10-04 | Claude Code (Opus 5.5) | Removed the "Run Analyzer from This Month" button and its result panel from `BudgetManager.jsx` at the user's request (on real imported data it returned "Excellent" from age alone: no income, rent or EMI categorized, no payments, no card). `POST /api/predict/from-budget` and `api.predictFromBudget` still exist but nothing in the UI calls them; the chat tool `analyze_budget_data` still uses the same service. Open issue: the score should say "not enough data" when debt ratio, payment history and card data are all missing |
| 2026-10-04 | Claude Code (Opus 5.5) | Logging fix in `backend/app.py`: INFO by default (`SMARTFIN_LOG_LEVEL` to override), pdfminer/pdfplumber/botocore/boto3/urllib3 pinned to WARNING so uploaded statements and the Bedrock key are no longer written to `backend.log`. Verified by previewing a sample PDF through the app. Existing log files still hold old data until deleted. §14 #21, §15 #65 |
| 2026-10-03 | Claude Code (Opus 5.5) | Budget history can now be deleted. Backend: `budget/data_management.py`, `GET /api/budget/data`, `DELETE /api/budget/month/<YYYY-MM>`, `DELETE /api/budget/all` (needs `{"confirm":"DELETE"}`), `GET /api/import/batches`. Frontend: `BudgetDataManager.jsx` "Manage data" card at the bottom of the Budget page (past imports with undo, delete this month, delete everything behind a typed confirmation). All deletes scoped to the logged-in user. 5 new tests (89 pass). Browser-verified against a copy of the database; real DB unchanged. Also killed a stale second backend on port 5000 that was still serving the old scorer. §7, §14 #23–#24, §15 #61–#64 |
| 2026-10-03 | Claude Code (Opus 5.5) | Replaced the financial health score. New `backend/risk_scorer/` (fetch, features, train, model, service): XGBoost classifier on Give Me Some Credit (149,999 real borrowers, real 2-year distress labels), 5 transferable features, monotone constraints, 5-fold CV AUC 0.858 vs logistic 0.836 (0.828 vs 0.820 without card data), calibrated. Score = percentile within age band; drivers from TreeSHAP. Wired into `/api/predict`, `/api/predict/from-budget`, `/api/whatif`, `/api/model-info` and the 3 chat tools; late/missed counts and age come from the user's own records. Frontend: risk + drivers + model disclosure in `ScoreDisplay.jsx`, optional inputs in `FinancialForm.jsx`, What-If now on EMI/rent. 19 new tests (84 pass). Verified through the real Flask app (routes + chat tools) and a Playwright run against a second backend on 5001, 0 console errors. Not changed: retirement planner still uses the old rule-based scorer; old model files left in `data/`. §5, §12, §14 #19–#22, §15 #55–#60 |
| 2026-10-03 | Claude Code (Sonnet 5.5) | Budget page history: month picker with prev/next/"This month" inside the expense-history section (shares the page's `month` state), plus filters (text search on note/category, category, source manual/import, min/max amount, clear-all). Cause of "can't see history": page opens on the current month, imported data was 2022-01..2023-10. "Failed to fetch budget summary" = backend not running (port 5000). Frontend build passes; not yet checked in a browser. Only `BudgetManager.jsx` changed |
| 2026-10-03 | Claude Code (Opus 5.5) | First real-shaped statement from the user failed to import; fixed. Parser accepts `DrCr`-style headers and files with `mode` + `name` columns instead of a narration. Categorizer matches long keywords as word prefixes. Recurring detection gained amount-cluster and calendar-month fallbacks (nameless NEFT salary on a moving pay day), with a tighter amount limit for clusters. 10 new tests (65 pass). Also restored the truncated "Deferred by user" line in §12. §15 #50–#54, §14 #15, #17, #18 |
| 2026-10-02 | Claude Code (Opus 5.5) | Phase 2 of automatic data entry: recurring-payment detection (`statement_import/recurring.py`, `GET /api/import/recurring`, `RecurringPayments.jsx` card), salary-based monthly income fill with `monthly_budgets.income_source` (manual income never overwritten; undo re-syncs), new `investment` category for SIPs/MFs. New 6-month sample statement; 11 new tests (55 total pass); browser-verified: income ₹45,000 filled for 6 months, exactly 7 real streams detected, 0 console errors |
| 2026-10-02 | Claude Code (Opus 5.5) | Phase 1 of automatic data entry: bank statement import (`backend/statement_import/`, `StatementImport.jsx`, button on the Budget page). Bank-agnostic CSV/XLS/XLSX/PDF parser (password-protected PDFs), Indian-merchant categorizer + learned user corrections, hash-based dedupe, server-side re-validation, undo. New tables `bank_transactions`, `merchant_category_overrides`, column `expense_entries.source`. 32 new tests on generated sample statements (44/44 total pass); verified live with curl + two Playwright runs. Added `.gitattributes`. Roadmap phases 2–6 recorded in §12 |
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

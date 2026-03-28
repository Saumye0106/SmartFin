# SmartFin Project Viva Guide

Last updated: March 28, 2026
Repository: smartfin-copy

## 1. Executive Summary

SmartFin is an end-to-end personal finance platform focused on students and early-career users. It combines:
- A React web app for user interaction and visualization
- A Flask backend API for business logic and data access
- A machine learning model for financial health scoring
- SQLite for persistent user/application data
- Optional AI assistance (Amazon Bedrock/Nova) for conversational financial guidance

In one line: SmartFin helps users track money behavior, evaluate financial health, plan goals/retirement, and receive actionable recommendations.

## 2. Problem Statement and Goal

Many users (especially students) do not have a formal way to:
- Measure financial health objectively
- Understand spending quality and debt burden
- Simulate improvements before making real financial decisions

This project solves that by providing:
1. Financial health score (0-100)
2. Category-based interpretation
3. Guidance and risk signals
4. Goal, budget, loan, and retirement tools
5. AI chat interface for natural-language interaction

## 3. What Is Built (Functional Scope)

### Core features implemented

1. Authentication and user session management
- Register/login with JWT
- Token refresh
- Forgot password flow
- Email verification
- Phone update and OTP-related flows

2. Financial health analysis
- ML-based prediction endpoint
- Score classification (Poor to Excellent)
- Spending pattern analysis (expense ratio, savings ratio, EMI burden)
- Guidance, anomaly/risk indicators, and investment suggestions

3. What-if simulation
- Compare current vs modified financial scenarios
- Score delta and impact label (positive/negative/neutral)

4. Profile and goals
- User profile creation, fetch, update
- Profile picture upload/delete
- Goal CRUD (create/read/update/delete)

5. Budget tracker
- Monthly budget setup
- Category allocations
- Expense CRUD
- Monthly summary and analysis-input generation
- Direct prediction from budget data

6. Loan management
- Loan CRUD with ownership checks
- Payment history tracking
- Loan metrics endpoint (diversity/payment/maturity)

7. Investment calculators
- SIP calculator
- Lumpsum calculator

8. Retirement planning module
- Corpus calculation
- Required monthly savings
- Readiness score
- Scenario creation/comparison
- Recommendations/export

9. AI chat assistant
- Chat endpoint with persistent session history
- Tool-based data access for profile, budget, loans, goals, projections
- Widget-capable responses in frontend chat UI

## 4. System Architecture

## High-level architecture

1. Frontend (React + Vite)
- Handles routes/pages/components
- Calls backend APIs via Axios service layer
- Maintains auth token in local storage

2. Backend (Flask)
- Exposes REST APIs
- Performs validation, business rules, DB operations
- Loads ML model and runs inference
- Integrates retirement and chat modules

3. Data Layer (SQLite)
- Stores users, profile, goals, budgets, expenses, loans, payments, chat sessions, etc.

4. ML Layer
- Gradient Boosting model loaded via joblib
- Produces financial health score and metadata

5. AI Layer (optional)
- Bedrock-backed chat orchestration (Nova model)
- Calls internal tools/functions and returns user-facing responses

## Request flow example (predict)

1. User fills data in frontend
2. Frontend calls POST /api/predict
3. Backend validates payload
4. Backend runs ML prediction
5. Backend computes classification/patterns/guidance
6. JSON response returned to frontend
7. UI renders score cards/charts/panels

## 5. Technology Stack

### Frontend
- React 19
- React Router DOM 7
- Axios
- Recharts
- Tailwind CSS
- Vite (rolldown-vite package alias)
- ESLint

### Backend
- Python 3.11
- Flask 3.1
- Flask-CORS
- Flask-JWT-Extended
- Waitress (WSGI serving)
- Marshmallow (validation support)

### Data and ML
- SQLite
- NumPy
- Pandas
- scikit-learn (Gradient Boosting Regressor)
- joblib

### Integrations
- Twilio (OTP/verification flows)
- python-dotenv
- boto3/botocore (Bedrock integration)

### Testing and quality dependencies
- pytest
- hypothesis

## 6. Current Frontend Structure and User Flow

### Main route flow

1. Landing page (/)
2. Authentication (/auth)
3. Protected dashboard and feature routes:
- /dashboard
- /profile
- /goals
- /risk-assessment
- /sip-calculator
- /loans
- /retirement
- /budget
- /chat

### Important frontend design points

1. Service abstraction
- All API calls are centralized in frontend/src/services/api.js

2. Auth handling
- JWT token stored as sf_token
- Axios default Authorization header set after login
- Interceptor handles 401 and redirects to /auth

3. Error handling
- Error boundary wrappers around key protected pages

4. Chat UX
- Chat component supports dynamic tool widgets like score, what-if, retirement, loans, goals

## 7. Backend Design and Modules

### Main backend file
- backend/app.py is the central API layer and app bootstrap

### Key backend responsibilities

1. App initialization
- Logging setup
- CORS configuration
- JWT setup
- Model loading from data/enhanced_model.pkl

2. Database initialization
- Creates tables if absent
- Adds constraints and indexes

3. Endpoint groups
- Auth and verification endpoints
- Financial prediction endpoints
- Profile/goals endpoints
- Budget endpoints
- Loan and payment endpoints
- Calculator endpoints
- Chat endpoints
- Retirement blueprint registration

### Additional backend modules

- guidance_engine.py: deterministic + optional AI-powered recommendation engine
- financial_health_scorer.py: weighted scoring model with loan dimensions
- chat_agent.py: LLM tool orchestration for conversational features
- retirement_planning/*: isolated domain package for retirement workflows

## 8. Database Design (Implemented)

Core tables visible in backend initialization include:
- users
- password_reset_tokens
- users_profile
- financial_goals
- monthly_budgets
- budget_categories
- expense_entries
- loans
- loan_payments
- loan_metrics
- chat_sessions

### Design choices

1. Relational references with foreign keys
- Data ownership and cascade behavior preserved

2. Constraints at DB level
- Positive amount checks, enum-like checks, age/risk bounds

3. Mixed identifiers
- Integer IDs for users
- UUID-style text IDs for many entities

4. Chat persistence
- conversation_json stored per session_id/user_id

## 9. ML Model and Scoring Logic

### Model used in runtime
- Enhanced model loaded from data/enhanced_model.pkl
- Metadata includes R2 score printed during startup

### Inputs seen in runtime prediction path
Common features include:
- income
- expenses (derived or direct)
- savings
- emi
- age
- has_loan
- loan_amount
- interest_rate

### Outputs
- Numeric score 0-100
- Classification category and description
- Spending patterns and risk flags
- Guidance and investment recommendations

### Business interpretation
This is not only a raw ML prediction. The backend enriches the score with deterministic explainability-friendly outputs (ratios, warning signals, guidance), making it suitable for educational use in a minor project viva.

## 10. API Surface (Major Endpoints)

### Health and model
- GET /
- POST /api/predict
- POST /api/predict/from-budget
- POST /api/whatif
- GET /api/model-info

### Chat
- POST /api/chat
- POST /api/chat/clear
- GET /api/chat/sessions
- GET /api/chat/history
- PUT /api/chat/session/title
- DELETE /api/chat/session

### Auth and account
- POST /register
- POST /login
- GET /protected
- POST /refresh
- POST /forgot-password
- POST /verify-reset-code
- POST /reset-password
- POST /update-phone
- GET /get-phone
- POST /send-email-verification
- POST /verify-email
- GET /check-email-verification

### OTP/Twilio
- POST /send-otp
- POST /verify-otp
- POST /register-with-otp
- POST /forgot-password-otp

### Profile and goals
- POST /api/profile/create
- GET /api/profile
- PUT /api/profile/update
- POST /api/profile/upload-picture
- DELETE /api/profile/delete-picture
- POST /api/profile/goals
- GET /api/profile/goals
- PUT /api/profile/goals/<goal_id>
- DELETE /api/profile/goals/<goal_id>

### Budget tracker
- POST /api/budget/monthly
- GET /api/budget/monthly
- POST /api/budget/expenses
- GET /api/budget/expenses
- PUT /api/budget/expenses/<expense_id>
- DELETE /api/budget/expenses/<expense_id>
- GET /api/budget/summary
- GET /api/budget/analysis-input

### Loan management
- POST /api/loans
- GET /api/loans/user/<user_id>
- GET /api/loans/<loan_id>
- PUT /api/loans/<loan_id>
- DELETE /api/loans/<loan_id>
- POST /api/loans/<loan_id>/payments
- GET /api/loans/<loan_id>/payments
- DELETE /api/loans/<loan_id>/payments/<payment_id>
- GET /api/loans/metrics/<user_id>

### Calculators
- POST /api/sip-calculator
- POST /api/lumpsum-calculator

### Retirement blueprint (prefix: /api/retirement)
- POST /calculate
- POST /plans
- GET /plans/<user_id>
- GET /plans/<plan_id>
- PUT /plans/<plan_id>
- DELETE /plans/<plan_id>
- POST /scenarios
- GET /scenarios/<plan_id>
- POST /readiness
- GET /recommendations/<plan_id>
- POST /export

## 11. Security and Validation Approach

1. JWT-based authentication on protected endpoints
2. Input validation in endpoint layer and schema/service utilities
3. Ownership checks for user-specific resources (loans, goals, etc.)
4. Password hashing with werkzeug security helpers
5. CORS configured for expected frontend origins
6. OTP/email verification flows for account hardening

## 12. Run and Deployment Workflow

### Local development

Option A (single script)
- Run START_SMARTFIN.bat from repo root
- This launches backend and frontend in separate terminals and opens browser

Option B (manual)
1. Backend: cd backend and run python app.py or wsgi.py
2. Frontend: cd frontend and run npm run dev

### Server mode
- Waitress WSGI is used for serving backend app
- Procfile supports platform deployment style command

## 13. Engineering Strengths (for Viva)

1. Full-stack integration
- Frontend, backend, ML, DB, and external services in one coherent system

2. Practical domain coverage
- Not just scoring; includes goals, budgets, loans, retirement, and chat

3. Explainable outputs
- Score is supported by ratios/warnings/recommendations, not opaque number only

4. Extensible architecture
- Retirement module isolated via blueprint and package structure
- Chat tools map to existing backend functionality

5. Real-world concerns addressed
- Auth, OTP, file upload, session handling, and persistent history

## 14. Known Gaps / Improvement Opportunities

1. Monolithic backend file
- backend/app.py is large; can be split into modular blueprints/services

2. Documentation drift
- Some older docs mention older stack versions/routes; code is source of truth

3. Test visibility
- Test files exist, but CI/status evidence should be consolidated in one report

4. Configuration hardening
- Ensure all secrets and production configs are environment-driven

5. Observability
- Add request-level metrics and centralized error monitoring for production

## 15. Suggested Viva Explanation Script (2-3 minutes)

You can present like this:

"SmartFin is a full-stack financial health platform. The frontend is built with React and communicates with a Flask backend using REST APIs. The backend stores user data in SQLite and loads a Gradient Boosting ML model to predict a financial health score from user financial inputs.

Beyond just prediction, we implemented practical modules: budget tracking, expense logging, loan and payment history, goals, retirement planning, SIP/lumpsum calculators, and an AI chat assistant. The chat assistant can call internal tools to fetch real user data and provide contextual recommendations.

Authentication uses JWT, and verification flows are supported with OTP and email checks. The architecture is extensible through a retirement blueprint and service-oriented modules. So this project demonstrates not only ML usage, but also complete product engineering from UI to backend logic, persistence, and user guidance." 

## 16. Common Viva Questions and Strong Answers

1. Why did you use Flask instead of Django?
- Flask gave faster API-centric development and lightweight control for custom ML/business logic integration.

2. Why SQLite for this project?
- Suitable for minor project scope, zero admin overhead, easy local setup, and enough for prototyping persistent relational workflows.

3. Which ML algorithm is used and why?
- Gradient Boosting Regressor, because it handles non-linear relationships well and gave strong performance in this domain.

4. Is this only an ML demo?
- No. ML is one module. The project includes complete user journey: auth, profile, budgets, loans, goals, retirement, and AI assistant.

5. How is security handled?
- JWT-based auth, hashed passwords, protected routes, ownership checks, validation layers, and verification flows.

6. How does what-if simulation work?
- Backend receives current and modified scenarios, predicts both scores, and returns score delta and impact.

7. How is explainability addressed?
- We return category labels, financial ratios, warnings, and recommendations alongside predicted score.

8. What would be your next version improvements?
- Modularize backend routes, improve automated testing/CI reports, migrate DB for scale, and add stronger observability.

## 17. File-Based Evidence (Source of Truth)

Use these files during review for proof:
- docs/PROJECT_VIVA_GUIDE.md (this document)
- backend/app.py
- backend/chat_agent.py
- backend/financial_health_scorer.py
- backend/guidance_engine.py
- backend/retirement_planning/api.py
- backend/requirements.txt
- frontend/src/App.jsx
- frontend/src/services/api.js
- frontend/src/components/ChatAgent.jsx
- frontend/package.json
- START_SMARTFIN.bat

## 18. Final Takeaway

SmartFin is a production-style academic project that demonstrates:
- Full-stack software architecture
- Practical ML integration
- Domain-driven financial feature engineering
- User-centric, explainable outputs
- Extensible module design for future enhancements

It is suitable for a minor project viva because it shows both conceptual understanding and real implementation depth.

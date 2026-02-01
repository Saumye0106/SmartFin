# SmartFin - Complete Project Context

> **Last Updated:** February 2, 2026  
> **Version:** 2.0.4  
> **Purpose:** Comprehensive context for migrating to another IDE or app builder

---

## 📋 Project Overview

**SmartFin** is an ML-powered financial health scoring platform that analyzes user finances and provides personalized recommendations. Users input income, expenses, savings, and debt data; the system returns a health score (0-100), spending breakdowns, risk alerts, and actionable guidance.

**Live Demo:** https://saumye0106.github.io/SmartFin/  
**Repository:** https://github.com/Saumye0106/SmartFin  
**Backend API:** https://smartfin-8hyb.onrender.com

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** React 19.2.0 (hooks-based, functional components)
- **Build Tool:** Vite 7.2.5 (Rolldown variant) - fast dev server & HMR
- **HTTP Client:** Axios 1.13.4 - API communication
- **Data Visualization:** Recharts 3.7.0 - financial charts
- **Styling:** Vanilla CSS with custom properties (no Tailwind/CSS-in-JS)
- **Typography:** JetBrains Mono (monospace data) + Syne (bold headlines) from Google Fonts
- **State Management:** React useState/useEffect (no Redux/Zustand)
- **Authentication:** JWT tokens stored in localStorage

### Backend
- **Framework:** Flask 3.x (Python)
- **Extensions:**
  - Flask-CORS - Cross-origin requests
  - Flask-JWT-Extended - JWT authentication
  - Werkzeug - Password hashing
- **Database:** SQLite (auth.db) - user accounts
- **ML Model:** scikit-learn Gradient Boosting Regressor (92% R² score)
- **Model Files:** Pickled .pkl files (model, feature names, metadata)

### Machine Learning
- **Algorithm:** Gradient Boosting Regressor
- **Training Data:** 1,500 synthetic financial profiles
- **Features:** 11 financial metrics (income, expenses, savings, debt ratios)
- **Target:** Financial health score (0-100)
- **Performance:** 92% R² on test set

### Deployment
- **Frontend:** GitHub Pages (static hosting)
- **Backend:** Render (free tier, auto-deploy from main branch)
- **Build:** Vite production build → `dist/` folder

---

## 🏗️ Architecture & Data Flow

```
┌─────────────┐
│   Browser   │
│  (React UI) │
└──────┬──────┘
       │ Axios HTTP
       ▼
┌─────────────────────────────────────┐
│     Flask Backend (Port 5000)       │
│  ┌──────────────────────────────┐   │
│  │  Auth Endpoints              │   │
│  │  /register, /login           │   │
│  │  JWT token generation        │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  ML Prediction Endpoints     │   │
│  │  /api/predict, /api/whatif   │   │
│  │  Loads .pkl model            │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  SQLite Database             │   │
│  │  users table (auth.db)       │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Request Flow Example:**
1. User enters financial data in React form
2. Frontend sends POST to `/api/predict` with JWT token
3. Backend validates token, extracts features
4. ML model predicts health score
5. Business logic generates alerts, guidance, recommendations
6. JSON response sent back to frontend
7. React components render visualizations

---

## 🚀 Running Locally

### Prerequisites
- **Node.js:** 18+ (for frontend)
- **Python:** 3.11+ (for backend)
- **pip:** Package installer

### Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server (default port 5000)
python app.py
```

**Backend will start at:** `http://localhost:5000`

### Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env file for local API
cat > .env << EOL
VITE_API_BASE_URL=http://localhost:5000
VITE_AUTH_BASE_URL=http://localhost:5000
EOL

# Run dev server (default port 5173)
npm run dev
```

**Frontend will start at:** `http://localhost:5173`

### Quick Test
1. Open browser to `http://localhost:5173`
2. Register a new account (email + password 6+ chars)
3. Fill in sample financial data or click "Load Sample Data"
4. Click "Analyze My Finances"
5. View score, charts, alerts, and recommendations

---

## 🔐 Environment Variables

### Frontend (.env)
```env
# Local development
VITE_API_BASE_URL=http://localhost:5000
VITE_AUTH_BASE_URL=http://localhost:5000

# Production (fallback in code)
# VITE_API_BASE_URL=https://smartfin-8hyb.onrender.com
# VITE_AUTH_BASE_URL=https://smartfin-8hyb.onrender.com
```

**Note:** `.env` is in `.gitignore` - never committed. Production uses fallback URLs in `frontend/src/services/api.js`.

### Backend (Environment Variables)
```env
# Optional (has defaults)
JWT_SECRET_KEY=smartfin-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour in seconds
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days
```

---

## 📡 API Endpoints

### Authentication

**POST /register**
- **Body:** `{ "email": "user@example.com", "password": "password123" }`
- **Response:** `{ "token": "jwt...", "refresh_token": "jwt...", "user": { "id": 1, "username": "user@example.com" } }`
- **Status:** 201 Created, 400 Bad Request, 409 Conflict

**POST /login**
- **Body:** `{ "email": "user@example.com", "password": "password123" }`
- **Response:** `{ "token": "jwt...", "refresh_token": "jwt...", "user": { "id": 1, "username": "user@example.com" } }`
- **Status:** 200 OK, 401 Unauthorized

**POST /refresh**
- **Headers:** `Authorization: Bearer <refresh_token>`
- **Response:** `{ "token": "new_access_token..." }`
- **Status:** 200 OK

### ML Predictions

**POST /api/predict**
- **Body:**
  ```json
  {
    "income": 100000,
    "rent": 30000,
    "food": 12000,
    "travel": 8000,
    "shopping": 15000,
    "emi": 20000,
    "savings": 15000,
    "investments": 10000,
    "credit_score": 750,
    "age": 30,
    "dependents": 2
  }
  ```
- **Response:**
  ```json
  {
    "score": 72,
    "classification": { "category": "Very Good", "color": "#3b82f6", "emoji": "✨", "description": "..." },
    "patterns": { "expense_ratio": 0.85, "savings_rate": 0.15, ... },
    "alerts": [ { "severity": "medium", "type": "high_emi", "message": "..." } ],
    "guidance": { "strengths": [...], "recommendations": [...] },
    "investment_advice": { "risk_profile": "moderate", "suggestions": [...] }
  }
  ```

**POST /api/whatif**
- **Body:** `{ "current": {...}, "modified": {...} }`
- **Response:** `{ "current_score": 72, "modified_score": 78, "difference": 6, ... }`

**GET /api/model-info**
- **Response:** `{ "model_type": "Gradient Boosting", "test_r2": 0.9197, ... }`

---

## 📁 File Structure

```
smartfin/
├── .github/
│   └── skills/
│       └── frontend-design/        # Design system guidelines
│           ├── SKILL.md
│           └── example-brutalist-landing.html
├── backend/
│   ├── app.py                      # Main Flask server (auth + ML + API)
│   ├── requirements.txt            # Python dependencies
│   ├── runtime.txt                 # Python version for Render
│   ├── auth.db                     # SQLite database (created on first run)
│   └── Procfile                    # Render deployment config
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main React component (terminal UI)
│   │   ├── App.css                 # Terminal aesthetic styles
│   │   ├── main.jsx                # React entry point
│   │   ├── index.css               # Global styles
│   │   ├── components/
│   │   │   ├── AuthForm.jsx        # Login/register form
│   │   │   ├── FinancialForm.jsx   # Data input form
│   │   │   ├── ScoreDisplay.jsx    # Health score visualization
│   │   │   ├── SpendingChart.jsx   # Expense breakdown chart
│   │   │   ├── RatiosDashboard.jsx # Financial ratios
│   │   │   ├── AlertsPanel.jsx     # Risk alerts
│   │   │   ├── GuidancePanel.jsx   # Recommendations
│   │   │   ├── InvestmentAdvice.jsx
│   │   │   └── WhatIfSimulator.jsx # Scenario simulator
│   │   └── services/
│   │       └── api.js              # Axios API client
│   ├── package.json
│   ├── vite.config.js
│   ├── eslint.config.js
│   ├── .env                        # Local env vars (gitignored)
│   └── .gitignore
├── ml/
│   ├── train_model.py              # Model training script
│   ├── financial_health_model.pkl  # Trained model
│   ├── feature_names.pkl
│   ├── model_metadata.pkl
│   └── README.md
├── data/
│   ├── dataset_generator.py        # Synthetic data generation
│   ├── smartfin_dataset.csv        # 1500 training samples
│   └── analyze_dataset.py
├── docs/
│   ├── README.md                   # Documentation index
│   ├── QUICKSTART.md               # 2-minute setup guide
│   ├── DEPLOYMENT.md               # Deployment instructions
│   ├── model_explanation.md        # ML model details
│   └── 2026-02-02-session-summary.md  # Recent development log
├── services/
│   └── auth/                       # Standalone auth microservice (optional)
│       └── app.py
├── README.md                       # Main project README
└── requirements.txt                # Root Python deps
```

---

## 🎨 Design System

### Visual Identity: "Financial Terminal Refined"

**Aesthetic Philosophy:**
Bloomberg Terminal meets editorial design - raw financial data presented with typographic excellence and confident visual hierarchy. Dark mode with neon accents, monospace data displays, and elegant sans-serif headlines.

### Color Palette
```css
--bg-primary: #0f1419;      /* Deep charcoal background */
--bg-secondary: #1a1f26;    /* Secondary panels */
--text-primary: #e6edf3;    /* Main text */
--text-secondary: #8b949e;  /* Muted text */
--accent-cyan: #00d9ff;     /* Primary actions, links */
--accent-amber: #ffb800;    /* Warnings, alerts */
--accent-red: #ff3366;      /* Errors, critical */
--accent-green: #00ff88;    /* Success, positive metrics */
--border-color: #30363d;    /* Dividers, borders */
```

### Typography
- **Headlines:** Syne (800 weight, tight letter-spacing)
- **Data/Numbers:** JetBrains Mono (700/800 weight, monospace)
- **Body Text:** JetBrains Mono (400 weight)

### Visual Effects
- **Scanlines:** Horizontal CRT-style lines (low opacity)
- **Grid Overlay:** Subtle background grid pattern
- **Glows:** Box-shadow glows on accent colors (cyan, amber, green)
- **Animations:** Cubic-bezier easing (0.16, 1, 0.3, 1) for smooth transitions
- **Status Indicators:** Pulsing LED dots with animation

### Component Patterns
- **Brackets:** `[SMARTFIN]` for branding
- **Uppercase Labels:** System-style labels (OPERATOR, STATUS, VERSION)
- **Border Accents:** Thick left borders (3-5px) for panels
- **Loading States:** Animated bars instead of spinners
- **Hover States:** 60-120ms color shifts + transform

---

## 🔑 Key Design Decisions

### Why Vanilla CSS (Not Tailwind)?
- **Bespoke Aesthetic:** Terminal-style scanlines, grid overlays, and custom glows require precise CSS
- **Design Skill:** `.github/skills/frontend-design` guides a distinctive visual language
- **Simplicity:** Small project benefits from explicit, auditable styles
- **No Generic Look:** Avoid utility-class aesthetics

### Why React (Not Vue/Svelte)?
- **Ecosystem:** Mature libraries (Recharts, React Router)
- **Team Knowledge:** Most common framework
- **Job Market:** Industry standard

### Why Flask (Not FastAPI/Django)?
- **Simplicity:** Lightweight, easy to understand
- **ML Integration:** Seamless joblib/scikit-learn loading
- **Microservices:** Flask-JWT-Extended for auth

### Why SQLite (Not PostgreSQL)?
- **Prototype Speed:** Zero setup, file-based
- **Render Free Tier:** Ephemeral filesystem acceptable for demo
- **Migration Path:** Easy to swap for Postgres later

### Authentication Strategy
- **Auto-login on Register:** UX improvement - users get JWT immediately
- **Access + Refresh Tokens:** Standard JWT pattern
- **localStorage:** Simple client-side token storage
- **Backend Handles Both:** Auth + API in single service (not microservices yet)

---

## 📝 Recent Changes (Feb 2, 2026)

### Frontend Redesign
- ✅ Implemented "Financial Terminal Refined" aesthetic
- ✅ Redesigned `App.jsx` with terminal-style header, live clock, system status
- ✅ Complete `App.css` rewrite (scanlines, grid, animations)
- ✅ Redesigned `ScoreDisplay` component with terminal visuals
- ✅ Added `.env` support for local development
- ✅ Improved responsive design for mobile

### Authentication Fixes
- ✅ Fixed register endpoint to auto-login with JWT tokens
- ✅ Made frontend handle both `username` and `email` fields (backward compatible)
- ✅ Added better error handling (backend messages surface in UI)
- ✅ Created `.env` configuration for local vs production

### Documentation
- ✅ Created frontend-design skill (`.github/skills/`)
- ✅ Added session summary (`docs/2026-02-02-session-summary.md`)
- ✅ Updated `.gitignore` to exclude `.env` files

### Deployment
- ✅ All changes pushed to GitHub
- ✅ Render auto-deploys backend from main branch
- ✅ GitHub Pages serves frontend static files

---

## 🐛 Known Issues & TODOs

### High Priority
- [ ] Migrate remaining components to terminal aesthetic (FinancialForm, AlertsPanel, etc.)
- [ ] Add comprehensive tests (Vitest for frontend, pytest for backend)
- [ ] Implement refresh token rotation for security
- [ ] Add loading states for all async operations

### Medium Priority
- [ ] Consider TypeScript migration for type safety
- [ ] Add accessibility audit (ARIA labels, keyboard navigation)
- [ ] Implement "remember me" checkbox for persistent login
- [ ] Add user profile page (view/edit account)
- [ ] Implement password reset flow

### Low Priority / Nice-to-Have
- [ ] Consider Tailwind CSS for layout utilities (hybrid approach)
- [ ] Add dark/light mode toggle (currently dark-only)
- [ ] Implement data export (CSV/PDF reports)
- [ ] Add historical tracking (save multiple predictions over time)
- [ ] Implement real-time WebSocket updates for live score changes
- [ ] Add social login (Google, GitHub OAuth)

### Technical Debt
- [ ] Move auth to separate microservice (services/auth/)
- [ ] Migrate SQLite → PostgreSQL for production
- [ ] Add rate limiting to API endpoints
- [ ] Implement proper logging (Winston/Sentry)
- [ ] Add API versioning (/api/v1/)
- [ ] Create OpenAPI/Swagger docs

---

## 🧪 Testing Strategy (Future)

### Frontend Testing
```bash
# Install Vitest + React Testing Library
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Run tests
npm test
```

**Test Coverage Targets:**
- Unit tests for utility functions (api.js)
- Component tests for all React components
- Integration tests for full user flows (register → predict → visualize)
- E2E tests with Playwright for critical paths

### Backend Testing
```bash
# Install pytest
pip install pytest pytest-flask pytest-cov

# Run tests
pytest --cov=backend
```

**Test Coverage Targets:**
- Unit tests for ML prediction logic
- API endpoint tests (all routes)
- Auth flow tests (register, login, token validation)
- Database tests (user CRUD)

---

## 🔒 Security Considerations

### Current Implementation
- ✅ Password hashing with Werkzeug (bcrypt-based)
- ✅ JWT tokens with expiration (1 hour access, 30 day refresh)
- ✅ CORS configured for specific origins
- ✅ SQL injection protection (parameterized queries)

### Production Hardening Needed
- [ ] Move JWT_SECRET_KEY to environment variable (not hardcoded)
- [ ] Implement rate limiting (Flask-Limiter)
- [ ] Add HTTPS-only cookie storage for tokens (httpOnly, secure flags)
- [ ] Implement CSRF protection for state-changing operations
- [ ] Add input validation/sanitization (Marshmallow/Pydantic)
- [ ] Enable Content Security Policy headers
- [ ] Add request logging and monitoring
- [ ] Implement token blacklisting on logout

---

## 📦 Dependencies

### Frontend (package.json)
```json
{
  "dependencies": {
    "axios": "^1.13.4",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "recharts": "^3.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^5.1.1",
    "eslint": "^9.39.1",
    "vite": "npm:rolldown-vite@7.2.5"
  }
}
```

### Backend (requirements.txt)
```txt
Flask==3.1.0
Flask-CORS==5.0.0
Flask-JWT-Extended==4.7.1
scikit-learn==1.6.1
joblib==1.4.2
numpy==2.2.3
pandas==2.2.3
Werkzeug==3.1.3
```

---

## 🚢 Deployment Guide

### Frontend (GitHub Pages)
1. Build production bundle: `npm run build`
2. Output goes to `frontend/dist/`
3. GitHub Actions deploys on push to main
4. Served at: https://saumye0106.github.io/SmartFin/

### Backend (Render)
1. Connected to GitHub repo (auto-deploy on push)
2. Build command: `pip install -r backend/requirements.txt`
3. Start command: `python backend/app.py`
4. Environment variables set in Render dashboard
5. Free tier: https://smartfin-8hyb.onrender.com

### Database Persistence
⚠️ **Note:** Render free tier has ephemeral filesystem. SQLite database resets on deploy. For production, migrate to:
- Render PostgreSQL (paid)
- Supabase (free PostgreSQL)
- PlanetScale (MySQL)

---

## 🔄 Migration Checklist

When moving to another IDE/builder:

### 1. Environment Setup
- [ ] Clone repository: `git clone https://github.com/Saumye0106/SmartFin.git`
- [ ] Install Node.js 18+ and Python 3.11+
- [ ] Create frontend `.env` file with local API URLs
- [ ] Install dependencies (`npm install`, `pip install -r requirements.txt`)

### 2. IDE Configuration
- [ ] Import project into new IDE
- [ ] Configure Python interpreter (point to venv)
- [ ] Configure ESLint/Prettier for frontend
- [ ] Set up run configurations (frontend dev, backend server)

### 3. Read Documentation
- [ ] Review `README.md` (main overview)
- [ ] Read `QUICKSTART.md` (how to run)
- [ ] Check `docs/2026-02-02-session-summary.md` (recent changes)
- [ ] Review `.github/skills/frontend-design/SKILL.md` (design guidelines)

### 4. Verify Functionality
- [ ] Start backend: `python backend/app.py`
- [ ] Start frontend: `npm run dev`
- [ ] Register new user
- [ ] Test prediction flow
- [ ] Check all components render correctly

### 5. Development Setup
- [ ] Install recommended VS Code extensions (if applicable)
- [ ] Configure debugger for Flask + React
- [ ] Set up Git hooks (pre-commit, pre-push)
- [ ] Review and update dependencies

---

## 💡 Tips for New Developers

### Code Navigation
- Start with `frontend/src/App.jsx` - main entry point
- Follow data flow: Form → `api.js` → Backend → Response → Components
- Check `backend/app.py` for all API routes (search for `@app.route`)

### Making Changes
- Frontend: Edit components, see live reload (HMR)
- Backend: Restart server after code changes
- CSS: Use existing CSS variables in `App.css` for consistency
- New features: Follow terminal aesthetic guidelines in `.github/skills/`

### Common Tasks
- Add new API endpoint: Define route in `backend/app.py`, add method in `frontend/src/services/api.js`
- Style new component: Use CSS custom properties, reference existing components
- Add new page: Create component, import in `App.jsx`, add routing logic
- Modify ML model: Retrain in `ml/train_model.py`, replace `.pkl` files

### Debugging
- Frontend errors: Check browser console (F12)
- Backend errors: Check terminal output (Flask logs)
- Network issues: Check browser Network tab (API requests/responses)
- Auth issues: Check localStorage for token (Application tab)

---

## 📞 Support & Resources

- **Repository Issues:** https://github.com/Saumye0106/SmartFin/issues
- **Documentation:** `docs/` folder
- **Session Logs:** `docs/*-session-summary.md`
- **Design Guidelines:** `.github/skills/frontend-design/SKILL.md`

---

## 📄 License

[Add license information here]

---

**Generated:** February 2, 2026  
**For:** Migration to new IDE/app builder  
**Contact:** [Add contact information]

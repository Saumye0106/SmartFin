
# 💰 SmartFin - ML-Based Financial Health Platform

An intelligent financial health assessment and learning platform for students, powered by machine learning.
![Status](https://img.shields.io/badge/status-complete-success)
![ML Accuracy](https://img.shields.io/badge/ML%20Accuracy-96%25-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![Flask](https://img.shields.io/badge/Flask-2.3.0-lightgrey)
![React](https://img.shields.io/badge/React-18.2-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.0-lightgrey)

---

## 🎯 Project Overview

SmartFin is a student-centric financial health platform that uses machine learning to predict financial health scores, classify financial status, analyze spending patterns, and provide personalized guidance and investment advice.

### Target Audience
- College students
- Young/non-earning population
- People with no finance background

---
## 🧠 Core Features (Academic)

1. **ML-Based Financial Health Score Prediction** ✅
   - Gradient Boosting Regressor
   - 95.85% R² accuracy (±5 points MAE)
   - Predicts score 0-100
   - Enhanced 8-factor model

2. **5-Category Classification** ✅
   - Poor (0-34)
   - Average (35-49)
   - Good (50-64)
   - Very Good (65-79)
   - Excellent (80-100)

3. **Loan History Management** ✅ NEW
   - Track multiple loans (Personal, Home, Auto, Education)
   - Record and monitor payments
   - Calculate loan metrics (Diversity, Payment History, Maturity)
   - Integrated into financial health scoring

4. **Spending Pattern Analysis** ✅
   - Expense ratio calculation
   - Savings ratio analysis
   - EMI burden assessment
   - Category-wise breakdown

5. **Personalized Guidance Engine** ✅
   - Identifies financial strengths
   - Issues risk warnings
   - Provides actionable recommendations

6. **What-If Simulation** ✅
   - Test financial scenarios
   - See score impact
   - Decision support

7. **Anomaly/Risk Detection** ✅
   - Critical alerts (deficit, debt trap)
   - High-risk warnings (zero savings)
   - Medium-risk flags
   - Low-risk notices

8. **Rule-Based Investment Advisor** ✅
   - Investment eligibility check
   - Risk-appropriate suggestions
   - Recommended allocationstions
   - Recommended allocations

---

## 🏗️ System Architecture

```
┌─────────────┐
│   Frontend  │  HTML/CSS/JS + Chart.js
│  (Dashboard)│
└──────┬──────┘
       │ REST API
       ↓
┌─────────────┐
│   Backend   │  Flask (Python)
│   (API)     │
└──────┬──────┘
       │
       ├→ ML Model (Gradient Boosting)
       ├→ Business Logic (Guidance, Investment)
       └→ Analysis Engine
```

---

## 📊 Tech Stack

### Backend
- **Language:** Python 3.11
- **Framework:** Flask 2.3.0
- **ML Library:** scikit-learn 1.3.0
### ML Model
- **Algorithm:** Gradient Boosting Regressor
- **Features:** 8 (income, rent, food, travel, shopping, emi, savings, loan metrics)
- **Target:** Financial health score (0-100)
- **Performance:** R² = 0.9585, MAE = 4.12
- **JavaScript (ES6+)** - Vanilla JS
- **Chart.js 4.4.0** - Visualizations

### ML Model
- **Algorithm:** Gradient Boosting Regressor
- **Features:** 7 (income, rent, food, travel, shopping, emi, savings)
- **Target:** Financial health score (0-100)
- **Performance:** R² = 0.9197, MAE = 5.37

---

## 📁 Project Structure

```
smartfin/
│
├── data/
│   ├── dataset_generator.py       # Synthetic dataset generation
│   ├── smartfin_dataset.csv       # 1500 training samples
│   └── analyze_dataset.py         # Data analysis script
│
├── ml/
│   ├── train_model.py             # Model training script
│   ├── financial_health_model.pkl # Trained model
│   ├── feature_names.pkl          # Feature list
│   ├── model_metadata.pkl         # Performance metrics
│   └── model_performance.png      # Visualizations
│
├── backend/
│   ├── app.py                     # Flask REST API (650+ lines)
│   ├── requirements.txt           # Python dependencies
│   ├── test_api.py                # API test suite
│   └── test_model_locally.py     # Local model tests
│
├── frontend/
│   ├── index.html                 # Main dashboard (300+ lines)
│   ├── css/
│   │   └── styles.css            # Complete styling (800+ lines)
│   ├── js/
│   │   ├── api.js                # API service layer
│   │   ├── charts.js             # Chart.js integration
│   │   └── app.js                # Main app logic (300+ lines)
│   └── README.md                 # Frontend docs
│
├── docs/
│   └── model_explanation.md      # ML model documentation
│
├── QUICKSTART.md                  # Quick start guide
├── PHASE_1_COMPLETE.md           # ML phase summary
├── PHASE_2_COMPLETE.md           # Backend phase summary
├── PHASE_3_COMPLETE.md           # Frontend phase summary
└── README.md                      # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip (Python package manager)
- Modern web browser

### Installation

1. **Clone/Download the project**

2. **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Verify ML Model Exists**
```bash
# Model should already be trained
# If not, run:
cd ../ml
python train_model.py
```

### Run the Application

**Terminal 1 - Start Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Open Frontend:**
```bash
cd frontend
python -m http.server 8000
```

**Visit:** `http://localhost:8000`

---

## 📖 Usage Guide

### 1. Enter Financial Data
Fill in your monthly financial information:
- Income
- Rent/Housing
- Food & Groceries
- Travel & Transport
- Shopping & Entertainment
- EMI & Loans
- Savings

Or click **"Load Sample Data"** for a quick demo.

### 2. Analyze
Click **"Analyze My Finances"** to:
- Get your financial health score
- View category classification
- See spending breakdown
- Get personalized guidance
- Receive investment advice

### 3. What-If Simulation
- Adjust shopping and savings amounts
- Click **"Run Simulation"**
- See how changes affect your score

---

### Model Performance
| Metric | Value |
|--------|-------|
| Algorithm | Gradient Boosting |
| R² Score | 0.9585 (96%) |
| MAE | 4.12 points |
| RMSE | 5.23 points |
| Training Samples | 42,000 |
| Test Samples | 10,424 |
| Features | 8 (5 original + 3 loan metrics) |
### Feature Importance
1. **Savings** - 45.18% (most important)
2. **EMI** - 28.53%
3. **Payment History Score** - 12.40% (NEW)
4. **Loan Diversity Score** - 6.90% (NEW)
5. **Loan Maturity Score** - 3.20% (NEW)
6. **Rent** - 1.90%
7. **Income** - 1.41%
8. **Shopping** - 0.48%|

### Feature Importance
1. **Savings** - 53.18% (most important)
2. **EMI** - 35.53%
3. **Rent** - 3.90%
4. **Income** - 3.66%
5. **Shopping** - 1.41%
6. **Food** - 1.32%
7. **Travel** - 1.00%

### Why These Features?
The model learned that **savings ratio** and **EMI burden** are the strongest predictors of financial health, validating domain knowledge that financial health depends on ratios, not absolute amounts.

---

## 🔌 API Documentation

### Base URL
```
http://localhost:5000
```

### Endpoints

#### 1. Health Check
```http
GET /
```

**Response:**
```json
{
  "status": "online",
  "service": "SmartFin Financial Health API",
  "model": "Gradient Boosting",
  "model_accuracy": "91.97%"
}
```

#### 2. Predict Score
```http
POST /api/predict
Content-Type: application/json

{
  "income": 50000,
  "rent": 15000,
  "food": 8000,
  "travel": 3000,
  "shopping": 5000,
  "emi": 10000,
  "savings": 9000
}
```

**Response:**
```json
{
  "success": true,
  "score": 58.43,
  "classification": {
    "category": "Good",
    "color": "#f59e0b",
    "emoji": "👍",
    "description": "..."
  },
  "patterns": {
    "expense_ratio": 0.82,
    "savings_ratio": 0.18,
    "emi_ratio": 0.20,
    "breakdown": {...}
  },
  "guidance": {
    "strengths": [...],
    "warnings": [...],
    "recommendations": [...]
  },
  "anomalies": [...],
  "investments": {...}
}
```

#### 3. What-If Simulation
```http
POST /api/whatif
Content-Type: application/json

{
  "current": {...},
  "modified": {...}
}
```

**Response:**
```json
{
  "success": true,
  "current_score": 58.43,
  "modified_score": 68.91,
  "score_change": 10.48,
  "impact": "positive",
  "current_classification": {...},
  "modified_classification": {...}
}
```

#### 4. Model Info
```http
GET /api/model-info
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
python test_model_locally.py    # Test without server
python test_api.py               # Test with server running
```

### Test Cases

**Excellent Profile:**
- Income: 100,000 → Score: 94+

**Poor Profile:**
- Income: 30,000, Expenses: 33,000 → Score: <35

**Student Profile:**
- Income: 25,000, Savings: 7,000 → Score: 75-80

---

## 📊 Dashboard Features

### Visualizations
1. **Circular Score Gauge** - Animated SVG progress
2. **Doughnut Chart** - Spending breakdown
3. **Progress Bars** - Financial ratios
4. **Alert Cards** - Risk warnings
5. **Guidance Panels** - Personalized advice

### Interactions
- Form validation
- Loading states
- Smooth animations
- Responsive design
- Error handling

---

## 🎨 Design System

### Colors
- Primary: `#3b82f6` (Blue)
- Success: `#10b981` (Green)
- Warning: `#f59e0b` (Amber)
- Danger: `#ef4444` (Red)
- Secondary: `#8b5cf6` (Purple)

### Typography
- Font: Inter, -apple-system, sans-serif
- Headings: 600-700 weight
- Body: 400 weight

### Spacing
- Base unit: 0.25rem (4px)
- Card padding: 2rem
- Gap: 1.5rem

---

## 🔒 Security Considerations

- **No sensitive data storage** - Everything is session-based
- **No authentication** - Educational project scope
- **CORS enabled** - For local development
- **Input validation** - Frontend and backend
- **No external APIs** - Fully self-contained

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Page Load | <1s |
| API Response | <500ms |
| Chart Render | <200ms |
| What-If Simulation | <300ms |

---

## 🌐 Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers

---

## 📱 Responsive Design

- **Desktop:** 1200px+ (full layout)
- **Tablet:** 768-1199px (2-column)
- **Mobile:** <768px (single column)

---

## 🎬 Demo Instructions

### For Viva/Presentation

**Step 1:** Show Architecture
- Explain ML → Backend → Frontend flow

**Step 2:** Dataset
- Show `data/smartfin_dataset.csv`
- Explain 1500 samples with 7 features

**Step 3:** ML Model
- Show `ml/model_performance.png`
- Highlight 92% R² accuracy
- Explain Gradient Boosting choice

**Step 4:** Backend
- Start Flask server
- Show API endpoints working
- Explain business logic

**Step 5:** Frontend
- Load sample data
- Analyze finances
- Show all features:
  - Score prediction
  - Charts
  - Guidance
  - Anomaly detection
  - Investment advice
  - What-if simulator

---

## 🎯 Academic Positioning

### Project Type
Minor Project - ML-based Financial Health Platform

### Core Contribution
ML-based financial health scoring and decision support system for students with integrated learning modules.

### Scope
- ✅ ML score prediction
- ✅ Pattern analysis
- ✅ Personalized guidance
- ✅ Investment recommendations
- ❌ No stock prediction
- ❌ No real transactions
- ❌ No bank integration

---

## 📚 Documentation

- `README.md` - This file (project overview)
- `QUICKSTART.md` - 2-minute setup guide
- `frontend/README.md` - Frontend documentation
- `docs/model_explanation.md` - ML model details
- `PHASE_*.md` - Development phase summaries

---

## 🚧 Future Enhancements (Out of Scope)

- [ ] User authentication & profiles
- [ ] Historical tracking
- [ ] News feed integration
- [ ] Interactive chatbot
- [ ] Finance learning game
- [ ] Mobile app (PWA)
- [ ] Multi-language support
- [ ] PDF report export

---

## 👨‍💻 Development Stats

- **Total Time:** ~5 hours
- **Lines of Code:** ~2,330
- **Files:** 25+
- **Commits:** N/A (single development)

**Breakdown:**
- ML Training: 280 lines
- Backend: 650 lines
- Frontend: 1,400 lines

---

## 📝 License

Educational Project - Free to use for academic purposes

---

## 🆘 Troubleshooting

### Issue: Module not found
```bash
cd backend
pip install -r requirements.txt
```

### Issue: Model file missing
```bash
cd ml
python train_model.py
```

### Issue: Frontend can't connect
1. Check backend is running on port 5000
2. Visit `http://localhost:5000` - should show API status
3. Check browser console for CORS errors

### Issue: Charts not showing
- Check internet connection (Chart.js loads from CDN)
- Open browser developer tools (F12)

---

## 📞 Support

For issues or questions:
1. Check `QUICKSTART.md`
2. Read phase completion docs
3. Review API documentation
4. Check browser console for errors

---

## ✅ Project Status

**Phase 1:** ✅ ML Model (Complete)
**Phase 2:** ✅ Backend API (Complete)
**Phase 3:** ✅ Frontend (Complete)

**All 7 core academic features implemented!**

---

## 🎉 Acknowledgments

- Built for academic minor project
- ML powered by scikit-learn
- Visualizations by Chart.js
- Modern web standards (HTML5/CSS3/ES6)

---

**Version:** 1.0.0
**Last Updated:** January 2025
**Status:** ✅ Production Ready

---

## 🚀 Ready to Demo!

Start the backend, open the frontend, and showcase your ML-powered financial health platform!

```bash
cd backend && python app.py
# Open frontend/index.html in browser
```

**Good luck with your project! 🎓**

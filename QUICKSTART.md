# SmartFin - Quick Start Guide

## 🚀 Run Your Project in 2 Minutes

### Step 1: Start Backend (Terminal 1)

```bash
cd backend
python app.py
```

You should see:
```
Loading ML model...
Model loaded: Gradient Boosting
Model R2 Score: 0.9197
SmartFin Backend Server Starting...
* Running on http://0.0.0.0:5000
```

### Step 2: Open Frontend

**Option A - Direct Open:**
```bash
# Just double-click or open in browser:
frontend/index.html
```

**Option B - Local Server (Better):**
```bash
cd frontend
python -m http.server 8000
```
Then visit: `http://localhost:8000`

### Step 3: Test It!

1. Click **"Load Sample Data"**
2. Click **"Analyze My Finances"**
3. See your score, charts, and recommendations!
4. Try the **What-If Simulator**

---

## 📊 Project Structure

```
smartfin/
├── data/
│   ├── dataset_generator.py    # Generate dataset
│   └── smartfin_dataset.csv    # 1500 samples
├── ml/
│   ├── train_model.py          # Train ML model
│   ├── financial_health_model.pkl
│   └── model_performance.png
├── backend/
│   ├── app.py                  # Flask API
│   └── requirements.txt
└── frontend/
    ├── index.html              # Dashboard
    ├── css/styles.css
    └── js/{api,charts,app}.js
```

---

## 🎯 What Each Part Does

### 1. Dataset (data/)
- **Purpose:** Training data for ML model
- **Run:** `python dataset_generator.py`
- **Output:** 1500 financial profiles with scores

### 2. ML Model (ml/)
- **Purpose:** Train prediction model
- **Run:** `python train_model.py`
- **Output:** 92% accurate Gradient Boosting model

### 3. Backend (backend/)
- **Purpose:** REST API for predictions
- **Port:** 5000
- **Endpoints:**
  - `POST /api/predict` - Get score & analysis
  - `POST /api/whatif` - Run simulation
  - `GET /api/model-info` - Model details

### 4. Frontend (frontend/)
- **Purpose:** Interactive dashboard
- **Tech:** HTML/CSS/JS + Chart.js
- **Features:** Score display, charts, guidance, what-if

---

## 🧪 Test Cases

### Test 1: Excellent Profile
```json
Income: 100000
Expenses: 50000
Savings: 40000
EMI: 10000
Expected Score: 90+
```

### Test 2: Poor Profile
```json
Income: 30000
Expenses: 33000 (deficit!)
Savings: 0
EMI: 8000
Expected Score: <35
```

### Test 3: Student Profile
```json
Income: 25000
Expenses: 16000
Savings: 7000
EMI: 0
Expected Score: 75-80
```

---

## 🔧 Troubleshooting

### Issue: Backend won't start

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Fix:**
```bash
cd backend
pip install -r requirements.txt
```

---

### Issue: Frontend shows "Error connecting to backend"

**Fix:**
1. Check backend is running: `http://localhost:5000`
2. Visit in browser - should show API status
3. If not, restart: `python app.py`

---

### Issue: Charts not showing

**Fix:**
- Check internet connection (Chart.js loads from CDN)
- Open browser console (F12) for errors

---

## 📝 For Your Viva

### Quick Facts:

- **ML Model:** Gradient Boosting Regressor
- **Accuracy:** 92% R² score (±5 points MAE)
- **Dataset:** 1500 synthetic samples
- **Features:** 7 financial inputs
- **Output:** Score (0-100) + 5 categories + guidance
- **Tech Stack:** Python, Flask, scikit-learn, HTML/CSS/JS
- **Development Time:** ~5 hours
- **Lines of Code:** ~2300

### Demo Flow:

1. Show dataset (`data/smartfin_dataset.csv`)
2. Explain ML training (`ml/model_performance.png`)
3. Start backend, show API working
4. Open frontend, enter data
5. Show score prediction
6. Explain guidance engine
7. Demo what-if simulator
8. Highlight investment advisor

---

## 📚 File Checklist

Before demo, ensure these exist:

- [x] `data/smartfin_dataset.csv`
- [x] `ml/financial_health_model.pkl`
- [x] `ml/model_performance.png`
- [x] `backend/app.py`
- [x] `frontend/index.html`
- [x] All JS/CSS files

---

## 🎬 Demo Script (5 minutes)

**Minute 1:** Introduction
- "SmartFin is an ML-based financial health platform for students"
- "It predicts a health score and provides personalized guidance"

**Minute 2:** Show ML Model
- Open `ml/model_performance.png`
- "92% R² accuracy on 1500 samples"
- "Gradient Boosting learns from rule-based scoring"

**Minute 3:** Backend Demo
- `python app.py` - show server start
- "Flask REST API with 3 endpoints"
- "Processes prediction, analysis, what-if"

**Minute 4:** Frontend Demo
- Load sample data
- Click Analyze
- Show: score, charts, guidance, alerts, investments

**Minute 5:** What-If Simulator
- "Change shopping from 5000 to 2000"
- "Change savings from 9000 to 12000"
- "Score improves by +10 points!"

---

## ✅ Final Checklist

Before submission/demo:

- [ ] Dataset generated (1500 rows)
- [ ] Model trained (92%+ R²)
- [ ] Backend runs without errors
- [ ] Frontend opens in browser
- [ ] Can complete full user flow
- [ ] What-if simulator works
- [ ] Charts render correctly
- [ ] All 7 core features working

---

## 🆘 Emergency Commands

If something breaks:

```bash
# Regenerate dataset
cd data
python dataset_generator.py

# Retrain model
cd ../ml
python train_model.py

# Reinstall backend dependencies
cd ../backend
pip install -r requirements.txt

# Restart everything
python app.py
```

---

## 🎉 You're Ready!

Your project is complete with:
- ✅ ML model (92% accurate)
- ✅ REST API backend
- ✅ Interactive frontend
- ✅ All 7 core features
- ✅ Documentation

**Good luck with your demo!** 🚀

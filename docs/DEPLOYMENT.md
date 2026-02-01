# SmartFin Deployment Guide

## 🚀 Deploy to GitHub Pages (Frontend Only)

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `smartfin`
3. Description: "ML-Based Financial Health Platform"
4. Public repository
5. **Don't** initialize with README (we have one)
6. Click "Create repository"

### Step 2: Push to GitHub

```bash
cd c:\Users\saumy\smartfin

# Add all files
git add .

# Commit
git commit -m "Initial commit - SmartFin ML Platform"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/smartfin.git

# Push
git branch -M main
git push -u origin main
```

### Step 3: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click "Settings"
3. Click "Pages" (left sidebar)
4. Under "Source": Select "main" branch
5. Select folder: `/` (root) or `/frontend`
6. Click "Save"

**If using root (`/`):**
- Move `frontend/index.html` to root
- Move `frontend/css` and `frontend/js` to root

**If using `/frontend`:**
- Keep structure as is
- Your site will be at: `https://YOUR_USERNAME.github.io/smartfin/frontend/`

---

## 🔧 Backend Deployment Options

GitHub Pages only hosts static files. You need to deploy the backend separately:

### Option 1: Railway (Recommended - Free Tier)

1. Go to https://railway.app/
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose `smartfin` repository
6. Railway auto-detects Python
7. Add start command: `cd backend && python app.py`
8. Click "Deploy"
9. Get your backend URL: `https://smartfin-production.up.railway.app`

**Update `frontend/config.js`:**
```javascript
PRODUCTION_BACKEND: 'https://smartfin-production.up.railway.app'
```

### Option 2: Render (Free Tier)

1. Go to https://render.com/
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect GitHub repository
5. Settings:
   - Name: `smartfin-backend`
   - Root Directory: `backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
6. Click "Create Web Service"
7. Get URL: `https://smartfin-backend.onrender.com`

### Option 3: PythonAnywhere (Free Tier)

1. Go to https://www.pythonanywhere.com/
2. Sign up (free account)
3. Upload your `backend/` folder
4. Create new web app (Flask)
5. Configure WSGI file
6. Reload web app
7. Get URL: `https://YOUR_USERNAME.pythonanywhere.com`

### Option 4: Heroku (No longer free, but popular)

```bash
cd backend

# Install Heroku CLI
# Create Procfile
echo "web: python app.py" > Procfile

# Add runtime.txt
echo "python-3.11.0" > runtime.txt

# Deploy
heroku create smartfin-backend
git push heroku main
```

---

## 🔐 Setting Environment Variables / Secrets

You must never store secrets (like the JWT signing key) in source control. Set `AUTH_JWT_SECRET` and other env vars in your hosting provider or CI secrets.

Examples:

- Railway: In your project, go to **Settings → Variables**, add `AUTH_JWT_SECRET` and any other variables. Railway exposes them to your service at runtime.

- Render: In the service dashboard, go to **Environment → Environment Variables**, add `AUTH_JWT_SECRET` (Key) and paste the secret value. Save and redeploy.

- Heroku (CLI):

```bash
heroku config:set AUTH_JWT_SECRET="$(openssl rand -base64 48)"
```

- GitHub Actions / Workflows: use repository secrets (recommended for Actions workflows).
    1. Go to GitHub repo → Settings → Secrets → Actions → New repository secret.
    2. Add `AUTH_JWT_SECRET` with your secret value.
 3. In workflow, reference it as `${{ secrets.AUTH_JWT_SECRET }}`.

- Local development (PowerShell):

```powershell
$Env:AUTH_JWT_SECRET = 'your-local-dev-secret-32chars'
python services/auth/app.py
```

- Local development (bash):

```bash
export AUTH_JWT_SECRET='your-local-dev-secret-32chars'
python services/auth/app.py
```

- Docker (run):

```bash
docker run -e AUTH_JWT_SECRET=$(openssl rand -base64 48) -p 6000:6000 myauthimage
```

Recommended secret generation (Linux/macOS):

```bash
openssl rand -base64 48
```

Use at least 32 bytes of random entropy for `AUTH_JWT_SECRET` (48 base64 chars is a good choice). Store secrets in your platform's secret manager.


---

## 📝 Quick Deploy Steps

### For GitHub + Railway:

```bash
# 1. Push to GitHub
git add .
git commit -m "SmartFin - ML Financial Health Platform"
git remote add origin https://github.com/YOUR_USERNAME/smartfin.git
git push -u origin main

# 2. Deploy backend on Railway
# - Go to railway.app
# - Deploy from GitHub
# - Get backend URL

# 3. Update config
# Edit frontend/config.js with your Railway URL

# 4. Push update
git add frontend/config.js
git commit -m "Update backend URL"
git push

# 5. Enable GitHub Pages
# Settings → Pages → Source: main branch
```

---

## 🌐 Frontend-Only Deployment (Demo Mode)

If you want to deploy just the frontend without backend:

### Create a demo mode in `frontend/js/app.js`:

Add at the top:
```javascript
const DEMO_MODE = true; // Set to true for demo without backend
```

Then mock the API responses for demonstration purposes.

---

## 📋 Deployment Checklist

### Before Deployment:

- [ ] All files committed to Git
- [ ] `.gitignore` in place
- [ ] README.md updated
- [ ] Backend dependencies in `requirements.txt`
- [ ] Frontend config.js created
- [ ] Test locally one more time

### After Deployment:

- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] GitHub Pages enabled
- [ ] Backend deployed (Railway/Render)
- [ ] Frontend config updated with backend URL
- [ ] Test deployed site
- [ ] Share URL!

---

## 🔗 Your URLs After Deployment

**Frontend (GitHub Pages):**
```
https://YOUR_USERNAME.github.io/smartfin/
```

**Backend (Railway/Render):**
```
https://smartfin-backend.up.railway.app/
```

**API Endpoints:**
```
https://smartfin-backend.up.railway.app/api/predict
https://smartfin-backend.up.railway.app/api/whatif
```

---

## 🐛 Common Deployment Issues

### Issue 1: CORS Error

**Backend needs CORS headers:**

Already configured in `backend/app.py`:
```python
from flask_cors import CORS
CORS(app)
```

### Issue 2: Model File Too Large for Git

ML model file might be >100MB:

```bash
# Use Git LFS
git lfs install
git lfs track "*.pkl"
git add .gitattributes
git commit -m "Add Git LFS"
```

Or host model on cloud storage and download on startup.

### Issue 3: Backend Cold Start

Free tiers sleep after inactivity:
- Railway: Keeps alive on free tier
- Render: Sleeps after 15 min, 30s cold start
- PythonAnywhere: Always on

**Solution:** Add wake-up message in frontend:
```javascript
if (firstLoad) {
    alert("Waking up backend server, please wait 30 seconds...");
}
```

---

## 🎯 Recommended Setup (Best for Demo)

1. **Frontend:** GitHub Pages (Free, Fast, Reliable)
2. **Backend:** Railway (Free, No Sleep, Easy Setup)
3. **Model:** Included in repo (or Git LFS if too large)

---

## 📊 Cost Breakdown

| Service | Cost | Limits |
|---------|------|--------|
| GitHub Pages | FREE | 100GB bandwidth/month |
| Railway | FREE | 500 hours/month, $5 credit |
| Render | FREE | 750 hours/month, sleeps |
| PythonAnywhere | FREE | 1 web app, CPU limits |

**Total Cost: $0** ✅

---

## 🚀 Quick Commands

```bash
# Initialize repo
git init
git add .
git commit -m "SmartFin ML Platform"

# Connect to GitHub (create repo first!)
git remote add origin https://github.com/YOUR_USERNAME/smartfin.git
git push -u origin main

# Update after changes
git add .
git commit -m "Update message"
git push
```

---

## ✅ Next Steps

1. Follow "Step 1-3" above to deploy to GitHub
2. Choose a backend hosting option (Railway recommended)
3. Update `frontend/config.js` with your backend URL
4. Test the deployed site
5. Share with your professor/classmates!

---

**Need help? Check the troubleshooting section or the README.md**

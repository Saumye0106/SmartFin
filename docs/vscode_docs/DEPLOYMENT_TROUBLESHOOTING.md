# Deployment Troubleshooting Guide

## Overview
This guide covers common issues when deploying SmartFin to GitHub Pages (frontend) and Render (backend).

## Deployment Status

### Check Deployment Health
- **Frontend (GitHub Pages)**: https://saumye0106.github.io/SmartFin/
- **Backend (Render)**: https://smartfin-8hyb.onrender.com/
- **Expected Backend Response**: `{"service": "SmartFin Financial Health API", "status": "online", ...}`

## Common Issues

### 1. CORS Errors (Most Common)

**Symptom**: Browser console shows:
```
Access to fetch at 'https://smartfin-8hyb.onrender.com/...' from origin 'https://saumye0106.github.io' has been blocked by CORS policy
```

**Root Cause**: Backend CORS configuration doesn't allow requests from GitHub Pages origin.

**Solution**:
1. Verify `backend/app.py` has correct CORS origins:
   ```python
   CORS(app, origins=["https://saumye0106.github.io", "http://localhost:5173"])
   ```
2. **Critical**: After updating code, redeploy Render backend:
   - Option A: Render Dashboard → Manual Deploy → "Deploy latest commit"
   - Option B: Push to main branch (triggers auto-deploy if configured)
3. Wait 2-3 minutes for deployment to complete
4. Test: Visit frontend, open DevTools Console, check for CORS errors

**Verification**:
```bash
curl -I https://smartfin-8hyb.onrender.com/
# Should include: Access-Control-Allow-Origin: https://saumye0106.github.io
```

### 2. Frontend Shows Blank White Page

**Symptom**: GitHub Pages loads but shows nothing.

**Root Cause**: Asset paths not configured for subdirectory deployment.

**Solution**:
1. Check `frontend/vite.config.js` has:
   ```javascript
   base: './',
   ```
2. Check `frontend/index.html` uses relative paths:
   ```html
   <link rel="icon" type="image/svg+xml" href="./vite.svg" />
   <script type="module" src="./src/main.jsx"></script>
   ```
3. Rebuild and redeploy:
   ```bash
   cd frontend
   npm run build
   git add dist/*
   git commit -m "Fix: Update asset paths"
   git push
   ```

**Verification**:
- Open browser DevTools → Network tab
- Look for 404 errors on `/assets/index-*.js` or `/assets/index-*.css`
- Should see relative paths: `./assets/index-*.js`

### 3. API Calls Go to Localhost Instead of Render

**Symptom**: Network tab shows requests to `http://localhost:5000/` instead of Render URL.

**Root Cause**: Frontend not using production API URLs.

**Solution**:
1. Verify `frontend/src/services/api.js`:
   ```javascript
   const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://smartfin-8hyb.onrender.com';
   const AUTH_BASE_URL = import.meta.env.VITE_AUTH_BASE_URL || 'https://smartfin-8hyb.onrender.com';
   ```
2. Verify `.github/workflows/deploy.yml` sets env vars during build:
   ```yaml
   - name: Build
     env:
       VITE_API_BASE_URL: https://smartfin-8hyb.onrender.com
       VITE_AUTH_BASE_URL: https://smartfin-8hyb.onrender.com
     run: npm run build
   ```
3. Re-run deploy workflow (Actions tab → Deploy to GitHub Pages → Run workflow)

**Verification**:
- Open browser DevTools → Network tab
- Click any feature (predict, login)
- Check request URL starts with `https://smartfin-8hyb.onrender.com`

### 4. Authentication Not Working

**Symptom**: Login/register returns errors or doesn't save session.

**Root Causes**:
- Backend auth service not running
- JWT tokens not being stored
- CORS blocking Set-Cookie headers

**Solutions**:

**A. Verify auth endpoints are live:**
```bash
curl https://smartfin-8hyb.onrender.com/register -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```
Expected: `{"message": "User registered successfully"}` or `{"error": "User already exists"}`

**B. Check browser localStorage:**
- Open DevTools → Application tab → Local Storage
- Look for keys: `token`, `refreshToken`
- If missing after login, check Network tab for `/login` response

**C. Verify CORS allows credentials:**
In `backend/app.py`:
```python
CORS(app, origins=["https://saumye0106.github.io", "http://localhost:5173"], 
     supports_credentials=True)
```

**D. Frontend must send credentials:**
In `frontend/src/services/api.js`, API calls should use:
```javascript
fetch(url, {
  credentials: 'include',  // Send cookies
  headers: { 'Authorization': `Bearer ${token}` }
})
```

### 5. Render Backend Shows "Service Unavailable"

**Symptom**: `https://smartfin-8hyb.onrender.com/` returns 503 or doesn't load.

**Root Causes**:
- Backend crashed or failed to start
- Dependencies missing
- Port configuration incorrect

**Solutions**:

**A. Check Render logs:**
1. Go to Render Dashboard → SmartFin service
2. Click "Logs" tab
3. Look for errors like:
   - `ModuleNotFoundError`: Missing dependency in requirements.txt
   - `Port must be...`: Port config issue
   - Traceback: Code error in app.py

**B. Verify requirements.txt is complete:**
```txt
flask==3.1.0
flask-cors==5.0.0
flask-jwt-extended==4.7.0
scikit-learn==1.6.1
pandas==2.2.3
joblib==1.4.2
numpy==2.2.2
```

**C. Check Procfile or start command:**
Should be: `web: python app.py` or similar

**D. Verify port binding in app.py:**
```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

**E. Model loading errors (ModuleNotFoundError: No module named '_loss'):**
- **Cause**: scikit-learn version mismatch between training and deployment
- **Solution**: Ensure `backend/requirements.txt` matches the version used to train the model
  - If trained with scikit-learn 1.8.0, requirements must have `scikit-learn==1.8.0`
  - Retrain model locally if needed: `cd ml && python train_model.py`
  - Commit updated requirements: `git push` (triggers Render redeploy)

### 6. GitHub Actions Deploy Workflow Fails

**Symptom**: Workflow shows red X, Pages not updated.

**Root Causes**:
- Node version mismatch (Vite needs 20.19+)
- Build errors (TypeScript, linting)
- Missing dependencies

**Solutions**:

**A. Check workflow run logs:**
1. GitHub → Actions tab → Failed workflow
2. Expand "Build" step
3. Look for error message

**B. Common fixes:**

**Node version too old:**
```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20.20.0'  # Must be 20.19+
```

**Build fails locally:**
```bash
cd frontend
npm install
npm run build
# Fix any errors shown
```

**Missing env vars:**
Verify `.github/workflows/deploy.yml` sets:
```yaml
env:
  VITE_API_BASE_URL: https://smartfin-8hyb.onrender.com
  VITE_AUTH_BASE_URL: https://smartfin-8hyb.onrender.com
```

## Testing Full Stack Deployment

### Step 1: Test Backend Health
```bash
curl https://smartfin-8hyb.onrender.com/
```
Expected response:
```json
{
  "service": "SmartFin Financial Health API",
  "status": "online",
  "model": "Gradient Boosting",
  "model_accuracy": "91.97%",
  "version": "1.0"
}
```

### Step 2: Test Frontend Loading
1. Open https://saumye0106.github.io/SmartFin/
2. Open DevTools → Console tab
3. Should see no errors (ignore warnings)
4. Should see SmartFin UI with forms

### Step 3: Test Prediction Flow
1. Fill out financial form with test data
2. Click "Analyze"
3. Check DevTools → Network tab:
   - Should see POST to `https://smartfin-8hyb.onrender.com/predict`
   - Status should be 200
   - Response should contain `score` and `ratios`
4. UI should show financial health score

### Step 4: Test Authentication Flow
1. Click "Register" or "Login"
2. Enter credentials
3. Check DevTools:
   - Network tab: POST to `/register` or `/login` should be 200
   - Application tab → Local Storage: Should see `token` and `refreshToken`
4. Try accessing protected features

## Quick Diagnostic Commands

### Check if backend is responding:
```bash
curl -v https://smartfin-8hyb.onrender.com/
```

### Check CORS headers:
```bash
curl -H "Origin: https://saumye0106.github.io" -I https://smartfin-8hyb.onrender.com/
# Look for: Access-Control-Allow-Origin header
```

### Test prediction endpoint:
```bash
curl -X POST https://smartfin-8hyb.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{"monthly_income":5000,"monthly_expenses":3000,"savings":10000,"debt":2000,"credit_score":720,"loan_payments":500,"investment_income":200,"spending_on_needs":1800,"spending_on_wants":700,"spending_on_savings":500}'
```

### Test auth registration:
```bash
curl -X POST https://smartfin-8hyb.onrender.com/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Password123!"}'
```

## Environment-Specific Notes

### Local Development
- Frontend: `http://localhost:5173` (Vite dev server)
- Backend: `http://localhost:5000` (Flask dev server)
- Auth: `http://localhost:5001` (Auth microservice)
- CORS allows `localhost:5173`

### Production
- Frontend: `https://saumye0106.github.io/SmartFin/` (GitHub Pages)
- Backend: `https://smartfin-8hyb.onrender.com` (Render)
- CORS allows `saumye0106.github.io`
- Env vars set during GitHub Actions build

## Getting Help

If issues persist:
1. Check browser DevTools Console for JavaScript errors
2. Check browser DevTools Network tab for failed requests
3. Check Render logs for backend errors
4. Verify all code changes are committed and deployed
5. Try hard refresh (Ctrl+Shift+R) to clear browser cache

## Status Dashboard Template

Use this checklist when debugging:
- [ ] Backend health check returns 200
- [ ] Frontend loads without blank page
- [ ] No CORS errors in browser console
- [ ] Network requests go to Render, not localhost
- [ ] Prediction endpoint returns valid response
- [ ] Auth endpoints return valid responses
- [ ] Tokens saved to localStorage after login
- [ ] GitHub Actions workflow passing
- [ ] Render deployment status is "Live"

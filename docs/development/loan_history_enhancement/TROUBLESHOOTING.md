# Loan History Enhancement - Troubleshooting Guide

**Date:** February 27, 2026

---

## Common Issues and Solutions

### Issue 1: Loan Metrics Showing for Users Without Loans

**Problem**: The loan metrics dashboard was displaying default/baseline scores even when users had no loans added to their account.

**Root Cause**: The component was fetching and displaying metrics regardless of whether the user had any loan data.

**Solution**: Added a check in `LoanMetricsDashboard.jsx` to verify `total_active_loans > 0` before displaying metrics. When no loans exist, the component now shows an empty state with:
- A friendly message: "No loans added yet"
- Explanation text about tracking loans
- "Add Your First Loan" button that navigates to `/loans`

**Files Modified**:
- `frontend/src/components/LoanMetricsDashboard.jsx` (lines 140-170)

**Implementation Details**:
```javascript
// Check if user actually has loans
const hasLoans = loan_statistics && loan_statistics.total_active_loans > 0;

if (!hasLoans) {
  return (
    <div className="text-center py-12">
      <iconify-icon icon="solar:wallet-money-linear" width="64" className="text-white/20 mb-4"></iconify-icon>
      <p className="text-white/40 mb-2">No loans added yet</p>
      <p className="text-white/20 text-sm mb-6">Start tracking your loans to see personalized metrics and improve your financial health score</p>
      <button
        onClick={() => window.location.href = '/loans'}
        className="px-6 py-3 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 transition-all text-sm font-medium flex items-center gap-2 mx-auto"
      >
        <iconify-icon icon="solar:add-circle-linear" width="20"></iconify-icon>
        Add Your First Loan
      </button>
    </div>
  );
}
```

**Backend Behavior**: The backend `getLoanStatistics()` method returns `total_active_loans: 0` when no loans exist, which the frontend uses to determine whether to show metrics or the empty state.

---

### Issue 3: Adding a Loan Redirects to Login Page

**Problem**: When users try to create a new loan, they are immediately redirected to the login page instead of the loan being created.

**Root Cause**: This is a 401 authentication error, which can be caused by:
1. **Expired JWT token** - The token has exceeded its expiration time (default: 1 hour)
2. **Missing token** - The token was not properly stored during login
3. **Invalid token format** - The token is malformed or corrupted
4. **Token not sent with request** - The Authorization header is missing or incorrect

**Debugging Steps**:

1. **Check browser console** - Look for detailed 401 error logs:
   ```
   === 401 AUTHENTICATION ERROR ===
   Request URL: http://127.0.0.1:5000/api/loans
   Request method: post
   Request headers: {...}
   Error response: {...}
   Token in localStorage: ...
   Token in axios defaults: ...
   ================================
   ```

2. **Verify token exists**:
   ```javascript
   // In browser console
   localStorage.getItem('sf_token')
   localStorage.getItem('userId')
   ```

3. **Check token expiration**:
   - JWT tokens expire after 1 hour by default
   - If you've been logged in for more than 1 hour, you need to log in again
   - Solution: Implement token refresh or increase token expiration time

4. **Verify token is being sent**:
   - Check Network tab in DevTools
   - Look at the request headers for `/api/loans` POST request
   - Should see: `Authorization: Bearer <token>`

**Solutions**:

**Solution 1: Re-login if token expired**
- Simply log out and log back in to get a fresh token
- This is the quickest fix for testing

**Solution 2: Increase token expiration (backend)**
```python
# In backend/app.py
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Increase to 24 hours
```

**Solution 3: Implement token refresh**
- Add a refresh token endpoint
- Automatically refresh the access token when it expires
- This requires more complex implementation

**Solution 4: Check token storage during login**
- Verify `AuthPage.jsx` is storing the token correctly:
```javascript
// Should be in handleLogin and handleRegister
localStorage.setItem('sf_token', response.token);
localStorage.setItem('userId', response.user.id.toString());
localStorage.setItem('userEmail', response.user.email);
api.setAuthToken(response.token);
```

**Files to Check**:
- `frontend/src/services/api.js` - Token handling and axios interceptor
- `frontend/src/components/AuthPage.jsx` - Token storage during login
- `frontend/src/components/LoanManagementPage.jsx` - Error handling
- `backend/app.py` - JWT configuration and loan creation endpoint

**Prevention**:
- Implement automatic token refresh before expiration
- Add token expiration warning to UI
- Store token expiration time and check before making requests

---

### Issue 2: "Failed to get loan metrics" Error

**Symptoms:**
- Error message appears when loading the dashboard
- Loan metrics section fails to load
- Console shows "Failed to get loan metrics"

**Root Cause:**
The `user.id` was not being stored in localStorage when the user logged in, causing the API call to fail.

**Solution:**
✅ **Fixed in latest version**

The following changes were made:

1. **AuthPage.jsx** - Now stores userId in localStorage during login/registration:
```javascript
if (response.user?.id) {
  localStorage.setItem('userId', response.user.id.toString());
}
```

2. **App.jsx** - Now retrieves userId from localStorage on app load:
```javascript
const userId = localStorage.getItem('userId');
setUser({ 
  id: userId ? parseInt(userId) : null,
  email: email
});
```

3. **MainDashboard.jsx** - Added check to ensure userId exists before rendering:
```javascript
{user && user.id && (
  <LoanMetricsDashboard userId={user.id} ... />
)}
```

**For Existing Users:**
If you're already logged in, you need to:
1. Log out
2. Log back in
3. The userId will now be stored correctly

---

### Issue 2: Loan Metrics Not Showing

**Symptoms:**
- Dashboard loads but shows "No metrics available"
- No loans appear in the list

**Possible Causes:**
1. No loans have been added yet
2. Database tables not created
3. User doesn't have any active loans

**Solution:**

**Check 1: Verify Database Tables**
```bash
cd backend
python misc/verify_loan_tables.py
```

**Check 2: Add a Test Loan**
1. Navigate to Profile page
2. Click "Loan Management"
3. Click "Add Loan"
4. Fill in loan details and submit

**Check 3: Check Backend Logs**
Look for errors in the Flask console when accessing `/api/loans/metrics/<user_id>`

---

### Issue 3: 403 Forbidden Error

**Symptoms:**
- API returns 403 status code
- Error message: "Not authorized to access this user's metrics"

**Root Cause:**
The JWT token's user ID doesn't match the requested user ID.

**Solution:**
1. Clear browser cache and localStorage
2. Log out and log back in
3. Ensure you're accessing your own metrics (not another user's)

---

### Issue 4: 500 Internal Server Error

**Symptoms:**
- API returns 500 status code
- Backend logs show database errors

**Possible Causes:**
1. Database tables not created
2. Database file permissions issue
3. Corrupted database

**Solution:**

**Step 1: Run Database Migration**
```bash
cd backend
python misc/migrate_add_loan_tables.py
```

**Step 2: Verify Tables**
```bash
python misc/verify_loan_tables.py
```

**Step 3: Check Database File**
```bash
# Check if auth.db exists and has correct permissions
ls -la auth.db
```

**Step 4: Restart Backend**
```bash
python app.py
```

---

### Issue 5: Loan Metrics Dashboard Shows Loading Forever

**Symptoms:**
- Dashboard shows "Loading metrics..." indefinitely
- No error message appears

**Root Cause:**
API request is hanging or not completing.

**Solution:**

**Check 1: Verify Backend is Running**
```bash
# Visit http://localhost:5000
# Should show API status
```

**Check 2: Check Browser Console**
```
F12 → Console tab
Look for network errors or CORS issues
```

**Check 3: Check Network Tab**
```
F12 → Network tab
Look for the /api/loans/metrics request
Check status code and response
```

**Check 4: Verify JWT Token**
```javascript
// In browser console
localStorage.getItem('token')
// Should return a valid JWT token
```

---

### Issue 6: Loan Form Validation Errors

**Symptoms:**
- Form shows validation errors
- Cannot submit loan

**Common Validation Rules:**
- Loan amount must be positive
- Interest rate must be between 0 and 100
- Loan tenure must be positive
- Start date cannot be in the future
- Maturity date must be after start date
- EMI must be positive

**Solution:**
Review the validation error messages and adjust the form values accordingly.

---

### Issue 7: Payment Recording Fails

**Symptoms:**
- Payment form shows error
- Payment not recorded

**Common Issues:**
1. Payment date in the future
2. Payment amount is negative or zero
3. Payment amount exceeds remaining balance

**Solution:**
- Ensure payment date is today or in the past
- Enter a valid positive amount
- Check remaining loan balance

---

## Debugging Tips

### Enable Debug Logging

**Backend:**
```python
# In app.py, set logging level to DEBUG
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
// In api.js, add console.log statements
console.log('API Request:', url, data);
console.log('API Response:', response);
```

### Check API Endpoints Manually

**Using curl:**
```bash
# Get loan metrics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/loans/metrics/1

# Get user loans
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/loans/1
```

**Using Browser:**
1. Open Developer Tools (F12)
2. Go to Network tab
3. Perform the action that's failing
4. Click on the failed request
5. Check Request Headers, Response, and Status

### Verify Database State

**Check if tables exist:**
```bash
cd backend
sqlite3 auth.db ".tables"
# Should show: loans, loan_payments, loan_metrics
```

**Check loan data:**
```bash
sqlite3 auth.db "SELECT * FROM loans LIMIT 5;"
```

**Check metrics data:**
```bash
sqlite3 auth.db "SELECT * FROM loan_metrics;"
```

---

## Getting Help

If you're still experiencing issues:

1. **Check the logs:**
   - Backend: Flask console output
   - Frontend: Browser console (F12)

2. **Verify the setup:**
   - Database tables created
   - Backend running on port 5000
   - Frontend running on port 8000 (or 3000)

3. **Test the API directly:**
   - Use curl or Postman
   - Verify endpoints work independently

4. **Review the documentation:**
   - `FEATURE_COMPLETE.md` - Feature overview
   - `IMPLEMENTATION_SUMMARY.md` - Technical details
   - `VALIDATION_ERROR_HANDLING.md` - Error codes

---

## Quick Fixes

### Reset Everything
```bash
# 1. Stop backend
# 2. Backup database
cp backend/auth.db backend/auth.db.backup

# 3. Re-run migrations
cd backend
python misc/migrate_add_loan_tables.py

# 4. Restart backend
python app.py

# 5. Clear browser data
# - Clear localStorage
# - Clear cookies
# - Hard refresh (Ctrl+Shift+R)

# 6. Log in again
```

### Clear Browser Data
```javascript
// In browser console
localStorage.clear();
location.reload();
```

### Verify JWT Token
```javascript
// In browser console
const token = localStorage.getItem('token');
console.log('Token:', token);

// Decode JWT (without verification)
const payload = JSON.parse(atob(token.split('.')[1]));
console.log('User ID:', payload.sub);
```

---

## Prevention

To avoid these issues in the future:

1. **Always log out/in after updates** - Ensures localStorage is fresh
2. **Check backend logs** - Catch errors early
3. **Use browser dev tools** - Monitor network requests
4. **Keep database backed up** - Easy recovery if needed
5. **Test in incognito mode** - Verify clean state works

---

**Document Version:** 1.0.0  
**Last Updated:** February 27, 2026  
**Status:** Active

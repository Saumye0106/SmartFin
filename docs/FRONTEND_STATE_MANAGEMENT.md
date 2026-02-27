# SmartFin Frontend - State Management Documentation

**Date:** February 27, 2026  
**Framework:** React 18 with React Router v6  
**Status:** Current Implementation

---

## Overview

SmartFin's frontend uses **React's built-in state management** (useState, useContext) rather than Redux. While Redux is listed in package.json as a dependency, it is **NOT actively used** in the current implementation.

---

## Current State Management Approach

### Why Not Redux?

The application uses **local component state** instead of Redux because:

1. **Simpler Architecture** - Fewer moving parts for a single-page application
2. **Easier Debugging** - State changes are easier to trace
3. **Smaller Bundle** - Reduces JavaScript payload
4. **Sufficient for Current Needs** - App doesn't have deeply nested state requirements
5. **Easier Onboarding** - Developers familiar with React hooks can contribute immediately

---

## State Structure in App.jsx

The main application state is managed in the `AppContent` component:

```javascript
// Authentication & User State
const [user, setUser] = useState(null);
const [authLoading, setAuthLoading] = useState(true);

// Financial Analysis State
const [loading, setLoading] = useState(false);
const [result, setResult] = useState(null);
const [currentData, setCurrentData] = useState(null);
const [error, setError] = useState(null);
```

### State Variables Explained

| State | Type | Purpose | Initial Value |
|-------|------|---------|---------------|
| `user` | Object | Current logged-in user info | null |
| `authLoading` | Boolean | Auth check in progress | true |
| `loading` | Boolean | Financial analysis in progress | false |
| `result` | Object | Financial score result | null |
| `currentData` | Object | Current financial data submitted | null |
| `error` | String | Error message | null |

---

## State Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    App Component                        │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  AppContent (Main State Container)               │  │
│  │                                                  │  │
│  │  State:                                          │  │
│  │  ├─ user (auth state)                           │  │
│  │  ├─ authLoading (auth check)                    │  │
│  │  ├─ loading (analysis in progress)              │  │
│  │  ├─ result (score result)                       │  │
│  │  ├─ currentData (submitted data)                │  │
│  │  └─ error (error messages)                      │  │
│  │                                                  │  │
│  │  Handlers:                                       │  │
│  │  ├─ handleAnalyze() → calls /api/predict        │  │
│  │  ├─ handleWhatIf() → calls /api/whatif          │  │
│  │  ├─ handleAuth() → sets user & token            │  │
│  │  ├─ handleLogout() → clears all state           │  │
│  │  └─ ProtectedRoute → checks auth                │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                          │                              │
│         ┌────────────────┼────────────────┐             │
│         ▼                ▼                ▼             │
│    ┌─────────┐    ┌──────────┐    ┌────────────┐      │
│    │ Landing │    │ Auth     │    │ Dashboard  │      │
│    │ Page    │    │ Page     │    │ (Protected)│      │
│    └─────────┘    └──────────┘    └────────────┘      │
│                                                         │
│    ┌─────────┐    ┌──────────┐    ┌────────────┐      │
│    │ Profile │    │ Goals    │    │ Loans      │      │
│    │ (Prot.) │    │ (Prot.)  │    │ (Prot.)    │      │
│    └─────────┘    └──────────┘    └────────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Authentication State Management

### Initial Load
```javascript
useEffect(() => {
  const storedToken = api.getStoredToken();
  if (storedToken) {
    api.setAuthToken(storedToken);
    const email = localStorage.getItem('userEmail') || 'user@smartfin.com';
    const userId = localStorage.getItem('userId');
    setUser({ 
      id: userId ? parseInt(userId) : null,
      email: email
    });
  }
  setAuthLoading(false);
}, []);
```

**Flow:**
1. Check localStorage for stored JWT token
2. If token exists, restore it in API headers
3. Restore user info from localStorage
4. Set authLoading to false

### Login Flow
```javascript
const handleAuth = (authResponse) => {
  const token = authResponse?.token;
  if (token) {
    api.setAuthToken(token);
    const email = localStorage.getItem('userEmail') || authResponse?.email;
    setUser({ 
      id: authResponse?.id, 
      email: email
    });
    navigate('/dashboard');
  }
};
```

**Flow:**
1. Receive auth response from backend
2. Extract JWT token
3. Set token in API headers
4. Store user info in state
5. Navigate to dashboard

### Logout Flow
```javascript
const handleLogout = () => {
  api.setAuthToken(null);
  setUser(null);
  setResult(null);
  setCurrentData(null);
  setError(null);
  localStorage.removeItem('userId');
  navigate('/');
};
```

**Flow:**
1. Clear API token
2. Clear all state
3. Clear localStorage
4. Navigate to home

---

## Financial Analysis State Management

### Score Prediction Flow
```javascript
const handleAnalyze = async (financialData) => {
  setLoading(true);
  setError(null);
  
  try {
    const response = await api.predict(financialData);
    setResult(response);
    setCurrentData(financialData);
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};
```

**State Changes:**
1. `setLoading(true)` - Show loading indicator
2. `setError(null)` - Clear previous errors
3. Call API `/api/predict`
4. `setResult(response)` - Store score result
5. `setCurrentData(financialData)` - Store submitted data
6. `setLoading(false)` - Hide loading indicator

### What-If Simulation Flow
```javascript
const handleWhatIf = async (current, modified) => {
  try {
    const response = await api.whatIf(current, modified);
    return response;
  } catch (err) {
    console.error('Error in what-if simulation:', err);
    throw err;
  }
};
```

**Note:** What-if results are returned directly without storing in state (used for temporary comparison)

---

## Protected Routes Implementation

```javascript
const ProtectedRoute = ({ children }) => {
  const hasToken = api.getStoredToken();
  const hasUserId = localStorage.getItem('userId');
  
  if (authLoading) {
    return <LoadingSpinner />;
  }
  
  if (!user && hasToken && hasUserId) {
    // Restore user state
    const email = localStorage.getItem('userEmail') || 'user@smartfin.com';
    const userId = localStorage.getItem('userId');
    setUser({ 
      id: userId ? parseInt(userId) : null,
      email: email
    });
    return <LoadingSpinner />;
  }
  
  if (!user) {
    return <Navigate to="/auth" replace />;
  }
  
  return children;
};
```

**Protection Logic:**
1. Check if auth is still loading
2. If no user but token exists, restore user state
3. If no user and no token, redirect to auth
4. Otherwise, render protected component

---

## Local Storage Usage

SmartFin uses localStorage for persistence:

```javascript
// Stored Items
localStorage.getItem('userId')        // User ID
localStorage.getItem('userEmail')     // User email
localStorage.getItem('token')         // JWT token (via api service)

// Clearing on logout
localStorage.removeItem('userId')
```

**Why localStorage?**
- Persists across page refreshes
- Survives browser restarts
- Simple key-value storage
- No server-side session needed

---

## API Service State Management

The `api.js` service manages API-level state:

```javascript
// Token management
api.getStoredToken()      // Retrieve stored token
api.setAuthToken(token)   // Set token in headers

// API calls
api.predict(data)         // POST /api/predict
api.whatIf(current, mod)  // POST /api/whatif
api.register(data)        // POST /api/register
api.login(data)           // POST /api/login
```

---

## Component State Patterns

### Individual Component State

Each component manages its own local state:

```javascript
// Example: FinancialForm.jsx
const [formData, setFormData] = useState({
  income: '',
  rent: '',
  food: '',
  travel: '',
  shopping: '',
  emi: '',
  savings: ''
});

const [errors, setErrors] = useState({});
const [submitted, setSubmitted] = useState(false);
```

### Props Drilling

State is passed down through props:

```javascript
<MainDashboard
  user={user}
  onLogout={handleLogout}
  onAnalyze={handleAnalyze}
  onWhatIf={handleWhatIf}
  loading={loading}
  result={result}
  currentData={currentData}
  error={error}
/>
```

---

## State Management Best Practices Used

### 1. Single Source of Truth
- App-level state in AppContent
- Passed down to child components
- Prevents state duplication

### 2. Unidirectional Data Flow
```
User Input → Handler Function → setState → Re-render
```

### 3. Error Handling
```javascript
setError(null);  // Clear before request
try {
  // API call
} catch (err) {
  setError(err.message);  // Set on error
}
```

### 4. Loading States
```javascript
setLoading(true);   // Before request
// API call
setLoading(false);  // After request (finally block)
```

---

## Future State Management Considerations

### When to Consider Redux

Redux would be beneficial if:
1. **Deeply Nested Components** - Many levels of prop drilling
2. **Complex State Logic** - Multiple interdependent state updates
3. **Time-Travel Debugging** - Need to replay state changes
4. **Middleware Needs** - Logging, analytics, async actions
5. **Large Team** - Standardized patterns needed

### Migration Path

If Redux becomes necessary:

```javascript
// Current (useState)
const [result, setResult] = useState(null);

// Future (Redux)
const result = useSelector(state => state.analysis.result);
const dispatch = useDispatch();
dispatch(setAnalysisResult(response));
```

---

## Performance Considerations

### Current Approach
- ✅ Minimal re-renders (only affected components)
- ✅ No middleware overhead
- ✅ Fast state updates
- ✅ Small bundle size

### Potential Issues
- ⚠️ Prop drilling if app grows significantly
- ⚠️ No built-in time-travel debugging
- ⚠️ State logic scattered across components

---

## Summary

| Aspect | Current Implementation |
|--------|----------------------|
| **State Management** | React useState hooks |
| **Global State** | App-level state in AppContent |
| **Local State** | Component-level useState |
| **Persistence** | localStorage for auth |
| **API State** | Managed in api.js service |
| **Routing** | React Router v6 |
| **Redux** | Listed in package.json but NOT used |
| **Context API** | Not currently used |
| **Prop Drilling** | Minimal (only 1-2 levels) |

---

## Code Examples

### Accessing State in Components

```javascript
// In MainDashboard.jsx
function MainDashboard({ user, result, loading, error, onAnalyze }) {
  return (
    <div>
      {loading && <LoadingSpinner />}
      {error && <ErrorMessage message={error} />}
      {result && <ScoreDisplay score={result.score} />}
      <FinancialForm onSubmit={onAnalyze} />
    </div>
  );
}
```

### Updating State

```javascript
// In FinancialForm.jsx
const handleSubmit = (e) => {
  e.preventDefault();
  if (validateForm()) {
    onAnalyze(formData);  // Pass to parent handler
  }
};
```

### Conditional Rendering Based on State

```javascript
// In App.jsx
{user ? (
  <ProtectedRoute>
    <MainDashboard {...props} />
  </ProtectedRoute>
) : (
  <LandingPage />
)}
```

---

## Conclusion

SmartFin's frontend uses a **simple, effective state management approach** with React hooks and localStorage. This is appropriate for the current application size and complexity. As the application grows, Redux or Context API can be introduced without major refactoring.

---

**Document Status:** Complete  
**Last Updated:** February 27, 2026

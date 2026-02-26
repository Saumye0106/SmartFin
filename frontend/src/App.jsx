import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import './App.css';
import api from './services/api';
import ErrorBoundary from './components/ErrorBoundary';
import LandingPage from './components/LandingPage';
import AuthPage from './components/AuthPage';
import MainDashboard from './components/MainDashboard';
import ProfilePage from './components/ProfilePage';
import ProfileEditForm from './components/ProfileEditForm';
import GoalsManager from './components/GoalsManager';
import RiskAssessment from './components/RiskAssessment';
import SIPCalculator from './components/SIPCalculator';
import ForgotPassword from './components/ForgotPassword';
import EmailVerification from './components/EmailVerification';

// Wrapper component to use navigate hook
function AppContent() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [currentData, setCurrentData] = useState(null);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);

  // Check for stored token on app load
  useEffect(() => {
    const storedToken = api.getStoredToken();
    if (storedToken) {
      // Set the token in API headers
      api.setAuthToken(storedToken);
      // Get email from localStorage
      const email = localStorage.getItem('userEmail') || 'user@smartfin.com';
      setUser({ 
        email: email
      });
    }
  }, []);

  const handleAnalyze = async (financialData) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.predict(financialData);
      setResult(response);
      setCurrentData(financialData);
    } catch (err) {
      setError(err.message);
      console.error('Error analyzing finances:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleWhatIf = async (current, modified) => {
    try {
      const response = await api.whatIf(current, modified);
      return response;
    } catch (err) {
      console.error('Error in what-if simulation:', err);
      throw err;
    }
  };

  const handleAuth = (authResponse) => {
    // authResponse expected to contain token and user id/email
    const token = authResponse?.token;
    if (token) {
      api.setAuthToken(token);
      // Get email from localStorage or authResponse
      const email = localStorage.getItem('userEmail') || authResponse?.user?.email || authResponse?.email || 'user@smartfin.com';
      setUser({ 
        id: authResponse?.user?.id || authResponse?.id, 
        email: email
      });
      navigate('/dashboard'); // Navigate to dashboard after successful auth
    }
  };

  const handleGetStarted = () => {
    if (user) {
      // If already logged in, go directly to dashboard
      navigate('/dashboard');
    } else {
      // Otherwise show auth page
      navigate('/auth');
    }
  };

  const handleBackToLanding = () => {
    navigate('/');
  };

  const handleLogout = () => {
    api.setAuthToken(null);
    setUser(null);
    setResult(null);
    setCurrentData(null);
    setError(null);
    navigate('/');
  };

  // Protected Route Component
  const ProtectedRoute = ({ children }) => {
    if (!user) {
      return <Navigate to="/auth" replace />;
    }
    return children;
  };

  return (
    <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage onGetStarted={handleGetStarted} />} />
          
          <Route path="/auth" element={<AuthPage onAuthSuccess={handleAuth} onBack={handleBackToLanding} />} />
          
          <Route path="/forgot-password" element={<ForgotPassword />} />
          
          <Route path="/verify-email" element={<EmailVerification />} />

          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <ErrorBoundary fallbackMessage="Error loading dashboard. Please try again.">
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
              </ErrorBoundary>
            </ProtectedRoute>
          } />

          <Route path="/profile" element={
            <ProtectedRoute>
              <ErrorBoundary fallbackMessage="Error loading profile. Please try again.">
                <ProfilePage />
              </ErrorBoundary>
            </ProtectedRoute>
          } />

          <Route path="/profile/create" element={
            <ProtectedRoute>
              <ErrorBoundary fallbackMessage="Error loading profile form. Please try again.">
                <ProfileEditForm />
              </ErrorBoundary>
            </ProtectedRoute>
          } />

          <Route path="/profile/edit" element={
            <ProtectedRoute>
              <ErrorBoundary fallbackMessage="Error loading profile form. Please try again.">
                <ProfileEditForm />
              </ErrorBoundary>
            </ProtectedRoute>
          } />

          <Route path="/goals" element={
            <ProtectedRoute>
              <ErrorBoundary fallbackMessage="Error loading goals manager. Please try again.">
                <GoalsManager />
              </ErrorBoundary>
            </ProtectedRoute>
          } />

          <Route path="/risk-assessment" element={
            <ProtectedRoute>
              <ErrorBoundary fallbackMessage="Error loading risk assessment. Please try again.">
                <RiskAssessment />
              </ErrorBoundary>
            </ProtectedRoute>
          } />

          <Route path="/sip-calculator" element={
            <ProtectedRoute>
              <ErrorBoundary fallbackMessage="Error loading SIP calculator. Please try again.">
                <SIPCalculator />
              </ErrorBoundary>
            </ProtectedRoute>
          } />

          {/* Catch all - redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
  );
}

// Main App component with Router wrapper
function App() {
  return (
    <ErrorBoundary fallbackMessage="Something went wrong with the application. Please refresh the page.">
      <Router>
        <AppContent />
      </Router>
    </ErrorBoundary>
  );
}

export default App;

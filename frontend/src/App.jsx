import { useState, useEffect } from 'react';
import './App.css';
import FinancialForm from './components/FinancialForm';
import ScoreDisplay from './components/ScoreDisplay';
import SpendingChart from './components/SpendingChart';
import RatiosDashboard from './components/RatiosDashboard';
import AlertsPanel from './components/AlertsPanel';
import GuidancePanel from './components/GuidancePanel';
import InvestmentAdvice from './components/InvestmentAdvice';
import WhatIfSimulator from './components/WhatIfSimulator';
import api from './services/api';
import AuthForm from './components/AuthForm';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [currentData, setCurrentData] = useState(null);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
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
      setUser({ id: authResponse.id, email: authResponse.email });
    }
  };

  const handleLogout = () => {
    api.setAuthToken(null);
    setUser(null);
  };

  return (
    <div className="app">
      <div className="scanlines"></div>
      <div className="grid-overlay"></div>
      
      <header className="app-header">
        <div className="container">
          <div className="header-content">
            <div className="logo-section">
              <div className="logo-bracket">[</div>
              <h1 className="app-title">SMARTFIN</h1>
              <div className="logo-bracket">]</div>
            </div>
            <div className="header-meta">
              <div className="status-indicator">
                <span className="status-dot"></span>
                <span className="status-text">SYSTEM ACTIVE</span>
              </div>
              <div className="time-display">
                {currentTime.toLocaleTimeString('en-US', { hour12: false })}
              </div>
            </div>
          </div>
          <div className="app-subtitle">
            <span className="subtitle-label">ML-POWERED</span>
            <span className="subtitle-separator">|</span>
            <span className="subtitle-label">FINANCIAL INTELLIGENCE</span>
            <span className="subtitle-separator">|</span>
            <span className="subtitle-label">REAL-TIME ANALYSIS</span>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          {error && (
            <div className="error-banner">
              <div className="error-icon">⚠</div>
              <div className="error-content">
                <div className="error-title">SYSTEM ERROR</div>
                <div className="error-message">{error}</div>
              </div>
            </div>
          )}

          {!user ? (
            <div className="auth-container">
              <AuthForm onAuth={handleAuth} />
            </div>
          ) : (
            <>
              <div className="user-panel">
                <div className="user-info">
                  <span className="user-label">OPERATOR</span>
                  <span className="user-email">{user.email}</span>
                </div>
                <button className="logout-btn" onClick={handleLogout}>
                  <span className="btn-bracket">[</span>
                  DISCONNECT
                  <span className="btn-bracket">]</span>
                </button>
              </div>

              <FinancialForm onSubmit={handleAnalyze} loading={loading} />
            </>
          )}

          {loading && (
            <div className="loading-container">
              <div className="loading-content">
                <div className="loading-bars">
                  <div className="loading-bar"></div>
                  <div className="loading-bar"></div>
                  <div className="loading-bar"></div>
                  <div className="loading-bar"></div>
                  <div className="loading-bar"></div>
                </div>
                <div className="loading-text">
                  <span className="loading-label">PROCESSING</span>
                  <span className="loading-dots"></span>
                </div>
                <div className="loading-status">Analyzing financial data streams...</div>
              </div>
            </div>
          )}

          {result && !loading && (
            <div className="results-section">
              <div className="results-header">
                <div className="results-title">ANALYSIS COMPLETE</div>
                <div className="results-timestamp">
                  {new Date().toLocaleString('en-US', { 
                    month: 'short', 
                    day: 'numeric', 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>

              <ScoreDisplay 
                score={result.score} 
                classification={result.classification} 
              />

              <div className="dashboard-grid">
                <SpendingChart patterns={result.patterns} />
                <RatiosDashboard patterns={result.patterns} />
              </div>

              <AlertsPanel anomalies={result.anomalies} />
              
              <GuidancePanel guidance={result.guidance} />
              
              <InvestmentAdvice investments={result.investments} />
              
              <WhatIfSimulator 
                currentData={currentData} 
                onSimulate={handleWhatIf}
              />
            </div>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-section">
              <span className="footer-label">VERSION</span>
              <span className="footer-value">2.0.4</span>
            </div>
            <div className="footer-section">
              <span className="footer-label">STATUS</span>
              <span className="footer-value">OPERATIONAL</span>
            </div>
            <div className="footer-section">
              <span className="footer-label">LATENCY</span>
              <span className="footer-value">12ms</span>
            </div>
            <div className="footer-section footer-note">
              <span className="footer-label">⚠ EDUCATIONAL USE ONLY</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

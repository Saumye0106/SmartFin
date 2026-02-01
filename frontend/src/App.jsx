import { useState } from 'react';
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

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [currentData, setCurrentData] = useState(null);
  const [error, setError] = useState(null);

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

  return (
    <div className="app">
      <header className="app-header">
        <div className="container">
          <h1 className="app-title">💰 SmartFin</h1>
          <p className="app-subtitle">ML-Based Financial Health Platform</p>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          {error && (
            <div className="error-banner">
              <strong>Error:</strong> {error}
            </div>
          )}

          <FinancialForm onSubmit={handleAnalyze} loading={loading} />

          {loading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Analyzing your financial health...</p>
            </div>
          )}

          {result && !loading && (
            <div className="results-section">
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
          <p>SmartFin v1.0 - Powered by Machine Learning</p>
          <p className="footer-note">⚠️ For educational purposes only</p>
        </div>
      </footer>
    </div>
  );
}

export default App;

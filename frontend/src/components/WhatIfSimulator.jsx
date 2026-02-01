import { useState } from 'react';
import './WhatIfSimulator.css';

const WhatIfSimulator = ({ currentData, onSimulate }) => {
  const [modifiedData, setModifiedData] = useState({
    shopping: currentData?.shopping || 0,
    savings: currentData?.savings || 0
  });

  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setModifiedData(prev => ({
      ...prev,
      [name]: Number(value)
    }));
  };

  const handleSimulate = async () => {
    if (!currentData) return;

    setLoading(true);
    try {
      const result = await onSimulate(currentData, {
        ...currentData,
        shopping: modifiedData.shopping,
        savings: modifiedData.savings
      });
      setSimulationResult(result);
    } catch (error) {
      console.error('Simulation error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!currentData) return null;

  return (
    <div className="whatif-simulator-container">
      <h2 className="section-title">🔮 What-If Simulator</h2>
      <p className="simulator-description">
        Test different scenarios to see how changes affect your financial health score
      </p>
      
      <div className="simulator-controls">
        <div className="control-group">
          <label htmlFor="shopping">Shopping & Entertainment (₹)</label>
          <div className="input-with-current">
            <input
              type="number"
              id="shopping"
              name="shopping"
              value={modifiedData.shopping}
              onChange={handleChange}
              min="0"
            />
            <span className="current-value">Current: ₹{currentData.shopping?.toLocaleString()}</span>
          </div>
        </div>

        <div className="control-group">
          <label htmlFor="savings">Monthly Savings (₹)</label>
          <div className="input-with-current">
            <input
              type="number"
              id="savings"
              name="savings"
              value={modifiedData.savings}
              onChange={handleChange}
              min="0"
            />
            <span className="current-value">Current: ₹{currentData.savings?.toLocaleString()}</span>
          </div>
        </div>

        <button 
          className="btn btn-simulate" 
          onClick={handleSimulate}
          disabled={loading}
        >
          {loading ? 'Simulating...' : '🚀 Run Simulation'}
        </button>
      </div>

      {simulationResult && (
        <div className="simulation-results">
          <h3 className="results-title">Simulation Results</h3>
          
          <div className="results-grid">
            <div className="result-card">
              <div className="result-label">Current Score</div>
              <div className="result-value current">{simulationResult.current_score?.toFixed(1)}</div>
            </div>

            <div className="result-card arrow-card">
              <div className={`impact-arrow impact-${simulationResult.impact}`}>
                {simulationResult.impact === 'positive' ? '↗️' : 
                 simulationResult.impact === 'negative' ? '↘️' : '➡️'}
              </div>
              <div className={`score-change change-${simulationResult.impact}`}>
                {simulationResult.score_change > 0 ? '+' : ''}
                {simulationResult.score_change?.toFixed(1)}
              </div>
            </div>

            <div className="result-card">
              <div className="result-label">New Score</div>
              <div className="result-value modified">{simulationResult.modified_score?.toFixed(1)}</div>
            </div>
          </div>

          <div className="classification-comparison">
            <div className="classification-item">
              <span className="classification-label">Current:</span>
              <span className="classification-badge" style={{ 
                backgroundColor: `${simulationResult.current_classification?.color}20`,
                color: simulationResult.current_classification?.color 
              }}>
                {simulationResult.current_classification?.emoji} {simulationResult.current_classification?.category}
              </span>
            </div>

            <div className="classification-item">
              <span className="classification-label">After Changes:</span>
              <span className="classification-badge" style={{ 
                backgroundColor: `${simulationResult.modified_classification?.color}20`,
                color: simulationResult.modified_classification?.color 
              }}>
                {simulationResult.modified_classification?.emoji} {simulationResult.modified_classification?.category}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WhatIfSimulator;

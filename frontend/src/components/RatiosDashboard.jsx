import { useEffect, useState } from 'react';
import './RatiosDashboard.css';

const RatiosDashboard = ({ patterns }) => {
  const [animatedRatios, setAnimatedRatios] = useState({
    expense_ratio: 0,
    savings_ratio: 0,
    emi_ratio: 0
  });

  useEffect(() => {
    if (patterns) {
      const duration = 1000; // 1 second
      const steps = 50;
      const stepTime = duration / steps;

      let currentStep = 0;

      const timer = setInterval(() => {
        currentStep++;
        const progress = currentStep / steps;

        setAnimatedRatios({
          expense_ratio: patterns.expense_ratio * progress,
          savings_ratio: patterns.savings_ratio * progress,
          emi_ratio: patterns.emi_ratio * progress
        });

        if (currentStep >= steps) {
          clearInterval(timer);
        }
      }, stepTime);

      return () => clearInterval(timer);
    }
  }, [patterns]);

  if (!patterns) return null;

  const getRatioColor = (ratio, type) => {
    if (type === 'expense') {
      if (ratio > 0.8) return '#ef4444';
      if (ratio > 0.7) return '#f97316';
      return '#10b981';
    } else if (type === 'savings') {
      if (ratio >= 0.25) return '#10b981';
      if (ratio >= 0.15) return '#f97316';
      return '#ef4444';
    } else if (type === 'emi') {
      if (ratio > 0.4) return '#ef4444';
      if (ratio > 0.3) return '#f97316';
      return '#10b981';
    }
  };

  return (
    <div className="ratios-dashboard-container">
      <h2 className="section-title">📊 Financial Ratios</h2>
      
      <div className="ratios-grid">
        <div className="ratio-card">
          <div className="ratio-header">
            <span className="ratio-label">Expense Ratio</span>
            <span className="ratio-value" style={{ color: getRatioColor(animatedRatios.expense_ratio, 'expense') }}>
              {(animatedRatios.expense_ratio * 100).toFixed(1)}%
            </span>
          </div>
          <div className="ratio-bar-container">
            <div 
              className="ratio-bar" 
              style={{ 
                width: `${animatedRatios.expense_ratio * 100}%`,
                backgroundColor: getRatioColor(animatedRatios.expense_ratio, 'expense')
              }}
            />
          </div>
          <p className="ratio-description">
            {animatedRatios.expense_ratio > 0.8 ? '⚠️ Very high expenses' : 
             animatedRatios.expense_ratio > 0.7 ? '⚡ Moderate expenses' : 
             '✅ Good expense control'}
          </p>
        </div>

        <div className="ratio-card">
          <div className="ratio-header">
            <span className="ratio-label">Savings Ratio</span>
            <span className="ratio-value" style={{ color: getRatioColor(animatedRatios.savings_ratio, 'savings') }}>
              {(animatedRatios.savings_ratio * 100).toFixed(1)}%
            </span>
          </div>
          <div className="ratio-bar-container">
            <div 
              className="ratio-bar" 
              style={{ 
                width: `${animatedRatios.savings_ratio * 100}%`,
                backgroundColor: getRatioColor(animatedRatios.savings_ratio, 'savings')
              }}
            />
          </div>
          <p className="ratio-description">
            {animatedRatios.savings_ratio >= 0.25 ? '🎯 Excellent savings!' : 
             animatedRatios.savings_ratio >= 0.15 ? '👍 Good savings' : 
             '📉 Low savings rate'}
          </p>
        </div>

        <div className="ratio-card">
          <div className="ratio-header">
            <span className="ratio-label">EMI Burden</span>
            <span className="ratio-value" style={{ color: getRatioColor(animatedRatios.emi_ratio, 'emi') }}>
              {(animatedRatios.emi_ratio * 100).toFixed(1)}%
            </span>
          </div>
          <div className="ratio-bar-container">
            <div 
              className="ratio-bar" 
              style={{ 
                width: `${animatedRatios.emi_ratio * 100}%`,
                backgroundColor: getRatioColor(animatedRatios.emi_ratio, 'emi')
              }}
            />
          </div>
          <p className="ratio-description">
            {animatedRatios.emi_ratio > 0.4 ? '🚨 EMI too high' : 
             animatedRatios.emi_ratio > 0.3 ? '⚠️ Watch EMI level' : 
             '✅ EMI under control'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default RatiosDashboard;

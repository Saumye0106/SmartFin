import { useEffect, useState } from 'react';
import './ScoreDisplay.css';

const ScoreDisplay = ({ score, classification }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    if (score) {
      let current = 0;
      const increment = score / 50;
      const timer = setInterval(() => {
        current += increment;
        if (current >= score) {
          setAnimatedScore(score);
          clearInterval(timer);
        } else {
          setAnimatedScore(Math.round(current));
        }
      }, 20);

      return () => clearInterval(timer);
    }
  }, [score]);

  if (!score || !classification) return null;

  const getScoreColor = (score) => {
    if (score >= 80) return '#00ff88';
    if (score >= 60) return '#ffb800';
    return '#ff3366';
  };

  const scoreColor = getScoreColor(animatedScore);
  const circumference = 2 * Math.PI * 85;
  const progress = (animatedScore / 100) * circumference;

  return (
    <div className="score-display-container">
      <div className="score-header">
        <div className="score-label-text">FINANCIAL HEALTH SCORE</div>
        <div className="score-bracket">[LIVE]</div>
      </div>
      
      <div className="score-main">
        <div className="score-visual">
          <svg className="score-circle" viewBox="0 0 200 200">
            {/* Grid pattern */}
            <defs>
              <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(48, 54, 61, 0.3)" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <circle cx="100" cy="100" r="95" fill="url(#grid)" />
            
            {/* Background track */}
            <circle
              cx="100"
              cy="100"
              r="85"
              fill="none"
              stroke="rgba(48, 54, 61, 0.5)"
              strokeWidth="8"
            />
            
            {/* Progress circle */}
            <circle
              cx="100"
              cy="100"
              r="85"
              fill="none"
              stroke={scoreColor}
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={circumference - progress}
              strokeLinecap="round"
              transform="rotate(-90 100 100)"
              className="score-progress"
              style={{ filter: `drop-shadow(0 0 8px ${scoreColor})` }}
            />
          </svg>
          
          <div className="score-content">
            <div className="score-value" style={{ color: scoreColor, textShadow: `0 0 20px ${scoreColor}80` }}>
              {animatedScore}
            </div>
            <div className="score-max">/100</div>
          </div>
        </div>

        <div className="score-details">
          <div className="score-status">
            <div className="status-badge" style={{ 
              borderColor: scoreColor,
              backgroundColor: `${scoreColor}15`
            }}>
              <span className="status-icon">●</span>
              <span className="status-label">{classification.category || 'ANALYZING'}</span>
            </div>
          </div>

          <div className="score-metrics">
            <div className="metric-row">
              <span className="metric-label">STATUS</span>
              <span className="metric-value" style={{ color: scoreColor }}>
                {classification.description || 'Processing data...'}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">TREND</span>
              <span className="metric-value text-green">↗ IMPROVING</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">LAST UPDATED</span>
              <span className="metric-value">{new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="score-indicator-bar">
        <div className="indicator-segment bad">
          <span className="indicator-label">0-40</span>
          <span className="indicator-text">CRITICAL</span>
        </div>
        <div className="indicator-segment poor">
          <span className="indicator-label">40-60</span>
          <span className="indicator-text">NEEDS WORK</span>
        </div>
        <div className="indicator-segment fair">
          <span className="indicator-label">60-80</span>
          <span className="indicator-text">STABLE</span>
        </div>
        <div className="indicator-segment good">
          <span className="indicator-label">80-100</span>
          <span className="indicator-text">EXCELLENT</span>
        </div>
        <div 
          className="indicator-pointer" 
          style={{ 
            left: `${animatedScore}%`,
            borderTopColor: scoreColor 
          }}
        />
      </div>
    </div>
  );
};

export default ScoreDisplay;

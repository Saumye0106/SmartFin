import { useEffect, useState } from 'react';
import './ScoreDisplay.css';

const ScoreDisplay = ({ score, classification }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    if (score) {
      let current = 0;
      const increment = score / 50; // 50 frames
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

  const circumference = 2 * Math.PI * 90;
  const progress = (animatedScore / 100) * circumference;

  return (
    <div className="score-display-container">
      <h2 className="section-title">Your Financial Health Score</h2>
      
      <div className="score-circle-wrapper">
        <svg className="score-circle" viewBox="0 0 200 200">
          {/* Background circle */}
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="12"
          />
          {/* Progress circle */}
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke={classification.color}
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            transform="rotate(-90 100 100)"
            className="score-progress"
          />
        </svg>
        
        <div className="score-content">
          <div className="score-number" style={{ color: classification.color }}>
            {animatedScore}
          </div>
          <div className="score-label">/ 100</div>
        </div>
      </div>

      <div className="classification-badge" style={{ backgroundColor: `${classification.color}20`, color: classification.color }}>
        <span className="classification-emoji">{classification.emoji}</span>
        <span className="classification-text">{classification.category}</span>
      </div>

      <p className="classification-description">{classification.description}</p>
    </div>
  );
};

export default ScoreDisplay;

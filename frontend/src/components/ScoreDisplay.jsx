import { useEffect, useState } from 'react';

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

  const circumference = 2 * Math.PI * 90;
  const progress = (animatedScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:chart-2-linear" className="text-cyan-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Financial Health Score</h2>
          <p className="text-xs text-white/50">AI-powered assessment of your financial wellness</p>
        </div>
      </div>
      
      <div className="relative w-64 h-64 mb-8">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 200 200">
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke="rgba(255, 255, 255, 0.05)"
            strokeWidth="12"
          />
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
            className="transition-all duration-1000 ease-out"
            style={{ filter: `drop-shadow(0 0 8px ${classification.color}40)` }}
          />
        </svg>
        
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-6xl font-bold font-display tracking-tight" style={{ color: classification.color }}>
            {animatedScore}
          </div>
          <div className="text-white/40 text-sm font-mono">/ 100</div>
        </div>
      </div>

      <div 
        className="inline-flex items-center gap-3 px-6 py-3 rounded-full border backdrop-blur-sm mb-4"
        style={{ 
          backgroundColor: `${classification.color}10`,
          borderColor: `${classification.color}30`,
          color: classification.color 
        }}
      >
        <span className="text-2xl">{classification.emoji}</span>
        <span className="font-semibold text-lg">{classification.category}</span>
      </div>

      <p className="text-center text-white/60 max-w-md text-sm leading-relaxed">
        {classification.description}
      </p>
    </div>
  );
};

export default ScoreDisplay;

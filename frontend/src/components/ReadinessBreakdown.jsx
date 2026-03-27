import { useState } from 'react';

const ReadinessBreakdown = ({ factors }) => {
  const factorWeights = {
    'Financial Health': 0.30,
    'Savings Adequacy': 0.25,
    'Savings Rate': 0.20,
    'Debt Burden': 0.15,
    'Time Horizon': 0.10
  };

  const getFactorColor = (score) => {
    if (score < 20) return 'bg-red-500';
    if (score < 40) return 'bg-orange-500';
    if (score < 60) return 'bg-yellow-500';
    if (score < 80) return 'bg-lime-500';
    return 'bg-green-500';
  };

  const getFactorLabel = (score) => {
    if (score < 20) return 'Critical';
    if (score < 40) return 'Poor';
    if (score < 60) return 'Fair';
    if (score < 80) return 'Good';
    return 'Excellent';
  };

  const totalScore = Object.entries(factors).reduce((sum, [name, score]) => {
    return sum + score * factorWeights[name];
  }, 0);

  return (
    <div className="space-y-6">
      {/* Pie Chart Representation */}
      <div className="flex justify-center">
        <svg width="200" height="200" viewBox="0 0 200 200">
          {/* Background circle */}
          <circle cx="100" cy="100" r="80" fill="none" stroke="#e5e7eb" strokeWidth="20" />

          {/* Pie segments */}
          {Object.entries(factors).map(([name, score], index) => {
            const weight = factorWeights[name];
            const startAngle = Object.entries(factors)
              .slice(0, index)
              .reduce((sum, [n]) => sum + factorWeights[n], 0) * 2 * Math.PI;
            const endAngle = startAngle + weight * 2 * Math.PI;

            const startX = 100 + 80 * Math.cos(startAngle - Math.PI / 2);
            const startY = 100 + 80 * Math.sin(startAngle - Math.PI / 2);
            const endX = 100 + 80 * Math.cos(endAngle - Math.PI / 2);
            const endY = 100 + 80 * Math.sin(endAngle - Math.PI / 2);

            const largeArc = weight > 0.5 ? 1 : 0;

            const colors = {
              'Financial Health': '#3b82f6',
              'Savings Adequacy': '#8b5cf6',
              'Savings Rate': '#ec4899',
              'Debt Burden': '#f59e0b',
              'Time Horizon': '#10b981'
            };

            return (
              <path
                key={name}
                d={`M 100 100 L ${startX} ${startY} A 80 80 0 ${largeArc} 1 ${endX} ${endY} Z`}
                fill={colors[name]}
                opacity="0.8"
              />
            );
          })}

          {/* Center circle */}
          <circle cx="100" cy="100" r="50" fill="#0a0a0a" />
          <text x="100" y="95" textAnchor="middle" fontSize="24" fontWeight="bold" fill="#ffffff">
            {totalScore.toFixed(0)}
          </text>
          <text x="100" y="115" textAnchor="middle" fontSize="12" fill="#ffffff80">
            Overall
          </text>
        </svg>
      </div>

      {/* Factor Details */}
      <div className="space-y-3">
        {Object.entries(factors).map(([name, score]) => {
          const weight = factorWeights[name];
          const contribution = score * weight;
          const color = getFactorColor(score);
          const label = getFactorLabel(score);

          const colors = {
            'Financial Health': '#3b82f6',
            'Savings Adequacy': '#8b5cf6',
            'Savings Rate': '#ec4899',
            'Debt Burden': '#f59e0b',
            'Time Horizon': '#10b981'
          };

          return (
            <div key={name} className="border border-white/10 rounded-lg p-4 bg-white/5">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold text-white">{name}</h4>
                  <p className="text-xs text-white/50">Weight: {(weight * 100).toFixed(0)}%</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold" style={{ color: colors[name] }}>
                    {score.toFixed(1)}
                  </p>
                  <p className="text-xs text-white/50">{label}</p>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden mb-2">
                <div
                  className={`h-full transition-all duration-500 ${color}`}
                  style={{ width: `${Math.min(score, 100)}%` }}
                ></div>
              </div>

              {/* Contribution */}
              <p className="text-xs text-white/50">
                Contribution to overall score: <span className="font-semibold">{contribution.toFixed(2)}</span>
              </p>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="bg-white/5 rounded-lg p-4 border border-white/10">
        <h4 className="font-semibold text-white mb-3">Score Interpretation</h4>
        <div className="grid grid-cols-5 gap-2 text-xs">
          <div className="text-center">
            <div className="w-3 h-3 bg-red-500 rounded mx-auto mb-1"></div>
            <span className="text-white/50">0-20: Critical</span>
          </div>
          <div className="text-center">
            <div className="w-3 h-3 bg-orange-500 rounded mx-auto mb-1"></div>
            <span className="text-white/50">20-40: Poor</span>
          </div>
          <div className="text-center">
            <div className="w-3 h-3 bg-yellow-500 rounded mx-auto mb-1"></div>
            <span className="text-white/50">40-60: Fair</span>
          </div>
          <div className="text-center">
            <div className="w-3 h-3 bg-lime-500 rounded mx-auto mb-1"></div>
            <span className="text-white/50">60-80: Good</span>
          </div>
          <div className="text-center">
            <div className="w-3 h-3 bg-green-500 rounded mx-auto mb-1"></div>
            <span className="text-white/50">80-100: Excellent</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReadinessBreakdown;

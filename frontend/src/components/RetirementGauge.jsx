import { useState } from 'react';

const RetirementGauge = ({ score }) => {
  const getColor = (score) => {
    if (score < 20) return '#ef4444'; // red
    if (score < 40) return '#f97316'; // orange
    if (score < 60) return '#eab308'; // yellow
    if (score < 80) return '#84cc16'; // light green
    return '#22c55e'; // dark green
  };

  const getLabel = (score) => {
    if (score < 20) return 'Critical';
    if (score < 40) return 'Poor';
    if (score < 60) return 'Fair';
    if (score < 80) return 'Good';
    return 'Excellent';
  };

  const color = getColor(score);
  const label = getLabel(score);
  const rotation = (score / 100) * 180 - 90;

  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className="relative w-48 h-24">
        {/* Gauge background */}
        <svg className="w-full h-full" viewBox="0 0 200 100">
          {/* Red section */}
          <path
            d="M 20 80 A 60 60 0 0 1 40 25"
            fill="none"
            stroke="#fee2e2"
            strokeWidth="12"
          />
          {/* Orange section */}
          <path
            d="M 40 25 A 60 60 0 0 1 80 10"
            fill="none"
            stroke="#fed7aa"
            strokeWidth="12"
          />
          {/* Yellow section */}
          <path
            d="M 80 10 A 60 60 0 0 1 120 10"
            fill="none"
            stroke="#fef08a"
            strokeWidth="12"
          />
          {/* Light green section */}
          <path
            d="M 120 10 A 60 60 0 0 1 160 25"
            fill="none"
            stroke="#dcfce7"
            strokeWidth="12"
          />
          {/* Dark green section */}
          <path
            d="M 160 25 A 60 60 0 0 1 180 80"
            fill="none"
            stroke="#bbf7d0"
            strokeWidth="12"
          />

          {/* Needle */}
          <g transform={`translate(100, 80) rotate(${rotation})`}>
            <line
              x1="0"
              y1="0"
              x2="0"
              y2="-50"
              stroke={color}
              strokeWidth="3"
              strokeLinecap="round"
            />
            <circle cx="0" cy="0" r="5" fill={color} />
          </g>

          {/* Center circle */}
          <circle cx="100" cy="80" r="8" fill="white" stroke={color} strokeWidth="2" />
        </svg>
      </div>

      {/* Score display */}
      <div className="text-center mt-4">
        <div className="text-4xl font-bold" style={{ color }}>
          {score.toFixed(1)}
        </div>
        <div className="text-lg font-semibold text-white/70 mt-1">{label}</div>
      </div>

      {/* Legend */}
      <div className="mt-6 grid grid-cols-5 gap-2 text-xs">
        <div className="text-center">
          <div className="w-4 h-4 bg-red-500 rounded mx-auto mb-1"></div>
          <span className="text-white/50">0-20</span>
        </div>
        <div className="text-center">
          <div className="w-4 h-4 bg-orange-500 rounded mx-auto mb-1"></div>
          <span className="text-white/50">20-40</span>
        </div>
        <div className="text-center">
          <div className="w-4 h-4 bg-yellow-500 rounded mx-auto mb-1"></div>
          <span className="text-white/50">40-60</span>
        </div>
        <div className="text-center">
          <div className="w-4 h-4 bg-lime-500 rounded mx-auto mb-1"></div>
          <span className="text-white/50">60-80</span>
        </div>
        <div className="text-center">
          <div className="w-4 h-4 bg-green-500 rounded mx-auto mb-1"></div>
          <span className="text-white/50">80-100</span>
        </div>
      </div>
    </div>
  );
};

export default RetirementGauge;

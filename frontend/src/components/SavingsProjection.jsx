import { useState } from 'react';

const SavingsProjection = ({ currentSavings, monthlySavings, yearsToRetirement, returnRate }) => {
  // Calculate savings projection year by year
  const projections = [];
  let balance = currentSavings;

  for (let year = 0; year <= yearsToRetirement; year++) {
    projections.push({
      year,
      balance: Math.round(balance)
    });

    // Calculate next year's balance
    const annualSavings = monthlySavings * 12;
    balance = balance * (1 + returnRate) + annualSavings;
  }

  const maxBalance = Math.max(...projections.map(p => p.balance));
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Create chart data
  const chartHeight = 200;
  const chartWidth = Math.max(400, projections.length * 30);

  return (
    <div className="space-y-6">
      {/* Line Chart */}
      <div className="overflow-x-auto">
        <svg width={chartWidth} height={chartHeight + 40} className="mx-auto">
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
            <line
              key={`grid-${i}`}
              x1="40"
              y1={chartHeight - chartHeight * ratio}
              x2={chartWidth - 20}
              y2={chartHeight - chartHeight * ratio}
              stroke="#ffffff20"
              strokeWidth="1"
              strokeDasharray="4"
            />
          ))}

          {/* Y-axis */}
          <line x1="40" y1="0" x2="40" y2={chartHeight} stroke="#ffffff40" strokeWidth="2" />

          {/* X-axis */}
          <line x1="40" y1={chartHeight} x2={chartWidth - 20} y2={chartHeight} stroke="#ffffff40" strokeWidth="2" />

          {/* Y-axis labels */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
            <text
              key={`y-label-${i}`}
              x="35"
              y={chartHeight - chartHeight * ratio + 5}
              textAnchor="end"
              fontSize="12"
              fill="#ffffff80"
            >
              {formatCurrency(maxBalance * ratio)}
            </text>
          ))}

          {/* Line path */}
          <polyline
            points={projections
              .map((p, i) => {
                const x = 40 + (i / projections.length) * (chartWidth - 60);
                const y = chartHeight - (p.balance / maxBalance) * chartHeight;
                return `${x},${y}`;
              })
              .join(' ')}
            fill="none"
            stroke="#a78bfa"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data points */}
          {projections.map((p, i) => (
            <circle
              key={`point-${i}`}
              cx={40 + (i / projections.length) * (chartWidth - 60)}
              cy={chartHeight - (p.balance / maxBalance) * chartHeight}
              r="4"
              fill="#a78bfa"
            />
          ))}

          {/* X-axis labels */}
          {projections
            .filter((_, i) => i % Math.ceil(projections.length / 10) === 0 || i === projections.length - 1)
            .map((p, i) => (
              <text
                key={`x-label-${i}`}
                x={40 + (p.year / yearsToRetirement) * (chartWidth - 60)}
                y={chartHeight + 20}
                textAnchor="middle"
                fontSize="12"
                fill="#ffffff80"
              >
                Year {p.year}
              </text>
            ))}
        </svg>
      </div>

      {/* Key Milestones */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
          <p className="text-white/50 text-sm mb-1">Current Savings</p>
          <p className="text-2xl font-bold text-blue-400">{formatCurrency(currentSavings)}</p>
        </div>

        <div className="bg-purple-500/10 rounded-lg p-4 border border-purple-500/20">
          <p className="text-white/50 text-sm mb-1">Monthly Contribution</p>
          <p className="text-2xl font-bold text-purple-400">{formatCurrency(monthlySavings)}</p>
        </div>

        <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/20">
          <p className="text-white/50 text-sm mb-1">Projected at Retirement</p>
          <p className="text-2xl font-bold text-green-400">
            {formatCurrency(projections[projections.length - 1].balance)}
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-white/5 rounded-lg p-4 border border-white/10">
        <h4 className="font-semibold text-white mb-3">Projection Summary</h4>
        <div className="space-y-2 text-sm">
          <p className="text-white/70">
            <span className="font-medium">Starting Amount:</span> {formatCurrency(currentSavings)}
          </p>
          <p className="text-white/70">
            <span className="font-medium">Monthly Savings:</span> {formatCurrency(monthlySavings)}
          </p>
          <p className="text-white/70">
            <span className="font-medium">Annual Return Rate:</span> {(returnRate * 100).toFixed(1)}%
          </p>
          <p className="text-white/70">
            <span className="font-medium">Time Horizon:</span> {yearsToRetirement} years
          </p>
          <p className="text-white/70 mt-3 pt-3 border-t border-white/10">
            <span className="font-medium">Total Contributions:</span> {formatCurrency(monthlySavings * 12 * yearsToRetirement)}
          </p>
          <p className="text-white/70">
            <span className="font-medium">Investment Growth:</span>{' '}
            {formatCurrency(projections[projections.length - 1].balance - currentSavings - monthlySavings * 12 * yearsToRetirement)}
          </p>
        </div>
      </div>
    </div>
  );
};

export default SavingsProjection;

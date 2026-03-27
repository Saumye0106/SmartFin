import { useState } from 'react';

const CorpusComparison = ({ target, projected }) => {
  const maxValue = Math.max(target, projected) * 1.1;
  const targetPercent = (target / maxValue) * 100;
  const projectedPercent = (projected / maxValue) * 100;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const gap = target - projected;
  const gapPercent = (gap / target) * 100;

  return (
    <div className="space-y-6">
      {/* Bar Chart */}
      <div className="space-y-4">
        {/* Target Bar */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="font-semibold text-white">Retirement Corpus Target</span>
            <span className="text-lg font-bold text-blue-400">{formatCurrency(target)}</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-8 overflow-hidden">
            <div
              className="bg-blue-500 h-full flex items-center justify-end pr-3 transition-all duration-500"
              style={{ width: '100%' }}
            >
              <span className="text-white text-sm font-semibold">100%</span>
            </div>
          </div>
        </div>

        {/* Projected Bar */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="font-semibold text-white">Projected Savings</span>
            <span className={`text-lg font-bold ${projected >= target ? 'text-green-400' : 'text-orange-400'}`}>
              {formatCurrency(projected)}
            </span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-8 overflow-hidden">
            <div
              className={`h-full flex items-center justify-end pr-3 transition-all duration-500 ${
                projected >= target ? 'bg-green-500' : 'bg-orange-500'
              }`}
              style={{ width: `${projectedPercent}%` }}
            >
              {projectedPercent > 10 && (
                <span className="text-white text-sm font-semibold">{projectedPercent.toFixed(0)}%</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
          <p className="text-white/50 text-sm mb-1">Target Corpus</p>
          <p className="text-2xl font-bold text-blue-400">{formatCurrency(target)}</p>
        </div>

        <div className={`rounded-lg p-4 border ${projected >= target ? 'bg-green-500/10 border-green-500/20' : 'bg-orange-500/10 border-orange-500/20'}`}>
          <p className="text-white/50 text-sm mb-1">Projected Savings</p>
          <p className={`text-2xl font-bold ${projected >= target ? 'text-green-400' : 'text-orange-400'}`}>
            {formatCurrency(projected)}
          </p>
        </div>

        <div className={`rounded-lg p-4 border ${gap < 0 ? 'bg-green-500/10 border-green-500/20' : 'bg-danger-500/10 border-danger-500/20'}`}>
          <p className="text-white/50 text-sm mb-1">Gap/Surplus</p>
          <p className={`text-2xl font-bold ${gap < 0 ? 'text-green-400' : 'text-danger-400'}`}>
            {formatCurrency(Math.abs(gap))}
          </p>
        </div>
      </div>

      {/* Status Message */}
      <div className={`rounded-lg p-4 border ${gap < 0 ? 'bg-green-500/10 border-green-500/20' : 'bg-orange-500/10 border-orange-500/20'}`}>
        {gap < 0 ? (
          <p className="text-green-400">
            <span className="font-semibold">Great news!</span> Your projected savings exceed your retirement corpus target by{' '}
            <span className="font-bold">{formatCurrency(Math.abs(gap))}</span>. You're on track for a comfortable retirement.
          </p>
        ) : (
          <p className="text-orange-400">
            <span className="font-semibold">Action needed:</span> There's a gap of{' '}
            <span className="font-bold">{formatCurrency(gap)}</span> ({gapPercent.toFixed(1)}%) between your target and projected savings.
            Consider increasing your monthly savings or adjusting your retirement timeline.
          </p>
        )}
      </div>
    </div>
  );
};

export default CorpusComparison;

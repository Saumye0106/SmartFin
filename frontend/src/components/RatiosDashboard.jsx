import { useEffect, useState } from 'react';

const RatiosDashboard = ({ patterns }) => {
  const [animatedRatios, setAnimatedRatios] = useState({
    expense_ratio: 0,
    savings_ratio: 0,
    emi_ratio: 0
  });

  useEffect(() => {
    if (patterns) {
      const duration = 1000;
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

  const getRatioStatus = (ratio, type) => {
    if (type === 'expense') {
      if (ratio > 0.8) return { icon: 'solar:danger-triangle-linear', text: 'Very high expenses' };
      if (ratio > 0.7) return { icon: 'solar:bolt-circle-linear', text: 'Moderate expenses' };
      return { icon: 'solar:check-circle-linear', text: 'Good expense control' };
    } else if (type === 'savings') {
      if (ratio >= 0.25) return { icon: 'solar:star-linear', text: 'Excellent savings!' };
      if (ratio >= 0.15) return { icon: 'solar:thumbs-up-linear', text: 'Good savings' };
      return { icon: 'solar:graph-down-linear', text: 'Low savings rate' };
    } else if (type === 'emi') {
      if (ratio > 0.4) return { icon: 'solar:danger-circle-linear', text: 'EMI too high' };
      if (ratio > 0.3) return { icon: 'solar:eye-linear', text: 'Watch EMI level' };
      return { icon: 'solar:shield-check-linear', text: 'EMI under control' };
    }
  };

  const ratios = [
    { 
      key: 'expense_ratio', 
      label: 'Expense Ratio', 
      value: animatedRatios.expense_ratio,
      type: 'expense',
      icon: 'solar:wallet-money-linear'
    },
    { 
      key: 'savings_ratio', 
      label: 'Savings Ratio', 
      value: animatedRatios.savings_ratio,
      type: 'savings',
      icon: 'solar:safe-square-linear'
    },
    { 
      key: 'emi_ratio', 
      label: 'EMI Burden', 
      value: animatedRatios.emi_ratio,
      type: 'emi',
      icon: 'solar:card-linear'
    }
  ];

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:graph-up-linear" className="text-blue-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Financial Ratios</h2>
          <p className="text-xs text-white/50">Key metrics for financial health</p>
        </div>
      </div>
      
      <div className="space-y-6">
        {ratios.map((ratio) => {
          const color = getRatioColor(ratio.value, ratio.type);
          const status = getRatioStatus(ratio.value, ratio.type);
          
          return (
            <div key={ratio.key} className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <iconify-icon icon={ratio.icon} className="text-white/60" width="18"></iconify-icon>
                  <span className="text-sm text-white/80">{ratio.label}</span>
                </div>
                <span className="text-lg font-bold font-mono" style={{ color }}>
                  {(ratio.value * 100).toFixed(1)}%
                </span>
              </div>
              
              <div className="relative h-2 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className="absolute inset-y-0 left-0 rounded-full transition-all duration-1000 ease-out"
                  style={{ 
                    width: `${ratio.value * 100}%`,
                    backgroundColor: color,
                    boxShadow: `0 0 10px ${color}40`
                  }}
                />
              </div>
              
              <div className="flex items-center gap-2 text-xs" style={{ color }}>
                <iconify-icon icon={status.icon} width="14"></iconify-icon>
                <span>{status.text}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RatiosDashboard;

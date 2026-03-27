const FinancialHealthIntegration = ({ plan }) => {
  const factors = [
    { name: 'Savings Rate', current: plan.savings_rate_factor, weight: 0.20 },
    { name: 'Debt Burden', current: plan.debt_burden_factor, weight: 0.15 },
    { name: 'Savings Adequacy', current: plan.savings_adequacy_factor, weight: 0.25 },
    { name: 'Financial Health', current: plan.financial_health_factor, weight: 0.30 },
    { name: 'Time Horizon', current: plan.time_horizon_factor, weight: 0.10 }
  ];

  const getFactorColor = (score) => {
    if (score < 20) return 'text-danger-400';
    if (score < 40) return 'text-orange-400';
    if (score < 60) return 'text-yellow-400';
    if (score < 80) return 'text-lime-400';
    return 'text-green-400';
  };

  const getFactorBgColor = (score) => {
    if (score < 20) return 'bg-danger-500/10 border-danger-500/20';
    if (score < 40) return 'bg-orange-500/10 border-orange-500/20';
    if (score < 60) return 'bg-yellow-500/10 border-yellow-500/20';
    if (score < 80) return 'bg-lime-500/10 border-lime-500/20';
    return 'bg-green-500/10 border-green-500/20';
  };

  const projectedScore = Math.min(100, plan.readiness_score + 15);

  return (
    <div className="space-y-6">
      {/* Current vs Projected */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel rounded-xl p-6 border border-blue-500/20 bg-blue-500/5">
          <h3 className="text-lg font-semibold text-white mb-4">Current Financial Health</h3>
          <div className="text-center">
            <p className="text-5xl font-bold text-blue-400 mb-2">{plan.financial_health_factor.toFixed(0)}</p>
            <p className="text-white/50">Overall Score</p>
          </div>
        </div>

        <div className="glass-panel rounded-xl p-6 border border-green-500/20 bg-green-500/5">
          <h3 className="text-lg font-semibold text-white mb-4">Projected Financial Health</h3>
          <div className="text-center">
            <p className="text-5xl font-bold text-green-400 mb-2">{projectedScore.toFixed(0)}</p>
            <p className="text-white/50">After Implementing Recommendations</p>
          </div>
        </div>
      </div>

      {/* Factor Breakdown */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Financial Health Factors</h3>
        <div className="space-y-4">
          {factors.map((factor) => (
            <div key={factor.name} className={`rounded-lg p-4 border glass-panel ${getFactorBgColor(factor.current)}`}>
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-semibold text-white">{factor.name}</h4>
                  <p className="text-xs text-white/50">Weight: {(factor.weight * 100).toFixed(0)}%</p>
                </div>
                <p className={`text-2xl font-bold ${getFactorColor(factor.current)}`}>
                  {factor.current.toFixed(0)}
                </p>
              </div>

              <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden mb-3">
                <div
                  className={`h-full transition-all duration-500 ${
                    factor.current < 20 ? 'bg-danger-500' :
                    factor.current < 40 ? 'bg-orange-500' :
                    factor.current < 60 ? 'bg-yellow-500' :
                    factor.current < 80 ? 'bg-lime-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(factor.current, 100)}%` }}
                ></div>
              </div>

              <p className="text-sm text-white/70">
                {factor.name === 'Savings Rate' && 'Increase your monthly savings to improve this factor.'}
                {factor.name === 'Debt Burden' && 'Focus on paying off high-interest debt.'}
                {factor.name === 'Savings Adequacy' && 'Your savings are on track. Continue with your current plan.'}
                {factor.name === 'Financial Health' && 'Maintain your financial health momentum.'}
                {factor.name === 'Time Horizon' && 'Use your time horizon wisely to build wealth.'}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Impact on Retirement */}
      <div className="glass-panel rounded-xl p-6 border border-purple-500/20 bg-purple-500/5">
        <h3 className="text-lg font-semibold text-white mb-3">Impact on Retirement Readiness</h3>
        <p className="text-white/70 mb-4">
          Your financial health score directly impacts your retirement readiness. By improving your financial health factors, you can increase your retirement readiness score by up to 15 points.
        </p>
        <div className="bg-white/5 rounded-lg p-4 border border-white/10">
          <div className="flex justify-between items-center mb-2">
            <span className="text-white/70">Current Readiness Score</span>
            <span className="font-bold text-purple-400">{plan.readiness_score.toFixed(1)}</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2 mb-4">
            <div
              className="bg-purple-500 h-full rounded-full"
              style={{ width: `${Math.min(plan.readiness_score, 100)}%` }}
            ></div>
          </div>

          <div className="flex justify-between items-center mb-2">
            <span className="text-white/70">Potential Score</span>
            <span className="font-bold text-green-400">{projectedScore.toFixed(1)}</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2">
            <div
              className="bg-green-500 h-full rounded-full"
              style={{ width: `${Math.min(projectedScore, 100)}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinancialHealthIntegration;

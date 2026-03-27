const GapAnalysisView = ({ plan }) => {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const improvementPaths = [
    {
      action: 'Increase Monthly Savings',
      description: 'Boost your monthly savings amount',
      impact: Math.min(plan.gap * 0.4, 50),
      timeline: 'Immediate',
      difficulty: 'Easy'
    },
    {
      action: 'Improve Investment Returns',
      description: 'Optimize your investment portfolio',
      impact: Math.min(plan.gap * 0.3, 40),
      timeline: 'Medium-term',
      difficulty: 'Medium'
    },
    {
      action: 'Delay Retirement',
      description: 'Work a few more years',
      impact: Math.min(plan.gap * 0.5, 60),
      timeline: 'Long-term',
      difficulty: 'Hard'
    },
    {
      action: 'Reduce Expenses',
      description: 'Lower your retirement lifestyle',
      impact: Math.min(plan.gap * 0.2, 30),
      timeline: 'Immediate',
      difficulty: 'Medium'
    }
  ];

  const isShortfall = plan.gap > 0;
  const gapPercent = (plan.gap / plan.retirement_corpus) * 100;

  return (
    <div className="space-y-6">
      {/* Gap Summary */}
      <div className={`rounded-xl p-6 border glass-panel ${isShortfall ? 'bg-danger-500/5 border-danger-500/20' : 'bg-green-500/5 border-green-500/20'}`}>
        <h3 className="text-lg font-semibold mb-4 text-white">
          {isShortfall ? '⚠️ Retirement Savings Gap' : '✅ Retirement Surplus'}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <p className="text-white/50 text-sm mb-1">Target Corpus</p>
            <p className="text-2xl font-bold text-white">{formatCurrency(plan.retirement_corpus)}</p>
          </div>

          <div>
            <p className="text-white/50 text-sm mb-1">Projected Savings</p>
            <p className="text-2xl font-bold text-white">{formatCurrency(plan.projected_savings)}</p>
          </div>

          <div>
            <p className={`text-sm mb-1 ${isShortfall ? 'text-danger-400' : 'text-green-400'}`}>
              {isShortfall ? 'Shortfall' : 'Surplus'}
            </p>
            <p className={`text-2xl font-bold ${isShortfall ? 'text-danger-400' : 'text-green-400'}`}>
              {formatCurrency(Math.abs(plan.gap))}
            </p>
          </div>
        </div>

        {isShortfall && (
          <div className="text-sm text-danger-400">
            <p>
              You have a shortfall of <span className="font-bold">{gapPercent.toFixed(1)}%</span> of your retirement corpus target.
              Consider implementing one or more of the improvement strategies below.
            </p>
          </div>
        )}
      </div>

      {/* Improvement Paths */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Improvement Paths</h3>
        <div className="space-y-4">
          {improvementPaths.map((path, index) => (
            <div key={index} className="border border-white/10 rounded-lg p-4 hover:border-purple-500/30 transition bg-white/5">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-semibold text-white">{path.action}</h4>
                  <p className="text-sm text-white/50">{path.description}</p>
                </div>
                <div className="text-right">
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${
                    path.difficulty === 'Easy' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                    path.difficulty === 'Medium' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                    'bg-danger-500/10 text-danger-400 border-danger-500/20'
                  }`}>
                    {path.difficulty}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <p className="text-xs text-white/50 mb-1">Estimated Impact</p>
                  <p className="text-lg font-bold text-purple-400">{path.impact.toFixed(0)}%</p>
                </div>
                <div>
                  <p className="text-xs text-white/50 mb-1">Timeline</p>
                  <p className="text-sm font-semibold text-white">{path.timeline}</p>
                </div>
              </div>

              <div className="w-full bg-white/10 rounded-full h-2">
                <div
                  className="bg-purple-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(path.impact, 100)}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Most Impactful Action */}
      <div className="glass-panel rounded-xl p-6 border border-purple-500/20 bg-purple-500/5">
        <h3 className="text-lg font-semibold text-white mb-3">🎯 Most Impactful Action</h3>
        <p className="text-white/70 mb-4">
          Based on your situation, <span className="font-bold">increasing your monthly savings</span> would have the most immediate impact on closing your retirement gap.
        </p>
        <div className="bg-white/5 rounded-lg p-4 border border-white/10">
          <p className="text-sm text-white/50 mb-2">Current Monthly Savings Required:</p>
          <p className="text-2xl font-bold text-purple-400">{formatCurrency(plan.required_monthly_savings)}</p>
          <p className="text-sm text-white/50 mt-3">
            Increasing this by 20% would reduce your gap by approximately {(improvementPaths[0].impact * 0.2).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Action Plan */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Recommended Action Plan</h3>
        <div className="space-y-3">
          {[
            { num: 1, title: 'Review Your Budget', desc: 'Identify areas where you can increase savings' },
            { num: 2, title: 'Optimize Investments', desc: 'Ensure your portfolio is aligned with your risk tolerance' },
            { num: 3, title: 'Monitor Progress', desc: 'Review your plan quarterly and adjust as needed' },
            { num: 4, title: 'Seek Professional Advice', desc: 'Consider consulting a financial advisor for personalized guidance' }
          ].map(item => (
            <div key={item.num} className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-purple-500/20 text-purple-400 rounded-full flex items-center justify-center font-bold border border-purple-500/30">{item.num}</div>
              <div>
                <p className="font-semibold text-white">{item.title}</p>
                <p className="text-sm text-white/50">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default GapAnalysisView;

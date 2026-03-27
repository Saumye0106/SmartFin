const ActionPlanView = ({ recommendations, plan }) => {
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 1:
        return 'bg-danger-500/10 text-danger-400 border-danger-500/20';
      case 2:
        return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 3:
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
      default:
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
    }
  };

  const getTimelineIcon = (timeline) => {
    switch (timeline) {
      case 'immediate':
        return '⚡';
      case 'short_term':
        return '📅';
      case 'long_term':
        return '📈';
      default:
        return '→';
    }
  };

  const getActionTypeDescription = (actionType) => {
    const descriptions = {
      'increase_savings': 'Increase your monthly savings amount',
      'improve_returns': 'Improve your investment returns',
      'delay_retirement': 'Consider delaying your retirement',
      'reduce_expenses': 'Reduce your monthly expenses',
      'pay_off_loans': 'Prioritize paying off loans',
      'diversify_investments': 'Diversify your investment portfolio'
    };
    return descriptions[actionType] || actionType;
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="glass-panel rounded-xl p-12 border border-white/10 text-center">
        <iconify-icon icon="solar:info-circle-linear" className="text-purple-400 text-4xl mb-4"></iconify-icon>
        <p className="text-white/50">No recommendations available yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:lightbulb-linear" className="text-purple-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Action Plan</h2>
          <p className="text-xs text-white/50">Prioritized recommendations to improve your retirement readiness</p>
        </div>
      </div>

      {/* Summary */}
      <div className="glass-panel rounded-xl p-6 border border-purple-500/20 bg-purple-500/5">
        <h3 className="text-lg font-semibold text-white mb-2">Action Plan Summary</h3>
        <p className="text-white/70">
          Follow these {recommendations.length} prioritized recommendations to improve your retirement readiness score.
        </p>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {recommendations.map((rec, index) => (
          <div key={rec.action_id} className="glass-panel rounded-xl p-6 border border-white/10 hover:border-purple-500/30 transition">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-4">
                <div className={`flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full ${getPriorityColor(rec.priority)} font-bold border`}>
                  {rec.priority}
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-white mb-1">
                    {rec.description}
                  </h4>
                  <p className="text-xs text-white/50">
                    {getActionTypeDescription(rec.action_type)}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-green-400">
                  +{rec.estimated_impact.toFixed(1)}
                </div>
                <p className="text-xs text-white/50">Score improvement</p>
              </div>
            </div>

            <div className="flex items-center gap-2 mb-4">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getPriorityColor(rec.priority)}`}>
                {getTimelineIcon(rec.timeline)} {rec.timeline.replace('_', ' ')}
              </span>
            </div>

            <div className="bg-white/5 rounded-lg p-4 border border-white/5">
              <p className="text-sm text-white/70">{rec.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Impact Projection */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <iconify-icon icon="solar:chart-square-linear" className="text-purple-400"></iconify-icon>
          Projected Impact
        </h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-white/70">Current Readiness Score</span>
            <span className="text-2xl font-bold text-purple-400">{plan.readiness_score.toFixed(1)}</span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-purple-500 transition-all duration-500"
              style={{ width: `${Math.min(plan.readiness_score, 100)}%` }}
            ></div>
          </div>

          <div className="mt-6 flex justify-between items-center">
            <span className="text-white/70">Potential Score (with all actions)</span>
            <span className="text-2xl font-bold text-green-400">
              {Math.min(100, plan.readiness_score + recommendations.reduce((sum, r) => sum + r.estimated_impact, 0)).toFixed(1)}
            </span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 transition-all duration-500"
              style={{
                width: `${Math.min(100, plan.readiness_score + recommendations.reduce((sum, r) => sum + r.estimated_impact, 0))}%`
              }}
            ></div>
          </div>
        </div>
      </div>

      {/* Implementation Guide */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <iconify-icon icon="solar:checklist-minimalistic-linear" className="text-purple-400"></iconify-icon>
          Implementation Guide
        </h3>
        <div className="space-y-4">
          <div className="border-l-4 border-danger-500 pl-4 py-2">
            <h4 className="font-semibold text-white mb-1">🔴 Immediate Actions (This Month)</h4>
            <p className="text-xs text-white/50">
              Start with high-priority recommendations that can be implemented immediately to see quick improvements.
            </p>
          </div>

          <div className="border-l-4 border-orange-500 pl-4 py-2">
            <h4 className="font-semibold text-white mb-1">🟠 Short-term Actions (Next 3 Months)</h4>
            <p className="text-xs text-white/50">
              Plan and execute medium-priority recommendations that require some preparation or adjustment.
            </p>
          </div>

          <div className="border-l-4 border-purple-500 pl-4 py-2">
            <h4 className="font-semibold text-white mb-1">🔵 Long-term Actions (6+ Months)</h4>
            <p className="text-xs text-white/50">
              Build sustainable habits and strategies that will compound over time for maximum retirement readiness.
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <iconify-icon icon="solar:wallet-linear" className="text-purple-400"></iconify-icon>
          Key Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-purple-500/10 rounded-lg p-4 border border-purple-500/20">
            <p className="text-white/50 text-xs mb-2 uppercase tracking-widest">Monthly Savings Required</p>
            <p className="text-2xl font-bold text-purple-400">{formatCurrency(plan.required_monthly_savings)}</p>
          </div>

          <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/20">
            <p className="text-white/50 text-xs mb-2 uppercase tracking-widest">Retirement Corpus Target</p>
            <p className="text-2xl font-bold text-green-400">{formatCurrency(plan.retirement_corpus)}</p>
          </div>

          <div className="bg-orange-500/10 rounded-lg p-4 border border-orange-500/20">
            <p className="text-white/50 text-xs mb-2 uppercase tracking-widest">Current Gap</p>
            <p className="text-2xl font-bold text-orange-400">{formatCurrency(Math.abs(plan.gap))}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActionPlanView;

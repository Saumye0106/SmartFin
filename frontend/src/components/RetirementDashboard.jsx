import RetirementGauge from './RetirementGauge';
import CorpusComparison from './CorpusComparison';
import SavingsProjection from './SavingsProjection';
import ReadinessBreakdown from './ReadinessBreakdown';

const RetirementDashboard = ({ plan }) => {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getGapStatus = () => {
    if (plan.gap < 0) {
      return { status: 'Surplus', color: 'text-green-400', bgColor: 'bg-green-500/10 border-green-500/20' };
    } else if (plan.gap_percentage < 20) {
      return { status: 'On Track', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20' };
    } else if (plan.gap_percentage < 50) {
      return { status: 'Moderate Gap', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10 border-yellow-500/20' };
    } else {
      return { status: 'Significant Gap', color: 'text-danger-400', bgColor: 'bg-danger-500/10 border-danger-500/20' };
    }
  };

  const gapStatus = getGapStatus();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:chart-2-linear" className="text-purple-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">{plan.plan_name}</h2>
          <p className="text-xs text-white/50">Retirement in {plan.retirement_age - plan.current_age} years at age {plan.retirement_age}</p>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Readiness Score */}
        <div className="glass-panel rounded-xl p-4 border border-white/10">
          <p className="text-xs text-white/50 mb-2 uppercase tracking-widest">Readiness Score</p>
          <p className="text-3xl font-bold text-purple-400">{plan.readiness_score.toFixed(1)}/100</p>
          <p className="text-xs text-white/40 mt-2 capitalize">{plan.readiness_classification}</p>
        </div>

        {/* Retirement Corpus */}
        <div className="glass-panel rounded-xl p-4 border border-white/10">
          <p className="text-xs text-white/50 mb-2 uppercase tracking-widest">Retirement Corpus</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(plan.retirement_corpus)}</p>
          <p className="text-xs text-white/40 mt-2">Total needed</p>
        </div>

        {/* Projected Savings */}
        <div className="glass-panel rounded-xl p-4 border border-white/10">
          <p className="text-xs text-white/50 mb-2 uppercase tracking-widest">Projected Savings</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(plan.projected_savings)}</p>
          <p className="text-xs text-white/40 mt-2">At retirement</p>
        </div>

        {/* Gap/Surplus */}
        <div className={`glass-panel rounded-xl p-4 border ${gapStatus.bgColor}`}>
          <p className="text-xs text-white/50 mb-2 uppercase tracking-widest">Gap/Surplus</p>
          <p className={`text-2xl font-bold ${gapStatus.color}`}>
            {formatCurrency(Math.abs(plan.gap))}
          </p>
          <p className={`text-xs mt-2 ${gapStatus.color}`}>{gapStatus.status}</p>
        </div>
      </div>

      {/* Monthly Savings */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <iconify-icon icon="solar:wallet-linear" className="text-purple-400"></iconify-icon>
          Monthly Savings
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-white/50 mb-2">Your current monthly savings</p>
            <p className="text-3xl font-bold text-white">{formatCurrency(plan.actual_monthly_savings || ((plan.current_salary / 12) - plan.current_monthly_expenses))}</p>
            <p className="text-xs text-white/40 mt-1">Income − Expenses</p>
          </div>
          <div>
            <p className="text-xs text-white/50 mb-2">Required to hit target</p>
            <p className={`text-3xl font-bold ${(plan.actual_monthly_savings || ((plan.current_salary / 12) - plan.current_monthly_expenses)) >= plan.required_monthly_savings ? 'text-green-400' : 'text-yellow-400'}`}>{formatCurrency(plan.required_monthly_savings)}</p>
            <p className="text-xs text-white/40 mt-1">Minimum monthly savings needed</p>
          </div>
          <div>
            <p className="text-xs text-white/50 mb-2">Current monthly expenses</p>
            <p className="text-2xl font-semibold text-white">{formatCurrency(plan.current_monthly_expenses)}</p>
          </div>
        </div>
      </div>

      {/* Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Readiness Gauge */}
        <div className="glass-panel rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <iconify-icon icon="solar:gauge-linear" className="text-purple-400"></iconify-icon>
            Retirement Readiness
          </h3>
          <RetirementGauge score={plan.readiness_score} />
        </div>

        {/* Readiness Breakdown */}
        <div className="glass-panel rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <iconify-icon icon="solar:chart-square-linear" className="text-purple-400"></iconify-icon>
            Readiness Factors
          </h3>
          <ReadinessBreakdown
            factors={{
              'Financial Health': plan.financial_health_factor,
              'Savings Adequacy': plan.savings_adequacy_factor,
              'Savings Rate': plan.savings_rate_factor,
              'Debt Burden': plan.debt_burden_factor,
              'Time Horizon': plan.time_horizon_factor
            }}
          />
        </div>
      </div>

      {/* Corpus Comparison */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <iconify-icon icon="solar:layers-linear" className="text-purple-400"></iconify-icon>
          Corpus Target vs Projected Savings
        </h3>
        <CorpusComparison
          target={plan.retirement_corpus}
          projected={plan.projected_savings}
        />
      </div>

      {/* Savings Projection */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <iconify-icon icon="solar:trending-up-linear" className="text-purple-400"></iconify-icon>
          Savings Growth Projection
        </h3>
        <SavingsProjection
          currentSavings={plan.current_savings}
          monthlySavings={plan.actual_monthly_savings || ((plan.current_salary / 12) - plan.current_monthly_expenses)}
          yearsToRetirement={plan.retirement_age - plan.current_age}
          returnRate={plan.investment_return_rate}
        />
      </div>

      {/* Summary */}
      <div className="glass-panel rounded-xl p-6 border border-purple-500/20 bg-purple-500/5">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <iconify-icon icon="solar:info-circle-linear" className="text-purple-400"></iconify-icon>
          Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-white/50 mb-1">Current Age</p>
            <p className="font-semibold text-white">{plan.current_age} years</p>
          </div>
          <div>
            <p className="text-white/50 mb-1">Retirement Age</p>
            <p className="font-semibold text-white">{plan.retirement_age} years</p>
          </div>
          <div>
            <p className="text-white/50 mb-1">Current Savings</p>
            <p className="font-semibold text-white">{formatCurrency(plan.current_savings)}</p>
          </div>
          <div>
            <p className="text-white/50 mb-1">Annual Salary</p>
            <p className="font-semibold text-white">{formatCurrency(plan.current_salary)}</p>
          </div>
          <div>
            <p className="text-white/50 mb-1">Inflation Rate</p>
            <p className="font-semibold text-white">{(plan.inflation_rate * 100).toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-white/50 mb-1">Expected Return</p>
            <p className="font-semibold text-white">{(plan.investment_return_rate * 100).toFixed(1)}%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RetirementDashboard;

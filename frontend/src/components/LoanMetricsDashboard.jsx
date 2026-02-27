import { useState, useEffect } from 'react';
import './LoanMetricsDashboard.css';

const LoanMetricsDashboard = ({ userId, onFetchMetrics }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [renderCount, setRenderCount] = useState(0);
  const [fetchCount, setFetchCount] = useState(0);

  const fetchMetrics = async () => {
    const newFetchCount = fetchCount + 1;
    setFetchCount(newFetchCount);
    console.log(`[FETCH #${newFetchCount}] Starting fetch for userId: ${userId}`);
    setLoading(true);
    setError(null);
    
    try {
      console.log(`[FETCH #${newFetchCount}] Calling onFetchMetrics...`);
      const data = await onFetchMetrics(userId);
      console.log(`[FETCH #${newFetchCount}] Data received:`, data);
      setMetrics(data);
      console.log(`[FETCH #${newFetchCount}] Metrics state updated`);
    } catch (err) {
      console.error(`[FETCH #${newFetchCount}] Error:`, err);
      setError(err.message || 'Failed to load metrics');
    } finally {
      setLoading(false);
      console.log(`[FETCH #${newFetchCount}] Fetch complete`);
    }
  };

  useEffect(() => {
    const newRenderCount = renderCount + 1;
    setRenderCount(newRenderCount);
    console.log(`[RENDER #${newRenderCount}] useEffect triggered with userId: ${userId}`);
    
    if (userId) {
      fetchMetrics();
    } else {
      console.warn(`[RENDER #${newRenderCount}] No userId provided`);
      setLoading(false);
      setError('User ID not available. Please log out and log back in.');
    }
    // Only fetch once on mount with userId
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const getScoreColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 65) return 'cyan';
    if (score >= 50) return 'yellow';
    if (score >= 35) return 'orange';
    return 'red';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 65) return 'Very Good';
    if (score >= 50) return 'Good';
    if (score >= 35) return 'Average';
    return 'Poor';
  };

  const getScoreIcon = (score) => {
    if (score >= 80) return 'solar:star-linear';
    if (score >= 65) return 'solar:star-shine-linear';
    if (score >= 50) return 'solar:check-circle-linear';
    if (score >= 35) return 'solar:info-circle-linear';
    return 'solar:danger-circle-linear';
  };

  const ScoreCard = ({ title, score, icon, description, breakdown }) => {
    const color = getScoreColor(score);
    const label = getScoreLabel(score);
    const scoreIcon = getScoreIcon(score);

    return (
      <div className="bg-[#0a0a0a] border border-white/10 rounded-lg p-5 hover:border-white/20 transition-all group">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg bg-${color}-500/10 border border-${color}-500/20 flex items-center justify-center`}>
              <iconify-icon icon={icon} width="20" className={`text-${color}-400`}></iconify-icon>
            </div>
            <div>
              <h3 className="text-white font-medium text-sm">{title}</h3>
              <p className="text-xs text-white/40">{description}</p>
            </div>
          </div>
        </div>

        {/* Score Display */}
        <div className="mb-4">
          <div className="flex items-end gap-2 mb-2">
            <span className={`text-4xl font-bold text-${color}-400`}>{Math.round(score)}</span>
            <span className="text-white/40 text-sm mb-1">/100</span>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
            <div 
              className={`h-full bg-${color}-500 transition-all duration-500 ease-out`}
              style={{ width: `${score}%` }}
            ></div>
          </div>
          
          {/* Label */}
          <div className="flex items-center justify-between mt-2">
            <span className={`text-xs font-medium text-${color}-400 flex items-center gap-1`}>
              <iconify-icon icon={scoreIcon} width="14"></iconify-icon>
              {label}
            </span>
            <span className="text-xs text-white/40">{Math.round(score)}%</span>
          </div>
        </div>

        {/* Breakdown */}
        {breakdown && (
          <div className="pt-4 border-t border-white/5 space-y-2">
            {Object.entries(breakdown).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-white/60 capitalize">{key.replace(/_/g, ' ')}</span>
                <span className="text-white font-medium">{typeof value === 'number' ? Math.round(value) : value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <iconify-icon icon="svg-spinners:ring-resize" width="32" className="text-cyan-400"></iconify-icon>
        <span className="ml-3 text-white/60">Loading metrics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6 text-center">
        <iconify-icon icon="solar:danger-circle-linear" width="48" className="text-red-400 mb-3"></iconify-icon>
        <p className="text-red-400 mb-4">{error}</p>
        <div className="text-xs text-red-300/60 mb-4 font-mono text-left bg-black/20 p-3 rounded">
          <div>Debug Info:</div>
          <div>- userId: {userId || 'undefined'}</div>
          <div>- userId type: {typeof userId}</div>
          <div>- localStorage userId: {typeof window !== 'undefined' ? localStorage.getItem('userId') : 'N/A'}</div>
        </div>
        <button
          onClick={fetchMetrics}
          className="px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-sm font-medium text-red-400 transition-all"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="text-center py-12">
        <iconify-icon icon="solar:wallet-money-linear" width="64" className="text-white/20 mb-4"></iconify-icon>
        <p className="text-white/40 mb-2">No loan data yet</p>
        <p className="text-white/20 text-sm mb-6">Add your first loan to start tracking metrics</p>
        <button
          onClick={() => window.location.href = '/loans'}
          className="px-6 py-3 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 transition-all text-sm font-medium"
        >
          Add Your First Loan
        </button>
      </div>
    );
  }

  const { 
    loan_diversity_score, 
    payment_history_score, 
    loan_maturity_score,
    payment_statistics,
    loan_statistics 
  } = metrics.metrics || metrics;

  // Check if user actually has loans
  const hasLoans = loan_statistics && loan_statistics.total_active_loans > 0;

  if (!hasLoans) {
    return (
      <div className="text-center py-12">
        <iconify-icon icon="solar:wallet-money-linear" width="64" className="text-white/20 mb-4"></iconify-icon>
        <p className="text-white/40 mb-2">No loans added yet</p>
        <p className="text-white/20 text-sm mb-6">Start tracking your loans to see personalized metrics and improve your financial health score</p>
        <button
          onClick={() => window.location.href = '/loans'}
          className="px-6 py-3 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 transition-all text-sm font-medium flex items-center gap-2 mx-auto"
        >
          <iconify-icon icon="solar:add-circle-linear" width="20"></iconify-icon>
          Add Your First Loan
        </button>
      </div>
    );
  }

  return (
    <div className="loan-metrics-dashboard space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">Loan Metrics</h2>
          <p className="text-sm text-white/60">Track your loan performance and health</p>
        </div>
        <button
          onClick={fetchMetrics}
          className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm font-medium text-white transition-all flex items-center gap-2"
        >
          <iconify-icon icon="solar:refresh-linear" width="18"></iconify-icon>
          Refresh
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Loan Diversity Score */}
        <ScoreCard
          title="Loan Diversity"
          score={loan_diversity_score || 50}
          icon="solar:pie-chart-2-linear"
          description="Variety of loan types"
          breakdown={loan_statistics ? {
            'Total Loans': loan_statistics.total_active_loans || 0,
            'Loan Types': Object.keys(loan_statistics.loan_type_distribution || {}).length || 0
          } : null}
        />

        {/* Payment History Score */}
        <ScoreCard
          title="Payment History"
          score={payment_history_score || 70}
          icon="solar:history-linear"
          description="On-time payment track record"
          breakdown={payment_statistics ? {
            'On-Time': `${Math.round(payment_statistics.on_time_payment_percentage || 0)}%`,
            'Late Payments': payment_statistics.late_payment_count || 0,
            'Missed Payments': payment_statistics.missed_payment_count || 0
          } : null}
        />

        {/* Loan Maturity Score */}
        <ScoreCard
          title="Loan Maturity"
          score={loan_maturity_score || 50}
          icon="solar:calendar-mark-linear"
          description="Loan tenure management"
          breakdown={loan_statistics ? {
            'Avg Tenure': `${Math.round(loan_statistics.average_loan_tenure || 0)} months`,
            'Total Amount': `₹${(loan_statistics.total_loan_amount || 0).toLocaleString('en-IN')}`
          } : null}
        />
      </div>

      {/* Detailed Statistics */}
      {(payment_statistics || loan_statistics) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Payment Statistics */}
          {payment_statistics && (
            <div className="bg-[#0a0a0a] border border-white/10 rounded-lg p-5">
              <h3 className="text-white font-medium mb-4 flex items-center gap-2">
                <iconify-icon icon="solar:card-linear" width="18" className="text-cyan-400"></iconify-icon>
                Payment Statistics
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Total Payments</span>
                  <span className="text-white font-semibold">{payment_statistics.total_payments || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">On-Time Percentage</span>
                  <span className="text-green-400 font-semibold">{Math.round(payment_statistics.on_time_payment_percentage || 0)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Late Payments</span>
                  <span className="text-orange-400 font-semibold">{payment_statistics.late_payment_count || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Missed Payments</span>
                  <span className="text-red-400 font-semibold">{payment_statistics.missed_payment_count || 0}</span>
                </div>
              </div>
            </div>
          )}

          {/* Loan Statistics */}
          {loan_statistics && (
            <div className="bg-[#0a0a0a] border border-white/10 rounded-lg p-5">
              <h3 className="text-white font-medium mb-4 flex items-center gap-2">
                <iconify-icon icon="solar:chart-2-linear" width="18" className="text-purple-400"></iconify-icon>
                Loan Statistics
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Active Loans</span>
                  <span className="text-white font-semibold">{loan_statistics.total_active_loans || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Total Amount</span>
                  <span className="text-white font-semibold">₹{(loan_statistics.total_loan_amount || 0).toLocaleString('en-IN')}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Average Tenure</span>
                  <span className="text-white font-semibold">{Math.round(loan_statistics.average_loan_tenure || 0)} months</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Weighted Tenure</span>
                  <span className="text-white font-semibold">{Math.round(loan_statistics.weighted_average_tenure || 0)} months</span>
                </div>
              </div>

              {/* Loan Type Distribution */}
              {loan_statistics.loan_type_distribution && Object.keys(loan_statistics.loan_type_distribution).length > 0 && (
                <div className="mt-4 pt-4 border-t border-white/5">
                  <p className="text-xs uppercase tracking-widest text-white/40 mb-3">Loan Type Distribution</p>
                  <div className="space-y-2">
                    {Object.entries(loan_statistics.loan_type_distribution).map(([type, percentage]) => (
                      <div key={type} className="flex items-center gap-2">
                        <span className="text-xs text-white/60 capitalize w-20">{type}</span>
                        <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-cyan-500"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-white font-medium w-12 text-right">{Math.round(percentage)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Info Note */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
        <div className="flex gap-3">
          <iconify-icon icon="solar:info-circle-linear" width="20" className="text-blue-400 flex-shrink-0 mt-0.5"></iconify-icon>
          <div className="text-sm text-blue-400/80">
            <p className="font-medium mb-1">About Loan Metrics</p>
            <p className="text-xs text-blue-400/60">
              These metrics contribute to your overall financial health score. Maintain diverse loans, make on-time payments, and manage loan tenures effectively to improve your score.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoanMetricsDashboard;

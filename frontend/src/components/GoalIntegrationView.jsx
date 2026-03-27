import { useState } from 'react';

const GoalIntegrationView = ({ plan }) => {
  const [goals] = useState([
    {
      goal_id: 1,
      goal_name: 'Retirement',
      target_amount: plan.retirement_corpus,
      current_amount: plan.current_savings,
      deadline: plan.retirement_age,
      priority: 'High',
      impact_on_retirement: 'Primary'
    }
  ]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const calculateProgress = (current, target) => {
    return Math.min((current / target) * 100, 100);
  };

  return (
    <div className="space-y-6">
      {/* Integration Summary */}
      <div className="glass-panel rounded-xl p-6 border border-purple-500/20 bg-purple-500/5">
        <h3 className="text-lg font-semibold text-white mb-2">Goal Integration Summary</h3>
        <p className="text-white/70">
          Your retirement goal is your primary financial objective. All other goals should be aligned with your retirement timeline.
        </p>
      </div>

      {/* Goals List */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Your Financial Goals</h3>
        <div className="space-y-4">
          {goals.map((goal) => {
            const progress = calculateProgress(goal.current_amount, goal.target_amount);

            return (
              <div key={goal.goal_id} className="border border-white/10 rounded-lg p-4 bg-white/5">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-semibold text-white">{goal.goal_name}</h4>
                    <p className="text-sm text-white/50">Target: {goal.deadline} years old</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${
                      goal.priority === 'High' ? 'bg-danger-500/10 text-danger-400 border-danger-500/20' :
                      goal.priority === 'Medium' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                      'bg-green-500/10 text-green-400 border-green-500/20'
                    }`}>
                      {goal.priority} Priority
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <p className="text-xs text-white/50 mb-1">Target Amount</p>
                    <p className="font-semibold text-white">{formatCurrency(goal.target_amount)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-white/50 mb-1">Current Amount</p>
                    <p className="font-semibold text-white">{formatCurrency(goal.current_amount)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-white/50 mb-1">Progress</p>
                    <p className="font-semibold text-purple-400">{progress.toFixed(0)}%</p>
                  </div>
                </div>

                <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-purple-500 h-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>

                <p className="text-xs text-white/50 mt-2">
                  Impact on Retirement: <span className="font-semibold">{goal.impact_on_retirement}</span>
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Goal Prioritization */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Goal Prioritization</h3>
        <div className="space-y-3">
          <div className="border-l-4 border-danger-500 pl-4 py-2">
            <h4 className="font-semibold text-white mb-1">🔴 Priority 1: Retirement</h4>
            <p className="text-sm text-white/50">
              Your retirement goal should be your primary focus. Allocate at least 70% of your savings capacity to this goal.
            </p>
          </div>

          <div className="border-l-4 border-yellow-500 pl-4 py-2">
            <h4 className="font-semibold text-white mb-1">🟡 Priority 2: Emergency Fund</h4>
            <p className="text-sm text-white/50">
              Maintain 6-12 months of expenses in an emergency fund. This protects your retirement savings from unexpected events.
            </p>
          </div>

          <div className="border-l-4 border-green-500 pl-4 py-2">
            <h4 className="font-semibold text-white mb-1">🟢 Priority 3: Other Goals</h4>
            <p className="text-sm text-white/50">
              After securing retirement and emergency funds, allocate remaining capacity to other goals like home purchase, education, etc.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GoalIntegrationView;

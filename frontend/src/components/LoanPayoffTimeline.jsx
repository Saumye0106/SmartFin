import { useState } from 'react';

const LoanPayoffTimeline = ({ plan }) => {
  const [strategy, setStrategy] = useState('balanced');

  const mockLoans = [
    { id: 1, name: 'Home Loan', amount: 2000000, rate: 0.065, emi: 15000, remaining_months: 240 },
    { id: 2, name: 'Car Loan', amount: 500000, rate: 0.085, emi: 12000, remaining_months: 48 },
    { id: 3, name: 'Personal Loan', amount: 200000, rate: 0.12, emi: 5000, remaining_months: 48 }
  ];

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const strategies = {
    snowball: {
      name: 'Snowball Strategy',
      description: 'Pay off smallest loans first to build momentum',
      order: [...mockLoans].sort((a, b) => a.amount - b.amount)
    },
    avalanche: {
      name: 'Avalanche Strategy',
      description: 'Pay off highest interest loans first to save money',
      order: [...mockLoans].sort((a, b) => b.rate - a.rate)
    },
    balanced: {
      name: 'Balanced Strategy',
      description: 'Balanced approach combining both strategies',
      order: mockLoans
    }
  };

  const currentStrategy = strategies[strategy];
  const totalDebt = mockLoans.reduce((sum, loan) => sum + loan.amount, 0);
  const totalEMI = mockLoans.reduce((sum, loan) => sum + loan.emi, 0);

  return (
    <div className="space-y-6">
      {/* Debt Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel rounded-lg p-6 border border-danger-500/20 bg-danger-500/5">
          <p className="text-white/50 text-sm mb-2">Total Debt</p>
          <p className="text-2xl font-bold text-danger-400">{formatCurrency(totalDebt)}</p>
        </div>

        <div className="glass-panel rounded-lg p-6 border border-orange-500/20 bg-orange-500/5">
          <p className="text-white/50 text-sm mb-2">Monthly EMI</p>
          <p className="text-2xl font-bold text-orange-400">{formatCurrency(totalEMI)}</p>
        </div>

        <div className="glass-panel rounded-lg p-6 border border-purple-500/20 bg-purple-500/5">
          <p className="text-white/50 text-sm mb-2">Impact on Retirement</p>
          <p className="text-2xl font-bold text-purple-400">High</p>
        </div>
      </div>

      {/* Strategy Selection */}
      <div className="glass-panel rounded-lg p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Loan Payoff Strategies</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(strategies).map(([key, strat]) => (
            <button
              key={key}
              onClick={() => setStrategy(key)}
              className={`p-4 rounded-lg border-2 transition text-left ${
                strategy === key
                  ? 'border-purple-500 bg-purple-500/10'
                  : 'border-white/10 bg-white/5 hover:border-purple-500/30'
              }`}
            >
              <h4 className="font-semibold text-white mb-1">{strat.name}</h4>
              <p className="text-sm text-white/50">{strat.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Payoff Timeline */}
      <div className="glass-panel rounded-lg p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Payoff Timeline - {currentStrategy.name}</h3>
        <div className="space-y-4">
          {currentStrategy.order.map((loan, index) => {
            const payoffMonths = loan.remaining_months;
            const payoffYears = (payoffMonths / 12).toFixed(1);

            return (
              <div key={loan.id} className="border border-white/10 rounded-lg p-4 bg-white/5">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-flex items-center justify-center w-6 h-6 bg-purple-500/20 text-purple-400 rounded-full text-sm font-bold border border-purple-500/30">
                        {index + 1}
                      </span>
                      <h4 className="font-semibold text-white">{loan.name}</h4>
                    </div>
                    <p className="text-sm text-white/50">Interest Rate: {(loan.rate * 100).toFixed(2)}%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-white">{formatCurrency(loan.amount)}</p>
                    <p className="text-xs text-white/50">Outstanding</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                  <div>
                    <p className="text-white/50 mb-1">Monthly EMI</p>
                    <p className="font-semibold text-white">{formatCurrency(loan.emi)}</p>
                  </div>
                  <div>
                    <p className="text-white/50 mb-1">Payoff Timeline</p>
                    <p className="font-semibold text-white">{payoffYears} years</p>
                  </div>
                  <div>
                    <p className="text-white/50 mb-1">Total Interest</p>
                    <p className="font-semibold text-white">
                      {formatCurrency(loan.emi * loan.remaining_months - loan.amount)}
                    </p>
                  </div>
                </div>

                <div className="w-full bg-white/10 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-full rounded-full"
                    style={{ width: `${((loan.remaining_months - payoffMonths) / loan.remaining_months) * 100}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Impact on Retirement */}
      <div className="glass-panel rounded-lg p-6 border border-purple-500/20 bg-purple-500/5">
        <h3 className="text-lg font-semibold text-white mb-3">Impact on Retirement Savings</h3>
        <p className="text-white/70 mb-4">
          By paying off your loans strategically, you can free up {formatCurrency(totalEMI)} per month for retirement savings.
        </p>
        <div className="bg-white/5 rounded-lg p-4 border border-white/10">
          <p className="text-sm text-white/50 mb-2">Additional Retirement Savings Potential</p>
          <p className="text-2xl font-bold text-green-400">
            {formatCurrency(totalEMI * 12 * (plan.retirement_age - plan.current_age))}
          </p>
          <p className="text-xs text-white/50 mt-2">
            If you redirect your EMI to retirement savings after paying off all loans
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoanPayoffTimeline;

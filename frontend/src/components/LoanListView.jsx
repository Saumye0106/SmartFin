import { useState, useEffect } from 'react';
import './LoanListView.css';

const LoanListView = ({ loans, onView, onEdit, onDelete, onRecordPayment, onViewPaymentHistory, loading, onRefresh }) => {
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filterType, setFilterType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const loanTypeColors = {
    personal: 'cyan',
    home: 'purple',
    auto: 'blue',
    education: 'green'
  };

  const loanTypeIcons = {
    personal: 'solar:user-circle-linear',
    home: 'solar:home-2-linear',
    auto: 'solar:bus-linear',
    education: 'solar:book-linear'
  };

  // Filter loans
  const filteredLoans = loans.filter(loan => {
    // Filter by type
    if (filterType !== 'all' && loan.loan_type !== filterType) {
      return false;
    }

    // Filter by search term
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return (
        loan.loan_type.toLowerCase().includes(search) ||
        loan.loan_amount.toString().includes(search) ||
        loan.loan_id.toLowerCase().includes(search)
      );
    }

    return true;
  });

  // Sort loans
  const sortedLoans = [...filteredLoans].sort((a, b) => {
    let aVal = a[sortBy];
    let bVal = b[sortBy];

    // Handle numeric values
    if (sortBy === 'loan_amount' || sortBy === 'monthly_emi' || sortBy === 'loan_tenure') {
      aVal = Number(aVal);
      bVal = Number(bVal);
    }

    // Handle dates
    if (sortBy === 'created_at' || sortBy === 'loan_start_date' || sortBy === 'loan_maturity_date') {
      aVal = new Date(aVal);
      bVal = new Date(bVal);
    }

    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateMonthsRemaining = (maturityDate) => {
    const now = new Date();
    const maturity = new Date(maturityDate);
    const months = Math.max(0, Math.round((maturity - now) / (1000 * 60 * 60 * 24 * 30)));
    return months;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <iconify-icon icon="svg-spinners:ring-resize" width="32" className="text-cyan-400"></iconify-icon>
        <span className="ml-3 text-white/60">Loading loans...</span>
      </div>
    );
  }

  if (!loans || loans.length === 0) {
    return (
      <div className="text-center py-12">
        <iconify-icon icon="solar:document-linear" width="64" className="text-white/20 mb-4"></iconify-icon>
        <p className="text-white/40 mb-4">No loans found</p>
        <p className="text-white/20 text-sm">Add your first loan to get started</p>
      </div>
    );
  }

  return (
    <div className="loan-list-view space-y-4">
      {/* Controls */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        {/* Search */}
        <div className="flex-1">
          <div className="relative">
            <iconify-icon 
              icon="solar:magnifer-linear" 
              width="18" 
              className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30"
            ></iconify-icon>
            <input
              type="text"
              placeholder="Search loans..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg pl-11 pr-4 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
            />
          </div>
        </div>

        {/* Filter by Type */}
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
        >
          <option value="all">All Types</option>
          <option value="personal">Personal</option>
          <option value="home">Home</option>
          <option value="auto">Auto</option>
          <option value="education">Education</option>
        </select>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
        >
          <option value="created_at">Date Added</option>
          <option value="loan_amount">Amount</option>
          <option value="loan_start_date">Start Date</option>
          <option value="loan_maturity_date">Maturity Date</option>
          <option value="monthly_emi">EMI</option>
        </select>

        {/* Sort Order */}
        <button
          onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
          className="bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white hover:border-white/20 transition-all"
        >
          <iconify-icon 
            icon={sortOrder === 'asc' ? 'solar:sort-vertical-linear' : 'solar:sort-vertical-linear'} 
            width="18"
            className={sortOrder === 'desc' ? 'rotate-180' : ''}
          ></iconify-icon>
        </button>

        {/* Refresh */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white hover:border-white/20 transition-all"
          >
            <iconify-icon icon="solar:refresh-linear" width="18"></iconify-icon>
          </button>
        )}
      </div>

      {/* Results Count */}
      <div className="text-xs text-white/40 mb-4">
        Showing {sortedLoans.length} of {loans.length} loans
      </div>

      {/* Loan Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sortedLoans.map((loan) => {
          const color = loanTypeColors[loan.loan_type];
          const icon = loanTypeIcons[loan.loan_type];
          const monthsRemaining = calculateMonthsRemaining(loan.loan_maturity_date);

          return (
            <div
              key={loan.loan_id}
              className="bg-[#0a0a0a] border border-white/10 rounded-lg p-5 hover:border-white/20 transition-all group"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg bg-${color}-500/10 border border-${color}-500/20 flex items-center justify-center`}>
                    <iconify-icon icon={icon} width="20" className={`text-${color}-400`}></iconify-icon>
                  </div>
                  <div>
                    <h3 className="text-white font-medium capitalize">{loan.loan_type} Loan</h3>
                    <p className="text-xs text-white/40 font-mono">{loan.loan_id.slice(0, 8)}...</p>
                  </div>
                </div>
                
                {loan.default_status ? (
                  <span className="px-2 py-1 rounded text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                    Default
                  </span>
                ) : (
                  <span className="px-2 py-1 rounded text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                    Active
                  </span>
                )}
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-white/40 mb-1">Loan Amount</p>
                  <p className="text-white font-semibold">{formatCurrency(loan.loan_amount)}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-white/40 mb-1">Monthly EMI</p>
                  <p className="text-white font-semibold">{formatCurrency(loan.monthly_emi)}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-white/40 mb-1">Interest Rate</p>
                  <p className="text-white font-semibold">{loan.interest_rate}%</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-white/40 mb-1">Tenure</p>
                  <p className="text-white font-semibold">{loan.loan_tenure} months</p>
                </div>
              </div>

              {/* Timeline */}
              <div className="flex items-center gap-2 mb-4 text-xs text-white/60">
                <iconify-icon icon="solar:calendar-mark-linear" width="14"></iconify-icon>
                <span>{formatDate(loan.loan_start_date)}</span>
                <span className="text-white/20">→</span>
                <span>{formatDate(loan.loan_maturity_date)}</span>
                <span className={`ml-auto px-2 py-0.5 rounded ${
                  monthsRemaining <= 6 ? 'bg-orange-500/10 text-orange-400' : 'bg-blue-500/10 text-blue-400'
                }`}>
                  {monthsRemaining} months left
                </span>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t border-white/5">
                <button
                  onClick={() => onView(loan)}
                  className="flex-1 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white transition-all flex items-center justify-center gap-2"
                >
                  <iconify-icon icon="solar:eye-linear" width="16"></iconify-icon>
                  View
                </button>
                <button
                  onClick={() => onRecordPayment(loan)}
                  className="flex-1 px-3 py-2 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-xs font-medium text-cyan-400 transition-all flex items-center justify-center gap-2"
                >
                  <iconify-icon icon="solar:card-linear" width="16"></iconify-icon>
                  Payment
                </button>
                {onViewPaymentHistory && (
                  <button
                    onClick={() => onViewPaymentHistory(loan)}
                    className="flex-1 px-3 py-2 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-xs font-medium text-purple-400 transition-all flex items-center justify-center gap-2"
                  >
                    <iconify-icon icon="solar:history-linear" width="16"></iconify-icon>
                    History
                  </button>
                )}
                <button
                  onClick={() => onEdit(loan)}
                  className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white transition-all"
                >
                  <iconify-icon icon="solar:pen-linear" width="16"></iconify-icon>
                </button>
                <button
                  onClick={() => onDelete(loan)}
                  className="px-3 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-xs font-medium text-red-400 transition-all"
                >
                  <iconify-icon icon="solar:trash-bin-trash-linear" width="16"></iconify-icon>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* No Results */}
      {sortedLoans.length === 0 && (
        <div className="text-center py-12">
          <iconify-icon icon="solar:magnifer-linear" width="48" className="text-white/20 mb-4"></iconify-icon>
          <p className="text-white/40">No loans match your filters</p>
          <button
            onClick={() => {
              setSearchTerm('');
              setFilterType('all');
            }}
            className="mt-4 text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
};

export default LoanListView;

import { useState, useEffect } from 'react';
import './PaymentForm.css';

const PaymentForm = ({ loan, onSubmit, onCancel, loading }) => {
  const [formData, setFormData] = useState({
    payment_date: new Date().toISOString().split('T')[0],
    payment_amount: loan?.monthly_emi || ''
  });

  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState(null);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (loan) {
      // Fetch payment history
      fetchPaymentHistory();
    }
  }, [loan]);

  const fetchPaymentHistory = async () => {
    setLoadingHistory(true);
    try {
      // This would be called from parent component
      // For now, we'll just set empty array
      setPaymentHistory([]);
    } catch (error) {
      console.error('Failed to fetch payment history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Validate payment date
    if (!formData.payment_date) {
      newErrors.payment_date = 'Payment date is required';
    } else {
      const paymentDate = new Date(formData.payment_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      // Allow today and past dates, reject only future dates
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      if (paymentDate >= tomorrow) {
        newErrors.payment_date = 'Payment date cannot be in the future';
      }
    }

    // Validate payment amount
    if (!formData.payment_amount || Number(formData.payment_amount) <= 0) {
      newErrors.payment_amount = 'Payment amount must be positive';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Convert to proper types and format date
    const data = {
      payment_date: new Date(formData.payment_date).toISOString(),
      payment_amount: Number(formData.payment_amount)
    };
    
    try {
      setSubmitError(null);
      console.log('Submitting payment:', data);
      onSubmit(data);
    } catch (err) {
      console.error('Error submitting payment:', err);
      setSubmitError(err.message || 'Failed to record payment');
    }
  };

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

  const getStatusColor = (status) => {
    switch (status) {
      case 'on-time':
        return 'green';
      case 'late':
        return 'orange';
      case 'missed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'on-time':
        return 'solar:check-circle-linear';
      case 'late':
        return 'solar:clock-circle-linear';
      case 'missed':
        return 'solar:close-circle-linear';
      default:
        return 'solar:question-circle-linear';
    }
  };

  return (
    <div className="payment-form-container space-y-6">
      {/* Error Display */}
      {submitError && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <iconify-icon icon="solar:danger-circle-linear" width="24" className="text-red-400 flex-shrink-0"></iconify-icon>
            <div>
              <h3 className="text-red-400 font-medium mb-1">Error</h3>
              <p className="text-red-400/80 text-sm">{submitError}</p>
              <button
                onClick={() => setSubmitError(null)}
                className="mt-2 text-xs text-red-400/60 hover:text-red-400 transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loan Summary */}
      {loan && (
        <div className="bg-[#0a0a0a] border border-white/10 rounded-lg p-4">
          <h3 className="text-sm font-medium text-white mb-3 capitalize">{loan.loan_type} Loan</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
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
        </div>
      )}

      {/* Payment Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Payment Date */}
          <div className="space-y-2">
            <label htmlFor="payment_date" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
              <iconify-icon icon="solar:calendar-mark-linear" width="14" className="text-blue-400"></iconify-icon>
              Payment Date
            </label>
            <input
              type="date"
              id="payment_date"
              name="payment_date"
              value={formData.payment_date}
              onChange={handleChange}
              max={new Date().toISOString().split('T')[0]}
              className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 ${
                errors.payment_date ? 'border-red-500/50' : 'border-white/10'
              }`}
            />
            {errors.payment_date && (
              <p className="text-xs text-red-400">{errors.payment_date}</p>
            )}
          </div>

          {/* Payment Amount */}
          <div className="space-y-2">
            <label htmlFor="payment_amount" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
              <iconify-icon icon="solar:wallet-money-linear" width="14" className="text-cyan-400"></iconify-icon>
              Payment Amount
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 text-sm font-mono">₹</span>
              <input
                type="number"
                id="payment_amount"
                name="payment_amount"
                value={formData.payment_amount}
                onChange={handleChange}
                placeholder={loan?.monthly_emi || '0'}
                min="0"
                step="0.01"
                className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-3 pl-8 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 font-mono ${
                  errors.payment_amount ? 'border-red-500/50' : 'border-white/10'
                }`}
              />
            </div>
            {errors.payment_amount && (
              <p className="text-xs text-red-400">{errors.payment_amount}</p>
            )}
            {loan && (
              <p className="text-xs text-white/40">
                Suggested: {formatCurrency(loan.monthly_emi)}
              </p>
            )}
          </div>
        </div>

        {/* Quick Amount Buttons */}
        {loan && (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, payment_amount: loan.monthly_emi }))}
              className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white transition-all"
            >
              EMI Amount
            </button>
            <button
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, payment_amount: loan.monthly_emi * 2 }))}
              className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white transition-all"
            >
              2x EMI
            </button>
            <button
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, payment_amount: loan.loan_amount }))}
              className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white transition-all"
            >
              Full Amount
            </button>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="relative flex-1 group overflow-hidden rounded-lg bg-white py-3 transition-all hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="relative z-10 flex items-center justify-center gap-2 text-sm font-semibold text-black">
              {loading ? (
                <>
                  <iconify-icon icon="svg-spinners:ring-resize" width="18"></iconify-icon>
                  Recording...
                </>
              ) : (
                <>
                  <iconify-icon icon="solar:check-circle-linear" width="18"></iconify-icon>
                  Record Payment
                </>
              )}
            </span>
          </button>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              className="px-6 py-3 rounded-lg border border-white/10 text-sm font-semibold text-white/60 hover:text-white hover:border-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {/* Payment History Timeline */}
      {paymentHistory && paymentHistory.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-white flex items-center gap-2">
            <iconify-icon icon="solar:history-linear" width="18"></iconify-icon>
            Payment History
          </h3>
          
          <div className="space-y-2">
            {paymentHistory.map((payment, index) => {
              const statusColor = getStatusColor(payment.payment_status);
              const statusIcon = getStatusIcon(payment.payment_status);
              
              return (
                <div
                  key={payment.payment_id || index}
                  className="bg-[#0a0a0a] border border-white/10 rounded-lg p-4 flex items-center gap-4"
                >
                  <div className={`w-10 h-10 rounded-lg bg-${statusColor}-500/10 border border-${statusColor}-500/20 flex items-center justify-center flex-shrink-0`}>
                    <iconify-icon icon={statusIcon} width="20" className={`text-${statusColor}-400`}></iconify-icon>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-white font-semibold">{formatCurrency(payment.payment_amount)}</p>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium bg-${statusColor}-500/10 text-${statusColor}-400 border border-${statusColor}-500/20 capitalize`}>
                        {payment.payment_status}
                      </span>
                    </div>
                    <p className="text-xs text-white/40">{formatDate(payment.payment_date)}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {loadingHistory && (
        <div className="flex items-center justify-center py-6">
          <iconify-icon icon="svg-spinners:ring-resize" width="24" className="text-cyan-400"></iconify-icon>
          <span className="ml-2 text-sm text-white/60">Loading payment history...</span>
        </div>
      )}
    </div>
  );
};

export default PaymentForm;

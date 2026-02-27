import { useState, useEffect } from 'react';
import './PaymentHistoryView.css';

const PaymentHistoryView = ({ loan, onClose }) => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (loan) {
      fetchPaymentHistory();
    }
  }, [loan]);

  const fetchPaymentHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get token from localStorage
      const token = localStorage.getItem('sf_token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`http://127.0.0.1:5000/api/loans/${loan.loan_id}/payments`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch payment history');
      }

      const data = await response.json();
      setPayments(data.payments || []);
    } catch (err) {
      console.error('Error fetching payment history:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePayment = async (paymentId) => {
    if (!window.confirm('Are you sure you want to delete this payment?')) {
      return;
    }

    try {
      const token = localStorage.getItem('sf_token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const url = `http://127.0.0.1:5000/api/loans/${loan.loan_id}/payments/${paymentId}`;
      console.log('Deleting payment from URL:', url);

      const response = await fetch(url, {
        method: 'DELETE',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('Delete response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to delete payment');
      }

      // Refresh payment history after deletion
      await fetchPaymentHistory();
    } catch (err) {
      console.error('Error deleting payment:', err);
      setError(err.message);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2
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

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-[#0a0a0a] border border-white/10 rounded-lg p-8 max-w-2xl w-full mx-4">
          <div className="flex items-center justify-center py-12">
            <iconify-icon icon="svg-spinners:ring-resize" width="32" className="text-cyan-400"></iconify-icon>
            <span className="ml-3 text-white/60">Loading payment history...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#0a0a0a] border border-white/10 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-white capitalize">{loan.loan_type} Loan - Payment History</h2>
            <p className="text-sm text-white/40 mt-1 font-mono">{loan.loan_id.slice(0, 12)}...</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-all"
          >
            <iconify-icon icon="solar:close-circle-linear" width="24" className="text-white/60"></iconify-icon>
          </button>
        </div>

        {/* Loan Summary */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4 mb-6">
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

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-6">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Payment History */}
        {payments.length === 0 ? (
          <div className="text-center py-12">
            <iconify-icon icon="solar:card-linear" width="48" className="text-white/20 mb-4"></iconify-icon>
            <p className="text-white/40">No payments recorded yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
              <iconify-icon icon="solar:history-linear" width="18"></iconify-icon>
              {payments.length} Payment{payments.length !== 1 ? 's' : ''} Recorded
            </h3>

            {payments.map((payment, index) => {
              const statusColor = getStatusColor(payment.payment_status);
              const statusIcon = getStatusIcon(payment.payment_status);

              return (
                <div
                  key={payment.payment_id || index}
                  className="bg-white/5 border border-white/10 rounded-lg p-4 hover:border-white/20 transition-all"
                >
                  <div className="flex items-start gap-4">
                    {/* Status Icon */}
                    <div className={`w-10 h-10 rounded-lg bg-${statusColor}-500/10 border border-${statusColor}-500/20 flex items-center justify-center flex-shrink-0 mt-1`}>
                      <iconify-icon icon={statusIcon} width="20" className={`text-${statusColor}-400`}></iconify-icon>
                    </div>

                    {/* Payment Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-white font-semibold">{formatCurrency(payment.payment_amount)}</p>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium bg-${statusColor}-500/10 text-${statusColor}-400 border border-${statusColor}-500/20 capitalize`}>
                          {payment.payment_status}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-white/40">
                        <div className="flex items-center gap-1">
                          <iconify-icon icon="solar:calendar-mark-linear" width="14"></iconify-icon>
                          <span>{formatDate(payment.payment_date)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <iconify-icon icon="solar:clock-circle-linear" width="14"></iconify-icon>
                          <span>{new Date(payment.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>
                    </div>

                    {/* Delete Button */}
                    <button
                      onClick={() => handleDeletePayment(payment.payment_id)}
                      className="p-2 hover:bg-red-500/10 rounded-lg transition-all flex-shrink-0"
                      title="Delete payment"
                    >
                      <iconify-icon icon="solar:trash-bin-trash-linear" width="18" className="text-red-400 hover:text-red-300"></iconify-icon>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Summary Stats */}
        {payments.length > 0 && (
          <div className="mt-6 pt-6 border-t border-white/10">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white/5 rounded-lg p-3">
                <p className="text-[10px] uppercase tracking-widest text-white/40 mb-1">Total Paid</p>
                <p className="text-white font-semibold">
                  {formatCurrency(payments.reduce((sum, p) => sum + parseFloat(p.payment_amount), 0))}
                </p>
              </div>
              <div className="bg-white/5 rounded-lg p-3">
                <p className="text-[10px] uppercase tracking-widest text-white/40 mb-1">Remaining</p>
                <p className="text-white font-semibold">
                  {formatCurrency(
                    loan.loan_amount - payments.reduce((sum, p) => sum + parseFloat(p.payment_amount), 0)
                  )}
                </p>
              </div>
              <div className="bg-white/5 rounded-lg p-3">
                <p className="text-[10px] uppercase tracking-widest text-white/40 mb-1">Progress</p>
                <p className="text-white font-semibold">
                  {Math.round(
                    (payments.reduce((sum, p) => sum + parseFloat(p.payment_amount), 0) / loan.loan_amount) * 100
                  )}%
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Close Button */}
        <button
          onClick={onClose}
          className="w-full mt-6 px-4 py-3 rounded-lg bg-white/10 hover:bg-white/20 text-white font-medium transition-all"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default PaymentHistoryView;

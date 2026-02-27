import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import LoanListView from './LoanListView';
import LoanForm from './LoanForm';
import PaymentForm from './PaymentForm';
import PaymentHistoryView from './PaymentHistoryView';
import Sidebar from './Sidebar';
import api from '../services/api';

function LoanManagementPage() {
  const [view, setView] = useState('list'); // 'list', 'create', 'edit', 'payment'
  const [selectedLoan, setSelectedLoan] = useState(null);
  const [paymentHistoryLoan, setPaymentHistoryLoan] = useState(null);
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchLoans();
  }, []);

  const fetchLoans = async () => {
    try {
      setLoading(true);
      setError(null);
      const userId = localStorage.getItem('userId');
      if (userId) {
        const data = await api.getUserLoans(userId);
        setLoans(data.loans || []);
      }
    } catch (err) {
      console.error('Error fetching loans:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLoan = async (loanData) => {
    try {
      setError(null);
      await api.createLoan(loanData);
      await fetchLoans();
      setView('list');
    } catch (err) {
      console.error('Error creating loan:', err);
      setError(err.message);
      throw err;
    }
  };

  const handleUpdateLoan = async (loanId, updates) => {
    try {
      setError(null);
      await api.updateLoan(loanId, updates);
      await fetchLoans();
      setView('list');
      setSelectedLoan(null);
    } catch (err) {
      console.error('Error updating loan:', err);
      setError(err.message || 'Failed to update loan');
    }
  };

  const handleDeleteLoan = async (loan) => {
    if (window.confirm('Are you sure you want to delete this loan?')) {
      try {
        console.log('Deleting loan:', loan.loan_id);
        const result = await api.deleteLoan(loan.loan_id);
        console.log('Loan deleted successfully:', result);
        setError(null);
        await fetchLoans();
      } catch (err) {
        console.error('Error deleting loan:', err);
        setError(err.message || 'Failed to delete loan');
      }
    }
  };

  const handleRecordPayment = async (loanId, paymentData) => {
    try {
      setError(null);
      console.log('Recording payment for loan:', loanId, 'with data:', paymentData);
      await api.recordPayment(loanId, paymentData);
      console.log('Payment recorded successfully');
      await fetchLoans();
      setView('list');
      setSelectedLoan(null);
    } catch (err) {
      console.error('Error recording payment:', err);
      setError(err.message || 'Failed to record payment');
    }
  };

  const handleViewLoan = (loan) => {
    setSelectedLoan(loan);
    setView('payment');
  };

  const handleEditLoan = (loan) => {
    setSelectedLoan(loan);
    setView('edit');
  };

  const handlePaymentClick = (loan) => {
    setSelectedLoan(loan);
    setView('payment');
  };

  const handleViewPaymentHistory = (loan) => {
    setPaymentHistoryLoan(loan);
  };

  const handleClosePaymentHistory = () => {
    setPaymentHistoryLoan(null);
  };

  return (
    <div className="min-h-screen bg-[#030303] text-white">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-purple-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-500/15 rounded-full blur-[100px] mix-blend-screen"></div>
      </div>

      {/* Sidebar */}
      <Sidebar />

      {/* Navigation Header */}
      <nav className="fixed top-0 left-0 w-full z-50">
        <div className="absolute inset-0 bg-black/50 backdrop-blur-md border-b border-white/5"></div>
        <div className="max-w-7xl mx-auto px-6 h-16 relative flex items-center justify-between">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-3 group transition-all hover:opacity-80"
          >
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-purple-500/50 transition-colors">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-purple-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">LOANS</span>
          </button>

          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium"
          >
            <iconify-icon icon="solar:arrow-left-linear" width="16"></iconify-icon>
            <span>Back to Dashboard</span>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="relative z-10 pt-24 pb-12 px-6 ml-20">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              Loan Management
            </h1>
            <p className="text-white/60">Track and manage your loans and payments</p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 bg-red-500/10 border border-red-500/20 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <iconify-icon icon="solar:danger-circle-linear" width="24" className="text-red-400 flex-shrink-0"></iconify-icon>
                <div>
                  <h3 className="text-red-400 font-medium mb-1">Error</h3>
                  <p className="text-red-400/80 text-sm">{error}</p>
                  <button
                    onClick={() => setError(null)}
                    className="mt-2 text-xs text-red-400/60 hover:text-red-400 transition-colors"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* View Switcher */}
          {view === 'list' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white">Your Loans</h2>
                <button
                  onClick={() => setView('create')}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 transition-all text-sm font-medium flex items-center gap-2"
                >
                  <iconify-icon icon="solar:add-circle-linear" width="18"></iconify-icon>
                  Add Loan
                </button>
              </div>

              <LoanListView
                loans={loans}
                loading={loading}
                onView={handleViewLoan}
                onEdit={handleEditLoan}
                onDelete={handleDeleteLoan}
                onRecordPayment={handlePaymentClick}
                onViewPaymentHistory={handleViewPaymentHistory}
                onRefresh={fetchLoans}
              />
            </div>
          )}

          {view === 'create' && (
            <div className="glass-panel rounded-2xl p-8 border border-white/10">
              <h2 className="text-2xl font-bold mb-6">Add New Loan</h2>
              <LoanForm
                onSubmit={handleCreateLoan}
                onCancel={() => setView('list')}
              />
            </div>
          )}

          {view === 'edit' && selectedLoan && (
            <div className="glass-panel rounded-2xl p-8 border border-white/10">
              <h2 className="text-2xl font-bold mb-6">Edit Loan</h2>
              <LoanForm
                loan={selectedLoan}
                onSubmit={(updates) => handleUpdateLoan(selectedLoan.loan_id, updates)}
                onCancel={() => {
                  setView('list');
                  setSelectedLoan(null);
                }}
              />
            </div>
          )}

          {view === 'payment' && selectedLoan && (
            <div className="glass-panel rounded-2xl p-8 border border-white/10">
              <h2 className="text-2xl font-bold mb-6">Record Payment</h2>
              <PaymentForm
                loan={selectedLoan}
                onSubmit={(paymentData) => handleRecordPayment(selectedLoan.loan_id, paymentData)}
                onCancel={() => {
                  setView('list');
                  setSelectedLoan(null);
                }}
              />
            </div>
          )}

          {/* Payment History Modal */}
          {paymentHistoryLoan && (
            <PaymentHistoryView
              loan={paymentHistoryLoan}
              onClose={handleClosePaymentHistory}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default LoanManagementPage;

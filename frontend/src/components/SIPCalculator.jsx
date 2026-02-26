import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './SIPCalculator.css';

function SIPCalculator() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('sip'); // 'sip' or 'lumpsum'
  
  // SIP Form Data
  const [sipFormData, setSipFormData] = useState({
    monthly_investment: '',
    annual_return_rate: '',
    time_period_years: ''
  });
  
  // Lumpsum Form Data
  const [lumpsumFormData, setLumpsumFormData] = useState({
    principal_amount: '',
    annual_return_rate: '',
    time_period_years: ''
  });
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSipChange = (e) => {
    const { name, value } = e.target;
    setSipFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleLumpsumChange = (e) => {
    const { name, value } = e.target;
    setLumpsumFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleCalculate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let response;
      if (activeTab === 'sip') {
        response = await api.calculateSIP(sipFormData);
      } else {
        response = await api.calculateLumpsum(lumpsumFormData);
      }
      setResult(response);
    } catch (err) {
      setError(err.message || 'Failed to calculate');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    if (activeTab === 'sip') {
      setSipFormData({
        monthly_investment: '',
        annual_return_rate: '',
        time_period_years: ''
      });
    } else {
      setLumpsumFormData({
        principal_amount: '',
        annual_return_rate: '',
        time_period_years: ''
      });
    }
    setResult(null);
    setError('');
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setResult(null);
    setError('');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-[#030303] text-white">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-blue-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-500/15 rounded-full blur-[100px] mix-blend-screen"></div>
      </div>

      {/* Navigation Header */}
      <nav className="fixed top-0 left-0 w-full z-50 transition-all duration-300">
        <div className="absolute inset-0 bg-black/50 backdrop-blur-md border-b border-white/5"></div>
        <div className="max-w-7xl mx-auto px-6 h-16 relative flex items-center justify-between">
          {/* Logo */}
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-3 group transition-all hover:opacity-80"
          >
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-blue-500/50 transition-colors">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-blue-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">INVESTMENT CALCULATOR</span>
          </button>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium"
            >
              <iconify-icon icon="solar:arrow-left-linear" width="16"></iconify-icon>
              <span className="hidden md:inline">Back to Dashboard</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-16 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <section className="mb-12">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span>
              <span className="text-xs text-white/50 font-medium tracking-widest uppercase">Investment Planning</span>
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
              Investment <span className="text-gradient-blue">Calculator</span>
            </h1>
            <p className="text-white/50 max-w-2xl">
              Calculate your SIP or Lumpsum investment returns and plan your financial future
            </p>
          </section>

          {/* Tab Switcher */}
          <div className="flex items-center gap-3 mb-8">
            <button
              onClick={() => handleTabChange('sip')}
              className={`px-6 py-3 rounded-lg font-semibold text-sm transition-all ${
                activeTab === 'sip'
                  ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-900/30'
                  : 'bg-white/5 text-white/60 hover:bg-white/10 border border-white/10'
              }`}
            >
              <div className="flex items-center gap-2">
                <iconify-icon icon="solar:chart-2-linear" width="18"></iconify-icon>
                SIP Calculator
              </div>
            </button>
            <button
              onClick={() => handleTabChange('lumpsum')}
              className={`px-6 py-3 rounded-lg font-semibold text-sm transition-all ${
                activeTab === 'lumpsum'
                  ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-900/30'
                  : 'bg-white/5 text-white/60 hover:bg-white/10 border border-white/10'
              }`}
            >
              <div className="flex items-center gap-2">
                <iconify-icon icon="solar:wallet-money-linear" width="18"></iconify-icon>
                Lumpsum Calculator
              </div>
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Calculator Form */}
            <div className="glass-panel rounded-xl p-8 border border-white/10">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                  <iconify-icon icon="solar:calculator-linear" className="text-blue-400 text-xl"></iconify-icon>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">
                    {activeTab === 'sip' ? 'SIP Details' : 'Lumpsum Details'}
                  </h2>
                  <p className="text-xs text-white/50">
                    {activeTab === 'sip' ? 'Enter your monthly investment parameters' : 'Enter your one-time investment parameters'}
                  </p>
                </div>
              </div>

              {error && (
                <div className="mb-6 p-4 rounded-lg bg-danger-950/30 border border-danger-500/30 flex items-start gap-3">
                  <iconify-icon icon="solar:danger-triangle-linear" className="text-danger-400 mt-0.5 shrink-0"></iconify-icon>
                  <div className="text-sm text-danger-400">{error}</div>
                </div>
              )}

              <form onSubmit={handleCalculate} className="space-y-6">
                {activeTab === 'sip' ? (
                  <>
                    {/* Monthly Investment */}
                    <div className="space-y-2 group">
                      <label htmlFor="monthly_investment" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-blue-400">
                        Monthly Investment (₹)
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          id="monthly_investment"
                          name="monthly_investment"
                          value={sipFormData.monthly_investment}
                          onChange={handleSipChange}
                          className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                          placeholder="5000"
                          min="100"
                          step="100"
                          required
                        />
                        <iconify-icon icon="solar:wallet-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-blue-400 transition-colors text-lg"></iconify-icon>
                      </div>
                    </div>

                    {/* Expected Return Rate */}
                    <div className="space-y-2 group">
                      <label htmlFor="annual_return_rate" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-blue-400">
                        Expected Annual Return (%)
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          id="annual_return_rate"
                          name="annual_return_rate"
                          value={sipFormData.annual_return_rate}
                          onChange={handleSipChange}
                          className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                          placeholder="12"
                          min="0"
                          max="100"
                          step="0.1"
                          required
                        />
                        <iconify-icon icon="solar:chart-2-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-blue-400 transition-colors text-lg"></iconify-icon>
                      </div>
                    </div>

                    {/* Time Period */}
                    <div className="space-y-2 group">
                      <label htmlFor="time_period_years" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-blue-400">
                        Time Period (Years)
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          id="time_period_years"
                          name="time_period_years"
                          value={sipFormData.time_period_years}
                          onChange={handleSipChange}
                          className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                          placeholder="10"
                          min="1"
                          max="50"
                          step="1"
                          required
                        />
                        <iconify-icon icon="solar:calendar-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-blue-400 transition-colors text-lg"></iconify-icon>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    {/* Principal Amount */}
                    <div className="space-y-2 group">
                      <label htmlFor="principal_amount" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-blue-400">
                        Investment Amount (₹)
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          id="principal_amount"
                          name="principal_amount"
                          value={lumpsumFormData.principal_amount}
                          onChange={handleLumpsumChange}
                          className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                          placeholder="100000"
                          min="1000"
                          step="1000"
                          required
                        />
                        <iconify-icon icon="solar:wallet-money-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-blue-400 transition-colors text-lg"></iconify-icon>
                      </div>
                    </div>

                    {/* Expected Return Rate */}
                    <div className="space-y-2 group">
                      <label htmlFor="annual_return_rate_lumpsum" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-blue-400">
                        Expected Annual Return (%)
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          id="annual_return_rate_lumpsum"
                          name="annual_return_rate"
                          value={lumpsumFormData.annual_return_rate}
                          onChange={handleLumpsumChange}
                          className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                          placeholder="12"
                          min="0"
                          max="100"
                          step="0.1"
                          required
                        />
                        <iconify-icon icon="solar:chart-2-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-blue-400 transition-colors text-lg"></iconify-icon>
                      </div>
                    </div>

                    {/* Time Period */}
                    <div className="space-y-2 group">
                      <label htmlFor="time_period_years_lumpsum" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-blue-400">
                        Time Period (Years)
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          id="time_period_years_lumpsum"
                          name="time_period_years"
                          value={lumpsumFormData.time_period_years}
                          onChange={handleLumpsumChange}
                          className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
                          placeholder="10"
                          min="1"
                          max="50"
                          step="1"
                          required
                        />
                        <iconify-icon icon="solar:calendar-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-blue-400 transition-colors text-lg"></iconify-icon>
                      </div>
                    </div>
                  </>
                )}

                {/* Buttons */}
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={handleReset}
                    className="flex-1 px-6 py-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-sm font-semibold"
                  >
                    Reset
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 border border-blue-400/20 transition-all text-sm font-semibold shadow-lg shadow-blue-900/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <iconify-icon icon="solar:spinner-solid" className="animate-spin text-lg"></iconify-icon>
                        Calculating...
                      </>
                    ) : (
                      <>
                        <iconify-icon icon="solar:calculator-linear" width="18"></iconify-icon>
                        Calculate
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Results Panel */}
            {result && (
              <div className="glass-panel rounded-xl p-8 border border-white/10 animate-fade-in-up">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                    <iconify-icon icon="solar:chart-square-linear" className="text-green-400 text-xl"></iconify-icon>
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">Investment Summary</h2>
                    <p className="text-xs text-white/50">Your SIP returns breakdown</p>
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="space-y-4 mb-6">
                  <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                    <div className="text-xs text-white/50 mb-1">Total Invested</div>
                    <div className="text-2xl font-bold text-white">{formatCurrency(result.total_invested)}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                    <div className="text-xs text-green-400 mb-1">Estimated Returns</div>
                    <div className="text-2xl font-bold text-green-400">{formatCurrency(result.estimated_returns)}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                    <div className="text-xs text-blue-400 mb-1">Future Value</div>
                    <div className="text-3xl font-bold text-blue-400">{formatCurrency(result.future_value)}</div>
                  </div>
                </div>

                {/* Year-wise Breakdown */}
                <div className="border-t border-white/10 pt-6">
                  <h3 className="text-sm font-bold text-white mb-4">Year-wise Growth</h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
                    {result.yearly_breakdown.map((year) => (
                      <div key={year.year} className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                            <span className="text-xs font-bold text-blue-400">{year.year}</span>
                          </div>
                          <div>
                            <div className="text-xs text-white/70">Year {year.year}</div>
                            <div className="text-xs text-white/50">{formatCurrency(year.invested)} invested</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-white">{formatCurrency(year.value)}</div>
                          <div className="text-xs text-green-400">+{formatCurrency(year.returns)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Empty State */}
            {!result && !loading && (
              <div className="glass-panel rounded-xl p-12 border border-white/10 flex flex-col items-center justify-center text-center">
                <div className="w-20 h-20 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6">
                  <iconify-icon icon="solar:chart-square-linear" className="text-blue-400 text-4xl"></iconify-icon>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">
                  Calculate Your {activeTab === 'sip' ? 'SIP' : 'Lumpsum'} Returns
                </h3>
                <p className="text-white/50 max-w-sm">
                  {activeTab === 'sip' 
                    ? 'Enter your monthly investment details to see how your money can grow over time with systematic investing'
                    : 'Enter your one-time investment details to see how your money can grow over time with compound interest'
                  }
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-20 border-t border-white/10 bg-black/50 backdrop-blur-md py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-blue-400 text-lg"></iconify-icon>
                <span className="font-display font-bold text-white">SmartFin</span>
                <span className="text-[10px] text-white/30 font-mono">v2.0.4</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                <span className="text-white/40">System Operational</span>
              </div>
            </div>
            <div className="text-xs text-white/30">
              Educational Use Only • College Project
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default SIPCalculator;

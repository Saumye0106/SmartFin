import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import FinancialForm from './FinancialForm';
import ScoreDisplay from './ScoreDisplay';
import SpendingChart from './SpendingChart';
import RatiosDashboard from './RatiosDashboard';
import AlertsPanel from './AlertsPanel';
import GuidancePanel from './GuidancePanel';
import InvestmentAdvice from './InvestmentAdvice';
import WhatIfSimulator from './WhatIfSimulator';

const MainDashboard = ({ 
  user, 
  onLogout, 
  onAnalyze, 
  onWhatIf, 
  loading, 
  result, 
  currentData, 
  error
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[#030303] text-white">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-cyan-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-500/15 rounded-full blur-[100px] mix-blend-screen"></div>
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
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-cyan-500/50 transition-colors">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-cyan-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">DASHBOARD</span>
          </button>

          {/* User Info & Actions */}
          <div className="flex items-center gap-6">
            <div className="hidden md:flex items-center gap-3 text-xs">
              <span className="text-white/40">Welcome back,</span>
              <span className="text-white font-medium">{user.email}</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/sip-calculator')}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 hover:border-blue-500/40 transition-all text-xs font-medium text-blue-400"
                title="SIP Calculator"
              >
                <iconify-icon icon="solar:calculator-linear" width="16"></iconify-icon>
                <span className="hidden md:inline">SIP</span>
              </button>
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 hover:border-cyan-500/40 transition-all text-xs font-medium text-cyan-400"
                title="My Profile"
              >
                <iconify-icon icon="solar:user-circle-linear" width="16"></iconify-icon>
                <span className="hidden md:inline">Profile</span>
              </button>
              <div className="text-[10px] font-mono text-cyan-400 bg-cyan-950/20 px-3 py-1.5 rounded-full border border-cyan-500/20">
                {currentTime.toLocaleTimeString('en-US', { hour12: false })}
              </div>
              <button 
                onClick={onLogout}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium"
              >
                <iconify-icon icon="solar:logout-2-linear" width="16"></iconify-icon>
                <span className="hidden md:inline">Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-16 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <section className="mb-12">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="text-xs text-white/50 font-medium tracking-widest uppercase">Live Analysis</span>
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
              Your Financial <span className="text-gradient">Command Center</span>
            </h1>
            <p className="text-white/50 max-w-2xl">
              AI-powered insights and real-time analysis to help you make smarter financial decisions
            </p>
          </section>

          {/* Error Display */}
          {error && (
            <div className="glass-panel rounded-xl p-6 mb-8 border-danger-500/30 bg-danger-950/20">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-danger-500/10 border border-danger-500/20 flex items-center justify-center shrink-0">
                  <iconify-icon icon="solar:danger-triangle-linear" className="text-danger-400 text-xl"></iconify-icon>
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-1">Analysis Error</h3>
                  <p className="text-danger-400 text-sm">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Financial Form */}
          <section className="mb-12">
            <div className="glass-panel rounded-xl p-8 border border-white/10">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                  <iconify-icon icon="solar:calculator-linear" className="text-cyan-400 text-xl"></iconify-icon>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Financial Analysis</h2>
                  <p className="text-xs text-white/50">Enter your data for AI-powered insights</p>
                </div>
              </div>
              <FinancialForm onSubmit={onAnalyze} loading={loading} />
            </div>
          </section>

          {/* Loading State */}
          {loading && (
            <div className="glass-panel rounded-xl p-12 text-center mb-12">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-6 relative">
                <iconify-icon icon="solar:spinner-solid" className="text-cyan-400 text-3xl animate-spin"></iconify-icon>
                <div className="absolute inset-0 rounded-full bg-cyan-500/20 animate-ping"></div>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Analyzing Your Finances</h3>
              <p className="text-white/50 text-sm">Our AI is processing your data to provide personalized insights...</p>
            </div>
          )}

          {/* Results Section */}
          {result && !loading && (
            <div className="space-y-8">
              {/* Section Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Financial Health Report</h2>
                  <p className="text-xs text-white/40 font-mono">
                    Generated {new Date().toLocaleDateString('en-US', { 
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-xs font-medium">
                  <iconify-icon icon="solar:file-download-linear" width="16"></iconify-icon>
                  Export Report
                </button>
              </div>

              {/* Score Display - Full Width */}
              <div className="glass-panel glass-panel-hover rounded-xl p-8 border border-white/10">
                <ScoreDisplay 
                  score={result.score} 
                  classification={result.classification} 
                />
              </div>

              {/* Charts Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel glass-panel-hover rounded-xl p-6 border border-white/10">
                  <SpendingChart patterns={result.patterns} />
                </div>
                <div className="glass-panel glass-panel-hover rounded-xl p-6 border border-white/10">
                  <RatiosDashboard patterns={result.patterns} />
                </div>
              </div>

              {/* Alerts - Full Width */}
              <div className="glass-panel glass-panel-hover rounded-xl p-6 border border-white/10">
                <AlertsPanel anomalies={result.anomalies} />
              </div>

              {/* Guidance & Investment Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel glass-panel-hover rounded-xl p-6 border border-white/10">
                  <GuidancePanel guidance={result.guidance} />
                </div>
                <div className="glass-panel glass-panel-hover rounded-xl p-6 border border-white/10">
                  <InvestmentAdvice investments={result.investments} />
                </div>
              </div>

              {/* What-If Simulator - Full Width */}
              <div className="glass-panel glass-panel-hover rounded-xl p-8 border border-white/10">
                <WhatIfSimulator 
                  currentData={currentData} 
                  onSimulate={onWhatIf}
                />
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-20 border-t border-white/10 bg-black/50 backdrop-blur-md py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-cyan-400 text-lg"></iconify-icon>
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
};

export default MainDashboard;

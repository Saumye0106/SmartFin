import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import RetirementInputForm from './RetirementInputForm';
import RetirementDashboard from './RetirementDashboard';
import ScenarioComparison from './ScenarioComparison';
import ActionPlanView from './ActionPlanView';
import Sidebar from './Sidebar';
import api from '../services/api';

const RetirementPlanner = () => {
  const [currentView, setCurrentView] = useState('input');
  const [plan, setPlan] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');

  // Load most recent saved plan on mount
  useEffect(() => {
    const loadSavedPlan = async () => {
      if (!userId) return;
      try {
        const response = await api.getRetirementPlans(userId);
        const plans = response.plans || [];
        if (plans.length > 0) {
          const latestPlan = plans[0];
          setPlan(latestPlan);
          setCurrentView('dashboard');

          // Load recommendations and scenarios for the saved plan
          try {
            const recResponse = await api.getRetirementRecommendations(latestPlan.plan_id);
            setRecommendations(recResponse.recommendations || []);
          } catch (e) { /* recommendations not critical */ }

          try {
            const scenResponse = await api.getRetirementScenarios(latestPlan.plan_id);
            setScenarios(scenResponse.scenarios || []);
          } catch (e) { /* scenarios not critical */ }
        }
      } catch (err) {
        // No saved plans, show input form
      }
    };
    loadSavedPlan();
  }, [userId]);

  const handlePlanCreated = async (planData) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.calculateRetirementPlan(planData);
      const newPlan = response.plan;

      setPlan(newPlan);
      setScenarios([]);
      setCurrentView('dashboard');

      // Fetch recommendations (don't let failure block the dashboard)
      try {
        const recResponse = await api.getRetirementRecommendations(newPlan.plan_id);
        setRecommendations(recResponse.recommendations || []);
      } catch (recErr) {
        console.error('Failed to load recommendations:', recErr);
        setRecommendations([]);
      }
    } catch (err) {
      setError(err.message || 'Failed to create plan');
    } finally {
      setLoading(false);
    }
  };

  const handleScenarioCreated = async (scenarioData) => {
    try {
      setLoading(true);
      const response = await api.createRetirementScenario(scenarioData);
      const newScenario = response.scenario;

      setScenarios([...scenarios, newScenario]);
    } catch (err) {
      setError(err.message || 'Failed to create scenario');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030303] text-white">
      <Sidebar />
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-purple-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-violet-500/15 rounded-full blur-[100px] mix-blend-screen"></div>
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
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-purple-500/50 transition-colors">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-purple-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">RETIREMENT PLANNER</span>
          </button>

          {/* Actions */}
          <div className="flex items-center gap-3">
            {plan && currentView !== 'input' && (
              <button
                onClick={() => { setPlan(null); setScenarios([]); setRecommendations([]); setCurrentView('input'); }}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 hover:border-purple-500/40 transition-all text-xs font-medium text-purple-300"
              >
                <iconify-icon icon="solar:add-circle-linear" width="16"></iconify-icon>
                <span className="hidden md:inline">New Plan</span>
              </button>
            )}
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
      <main className="relative z-10 pt-24 pb-16 px-6 ml-20">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <section className="mb-12">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
              <span className="text-xs text-white/50 font-medium tracking-widest uppercase">Retirement Planning</span>
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
              Retirement <span className="text-gradient">Planning Calculator</span>
            </h1>
            <p className="text-white/50 max-w-2xl">
              Plan your retirement with AI-powered insights and recommendations
            </p>
          </section>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 rounded-lg bg-danger-950/30 border border-danger-500/30 flex items-start gap-3">
              <iconify-icon icon="solar:danger-triangle-linear" className="text-danger-400 mt-0.5 shrink-0"></iconify-icon>
              <div className="flex-1">
                <div className="text-sm text-danger-400">{error}</div>
                <button
                  onClick={() => setError(null)}
                  className="mt-2 text-xs text-danger-400/60 hover:text-danger-400 transition-colors"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="glass-panel rounded-xl p-12 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-500/10 border border-purple-500/20 mb-6 relative">
                <iconify-icon icon="solar:spinner-solid" className="text-purple-400 text-3xl animate-spin"></iconify-icon>
                <div className="absolute inset-0 rounded-full bg-purple-500/20 animate-ping"></div>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Processing Your Plan</h3>
              <p className="text-white/50 text-sm">Calculating your retirement projections...</p>
            </div>
          )}

          {!loading && (
            <>
              {currentView === 'input' && (
                <div className="glass-panel rounded-2xl p-8 border border-white/10">
                  <RetirementInputForm onPlanCreated={handlePlanCreated} />
                </div>
              )}

              {plan && ['dashboard', 'scenarios', 'recommendations'].includes(currentView) && (
                <div className="space-y-6">
                  {/* View Navigation */}
                  <div className="flex gap-3 flex-wrap">
                    <button
                      onClick={() => setCurrentView('dashboard')}
                      className={`px-6 py-3 rounded-lg font-semibold text-sm transition-all flex items-center gap-2 ${
                        currentView === 'dashboard'
                          ? 'bg-gradient-to-r from-purple-500 to-violet-600 text-white shadow-lg shadow-purple-900/30'
                          : 'bg-white/5 text-white/60 hover:bg-white/10 border border-white/10'
                      }`}
                    >
                      <iconify-icon icon="solar:chart-2-linear" width="18"></iconify-icon>
                      Dashboard
                    </button>
                    <button
                      onClick={() => setCurrentView('scenarios')}
                      className={`px-6 py-3 rounded-lg font-semibold text-sm transition-all flex items-center gap-2 ${
                        currentView === 'scenarios'
                          ? 'bg-gradient-to-r from-purple-500 to-violet-600 text-white shadow-lg shadow-purple-900/30'
                          : 'bg-white/5 text-white/60 hover:bg-white/10 border border-white/10'
                      }`}
                    >
                      <iconify-icon icon="solar:layers-linear" width="18"></iconify-icon>
                      Scenarios
                    </button>
                    <button
                      onClick={() => setCurrentView('recommendations')}
                      className={`px-6 py-3 rounded-lg font-semibold text-sm transition-all flex items-center gap-2 ${
                        currentView === 'recommendations'
                          ? 'bg-gradient-to-r from-purple-500 to-violet-600 text-white shadow-lg shadow-purple-900/30'
                          : 'bg-white/5 text-white/60 hover:bg-white/10 border border-white/10'
                      }`}
                    >
                      <iconify-icon icon="solar:lightbulb-linear" width="18"></iconify-icon>
                      Recommendations
                    </button>
                  </div>

                  {/* View Content */}
                  {currentView === 'dashboard' && (
                    <div className="glass-panel rounded-2xl p-8 border border-white/10">
                      <RetirementDashboard plan={plan} />
                    </div>
                  )}

                  {currentView === 'scenarios' && (
                    <div className="glass-panel rounded-2xl p-8 border border-white/10">
                      <ScenarioComparison
                        plan={plan}
                        scenarios={scenarios}
                        onScenarioCreated={handleScenarioCreated}
                      />
                    </div>
                  )}

                  {currentView === 'recommendations' && (
                    <div className="glass-panel rounded-2xl p-8 border border-white/10">
                      <ActionPlanView recommendations={recommendations} plan={plan} />
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-20 border-t border-white/10 bg-black/50 backdrop-blur-md py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-purple-400 text-lg"></iconify-icon>
                <span className="font-display font-bold text-white">SmartFin</span>
                <span className="text-[10px] text-white/30 font-mono">v2.0.4</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
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

export default RetirementPlanner;

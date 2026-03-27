import { useState } from 'react';
import api from '../services/api';

const ScenarioComparison = ({ plan, scenarios, onScenarioCreated }) => {
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    scenario_name: '',
    retirement_age: plan.retirement_age,
    monthly_savings: plan.required_monthly_savings,
    investment_return_rate: plan.investment_return_rate
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const presetScenarios = [
    {
      name: 'Conservative',
      description: 'Lower returns, longer working years',
      retirement_age: Math.min(plan.retirement_age + 5, 75),
      investment_return_rate: 0.08
    },
    {
      name: 'Moderate',
      description: 'Balanced approach',
      retirement_age: plan.retirement_age,
      investment_return_rate: 0.10
    },
    {
      name: 'Aggressive',
      description: 'Higher returns, earlier retirement',
      retirement_age: Math.max(plan.retirement_age - 5, plan.current_age + 1),
      investment_return_rate: 0.12
    }
  ];

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const handlePresetScenario = async (preset) => {
    try {
      setLoading(true);
      setError(null);

      const scenarioData = {
        plan_id: plan.plan_id,
        scenario_name: preset.name,
        retirement_age: preset.retirement_age,
        investment_return_rate: preset.investment_return_rate,
        monthly_savings: plan.required_monthly_savings
      };

      const response = await api.createRetirementScenario(scenarioData);
      onScenarioCreated(response.scenario);
    } catch (err) {
      setError(err.message || 'Failed to create scenario');
    } finally {
      setLoading(false);
    }
  };

  const handleCustomScenario = async (e) => {
    e.preventDefault();

    if (!formData.scenario_name.trim()) {
      setError('Scenario name is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const scenarioData = {
        plan_id: plan.plan_id,
        ...formData
      };

      const response = await api.createRetirementScenario(scenarioData);
      onScenarioCreated(response.scenario);

      setFormData({
        scenario_name: '',
        retirement_age: plan.retirement_age,
        monthly_savings: plan.required_monthly_savings,
        investment_return_rate: plan.investment_return_rate
      });
      setShowForm(false);
    } catch (err) {
      setError(err.message || 'Failed to create scenario');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:layers-linear" className="text-purple-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Scenario Comparison</h2>
          <p className="text-xs text-white/50">Compare different retirement scenarios</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-danger-950/30 border border-danger-500/30 flex items-start gap-3">
          <iconify-icon icon="solar:danger-triangle-linear" className="text-danger-400 mt-0.5 shrink-0"></iconify-icon>
          <div className="text-sm text-danger-400">{error}</div>
        </div>
      )}

      {/* Preset Scenarios */}
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <iconify-icon icon="solar:chart-2-linear" className="text-purple-400"></iconify-icon>
          Preset Scenarios
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {presetScenarios.map((preset) => (
            <button
              key={preset.name}
              onClick={() => handlePresetScenario(preset)}
              disabled={loading}
              className="p-4 border border-white/10 rounded-lg hover:border-purple-500/50 hover:bg-purple-500/5 transition disabled:opacity-50 disabled:cursor-not-allowed text-left"
            >
              <h4 className="font-semibold text-white mb-1">{preset.name}</h4>
              <p className="text-xs text-white/50 mb-3">{preset.description}</p>
              <div className="text-xs text-white/40 space-y-1">
                <p>Retire at: {preset.retirement_age}</p>
                <p>Return: {(preset.investment_return_rate * 100).toFixed(1)}%</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Custom Scenario Form */}
      {!showForm ? (
        <button
          onClick={() => setShowForm(true)}
          className="w-full px-6 py-3 rounded-lg bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700 border border-purple-400/20 transition text-sm font-semibold shadow-lg shadow-purple-900/30 flex items-center justify-center gap-2"
        >
          <iconify-icon icon="solar:add-circle-linear" width="18"></iconify-icon>
          Create Custom Scenario
        </button>
      ) : (
        <div className="glass-panel rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">Create Custom Scenario</h3>
          <form onSubmit={handleCustomScenario} className="space-y-4">
            <div className="space-y-2 group">
              <label className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-purple-400">
                Scenario Name
              </label>
              <input
                type="text"
                value={formData.scenario_name}
                onChange={(e) => setFormData(prev => ({ ...prev, scenario_name: e.target.value }))}
                placeholder="e.g., My Custom Plan"
                className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2 group">
                <label className="text-[10px] uppercase tracking-widest text-white/40 font-medium">
                  Retirement Age
                </label>
                <input
                  type="number"
                  value={formData.retirement_age}
                  onChange={(e) => setFormData(prev => ({ ...prev, retirement_age: parseInt(e.target.value) }))}
                  min={plan.current_age + 1}
                  max="75"
                  className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all"
                />
              </div>

              <div className="space-y-2 group">
                <label className="text-[10px] uppercase tracking-widest text-white/40 font-medium">
                  Monthly Savings (₹)
                </label>
                <input
                  type="number"
                  value={formData.monthly_savings}
                  onChange={(e) => setFormData(prev => ({ ...prev, monthly_savings: parseFloat(e.target.value) }))}
                  min="0"
                  className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all"
                />
              </div>

              <div className="space-y-2 group">
                <label className="text-[10px] uppercase tracking-widest text-white/40 font-medium">
                  Return Rate (%)
                </label>
                <input
                  type="number"
                  value={formData.investment_return_rate * 100}
                  onChange={(e) => setFormData(prev => ({ ...prev, investment_return_rate: parseFloat(e.target.value) / 100 }))}
                  min="5"
                  max="30"
                  step="0.1"
                  className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700 border border-purple-400/20 transition text-sm font-semibold shadow-lg shadow-purple-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating...' : 'Create Scenario'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="flex-1 px-6 py-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition text-sm font-semibold"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Scenarios List */}
      {scenarios.length > 0 && (
        <div className="glass-panel rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <iconify-icon icon="solar:layers-linear" className="text-purple-400"></iconify-icon>
            Your Scenarios
          </h3>
          <div className="space-y-4">
            {scenarios.map((scenario) => (
              <div key={scenario.scenario_id} className="border border-white/10 rounded-lg p-4 hover:border-purple-500/30 transition">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-semibold text-white">{scenario.scenario_name}</h4>
                    <p className="text-xs text-white/50">Retire at {scenario.retirement_age}</p>
                  </div>
                  <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded border border-purple-500/30">
                    {scenario.monthly_savings > plan.required_monthly_savings ? 'Aggressive' : 'Conservative'}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-white/50 mb-1">Corpus Target</p>
                    <p className="font-semibold text-white">{formatCurrency(scenario.retirement_corpus)}</p>
                  </div>
                  <div>
                    <p className="text-white/50 mb-1">Projected Savings</p>
                    <p className="font-semibold text-white">{formatCurrency(scenario.projected_savings)}</p>
                  </div>
                  <div>
                    <p className="text-white/50 mb-1">Gap</p>
                    <p className={`font-semibold ${scenario.gap < 0 ? 'text-green-400' : 'text-danger-400'}`}>
                      {formatCurrency(Math.abs(scenario.gap))}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ScenarioComparison;

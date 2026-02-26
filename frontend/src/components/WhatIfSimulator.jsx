import { useState } from 'react';

const WhatIfSimulator = ({ currentData, onSimulate }) => {
  const [modifiedData, setModifiedData] = useState({
    shopping: currentData?.shopping || 0,
    savings: currentData?.savings || 0
  });

  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setModifiedData(prev => ({
      ...prev,
      [name]: Number(value)
    }));
  };

  const handleSimulate = async () => {
    if (!currentData) return;

    setLoading(true);
    try {
      const result = await onSimulate(currentData, {
        ...currentData,
        shopping: modifiedData.shopping,
        savings: modifiedData.savings
      });
      setSimulationResult(result);
    } catch (error) {
      console.error('Simulation error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!currentData) return null;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:magic-stick-3-linear" className="text-purple-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">What-If Simulator</h2>
          <p className="text-xs text-white/50">Test different scenarios to optimize your finances</p>
        </div>
      </div>
      
      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="space-y-2">
          <label htmlFor="shopping" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
            <iconify-icon icon="solar:bag-smile-linear" width="14" className="text-purple-400"></iconify-icon>
            Shopping & Entertainment
          </label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 text-sm font-mono">₹</span>
            <input
              type="number"
              id="shopping"
              name="shopping"
              value={modifiedData.shopping}
              onChange={handleChange}
              min="0"
              className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-3 pl-8 text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all duration-200 font-mono"
            />
          </div>
          <div className="text-xs text-white/40 font-mono">
            Current: ₹{currentData.shopping?.toLocaleString()}
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="savings" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
            <iconify-icon icon="solar:safe-square-linear" width="14" className="text-green-400"></iconify-icon>
            Monthly Savings
          </label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 text-sm font-mono">₹</span>
            <input
              type="number"
              id="savings"
              name="savings"
              value={modifiedData.savings}
              onChange={handleChange}
              min="0"
              className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-3 pl-8 text-sm text-white placeholder-white/20 focus:outline-none focus:border-green-500/50 focus:ring-1 focus:ring-green-500/50 transition-all duration-200 font-mono"
            />
          </div>
          <div className="text-xs text-white/40 font-mono">
            Current: ₹{currentData.savings?.toLocaleString()}
          </div>
        </div>
      </div>

      <button 
        onClick={handleSimulate}
        disabled={loading}
        className="w-full relative group overflow-hidden rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 py-3 transition-all hover:from-purple-600 hover:to-pink-600 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed mb-6"
      >
        {!loading && (
          <>
            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            <span className="relative text-sm font-semibold text-white flex items-center justify-center gap-2">
              <iconify-icon icon="solar:rocket-2-linear" width="18"></iconify-icon>
              Run Simulation
            </span>
          </>
        )}
        {loading && (
          <div className="flex items-center justify-center text-white gap-2">
            <iconify-icon icon="solar:spinner-solid" className="animate-spin text-lg"></iconify-icon>
            <span className="text-sm font-semibold">Simulating...</span>
          </div>
        )}
      </button>

      {/* Results */}
      {simulationResult && (
        <div className="space-y-6 p-6 rounded-lg border border-white/10 bg-white/5 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-4">
            <iconify-icon icon="solar:chart-2-linear" className="text-cyan-400" width="20"></iconify-icon>
            <h3 className="text-lg font-semibold text-white">Simulation Results</h3>
          </div>
          
          {/* Score Comparison */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 rounded-lg bg-white/5 border border-white/10">
              <div className="text-xs text-white/50 mb-2">Current Score</div>
              <div className="text-3xl font-bold text-white font-mono">
                {simulationResult.current_score?.toFixed(1)}
              </div>
            </div>

            <div className="flex flex-col items-center justify-center p-4 rounded-lg bg-white/5 border border-white/10">
              <div 
                className="text-4xl mb-2"
              >
                {simulationResult.impact === 'positive' ? '↗️' : 
                 simulationResult.impact === 'negative' ? '↘️' : '➡️'}
              </div>
              <div 
                className={`text-lg font-bold font-mono ${
                  simulationResult.impact === 'positive' ? 'text-green-400' :
                  simulationResult.impact === 'negative' ? 'text-red-400' :
                  'text-white/60'
                }`}
              >
                {simulationResult.score_change > 0 ? '+' : ''}
                {simulationResult.score_change?.toFixed(1)}
              </div>
            </div>

            <div className="text-center p-4 rounded-lg bg-white/5 border border-white/10">
              <div className="text-xs text-white/50 mb-2">New Score</div>
              <div 
                className="text-3xl font-bold font-mono"
                style={{ color: simulationResult.modified_classification?.color }}
              >
                {simulationResult.modified_score?.toFixed(1)}
              </div>
            </div>
          </div>

          {/* Classification Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-white/10">
            <div>
              <div className="text-xs text-white/40 mb-2">Current Status</div>
              <div 
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full border backdrop-blur-sm"
                style={{ 
                  backgroundColor: `${simulationResult.current_classification?.color}10`,
                  borderColor: `${simulationResult.current_classification?.color}30`,
                  color: simulationResult.current_classification?.color 
                }}
              >
                <span className="text-lg">{simulationResult.current_classification?.emoji}</span>
                <span className="font-semibold text-sm">{simulationResult.current_classification?.category}</span>
              </div>
            </div>

            <div>
              <div className="text-xs text-white/40 mb-2">After Changes</div>
              <div 
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full border backdrop-blur-sm"
                style={{ 
                  backgroundColor: `${simulationResult.modified_classification?.color}10`,
                  borderColor: `${simulationResult.modified_classification?.color}30`,
                  color: simulationResult.modified_classification?.color 
                }}
              >
                <span className="text-lg">{simulationResult.modified_classification?.emoji}</span>
                <span className="font-semibold text-sm">{simulationResult.modified_classification?.category}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WhatIfSimulator;

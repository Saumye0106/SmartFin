const InvestmentAdvice = ({ investments }) => {
  if (!investments) return null;

  const getRiskConfig = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return { color: '#10b981', icon: 'solar:shield-check-linear' };
      case 'medium':
        return { color: '#eab308', icon: 'solar:shield-linear' };
      case 'high':
        return { color: '#ef4444', icon: 'solar:shield-warning-linear' };
      default:
        return { color: '#06b6d4', icon: 'solar:shield-linear' };
    }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:chart-square-linear" className="text-green-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Investment Recommendations</h2>
          <p className="text-xs text-white/50">Smart investment strategies for your profile</p>
        </div>
      </div>
      
      <div className="space-y-6">
        {/* Eligibility Status */}
        <div 
          className="flex items-center gap-3 p-4 rounded-lg border backdrop-blur-sm"
          style={{
            backgroundColor: investments.eligible ? 'rgba(16, 185, 129, 0.1)' : 'rgba(249, 115, 22, 0.1)',
            borderColor: investments.eligible ? 'rgba(16, 185, 129, 0.3)' : 'rgba(249, 115, 22, 0.3)'
          }}
        >
          <iconify-icon 
            icon={investments.eligible ? 'solar:check-circle-bold' : 'solar:close-circle-bold'}
            className={investments.eligible ? 'text-green-400' : 'text-orange-400'}
            width="24"
          ></iconify-icon>
          <span className={`font-semibold ${investments.eligible ? 'text-green-400' : 'text-orange-400'}`}>
            {investments.eligible ? 'Ready to Invest' : 'Not Ready Yet'}
          </span>
        </div>

        {/* Message */}
        <p className="text-sm text-white/70 leading-relaxed">
          {investments.message}
        </p>

        {/* Investment Suggestions */}
        {investments.suggestions && investments.suggestions.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <iconify-icon icon="solar:star-linear" className="text-cyan-400" width="16"></iconify-icon>
              Recommended Investments
            </h3>
            <div className="space-y-3">
              {investments.suggestions.map((suggestion, index) => {
                const riskConfig = getRiskConfig(suggestion.risk_level);
                
                return (
                  <div 
                    key={index}
                    className="p-4 rounded-lg border border-white/10 bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-all"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <iconify-icon icon="solar:wallet-linear" className="text-cyan-400" width="18"></iconify-icon>
                        <span className="font-semibold text-white">{suggestion.type}</span>
                      </div>
                      {suggestion.risk_level && (
                        <div 
                          className="flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium"
                          style={{
                            backgroundColor: `${riskConfig.color}20`,
                            color: riskConfig.color
                          }}
                        >
                          <iconify-icon icon={riskConfig.icon} width="12"></iconify-icon>
                          {suggestion.risk_level}
                        </div>
                      )}
                    </div>
                    
                    {suggestion.allocation && (
                      <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/10">
                        <span className="text-xs text-white/50">Suggested Amount</span>
                        <span className="text-sm font-semibold text-white font-mono">
                          ₹{suggestion.allocation.toLocaleString()}
                        </span>
                      </div>
                    )}
                    
                    {suggestion.description && (
                      <p className="text-xs text-white/60 leading-relaxed">
                        {suggestion.description}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Pro Tip */}
        {investments.advice && (
          <div className="p-4 rounded-lg border border-cyan-500/30 bg-cyan-950/20 backdrop-blur-sm">
            <div className="flex items-start gap-3">
              <iconify-icon icon="solar:lightbulb-bolt-linear" className="text-cyan-400 shrink-0" width="20"></iconify-icon>
              <div>
                <div className="text-xs font-semibold text-cyan-400 mb-1">Pro Tip</div>
                <p className="text-sm text-white/70 leading-relaxed">{investments.advice}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InvestmentAdvice;

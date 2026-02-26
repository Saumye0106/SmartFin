const AlertsPanel = ({ anomalies }) => {
  if (!anomalies || anomalies.length === 0) return null;

  const getSeverityConfig = (severity) => {
    switch (severity) {
      case 'critical':
        return {
          icon: 'solar:danger-triangle-bold',
          color: '#ef4444',
          bgColor: 'rgba(239, 68, 68, 0.1)',
          borderColor: 'rgba(239, 68, 68, 0.3)'
        };
      case 'high':
        return {
          icon: 'solar:shield-warning-linear',
          color: '#f97316',
          bgColor: 'rgba(249, 115, 22, 0.1)',
          borderColor: 'rgba(249, 115, 22, 0.3)'
        };
      case 'medium':
        return {
          icon: 'solar:bolt-circle-linear',
          color: '#eab308',
          bgColor: 'rgba(234, 179, 8, 0.1)',
          borderColor: 'rgba(234, 179, 8, 0.3)'
        };
      case 'low':
        return {
          icon: 'solar:info-circle-linear',
          color: '#06b6d4',
          bgColor: 'rgba(6, 182, 212, 0.1)',
          borderColor: 'rgba(6, 182, 212, 0.3)'
        };
      default:
        return {
          icon: 'solar:info-circle-linear',
          color: '#06b6d4',
          bgColor: 'rgba(6, 182, 212, 0.1)',
          borderColor: 'rgba(6, 182, 212, 0.3)'
        };
    }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:bell-bing-linear" className="text-red-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Risk Alerts & Anomalies</h2>
          <p className="text-xs text-white/50">Important notifications about your finances</p>
        </div>
      </div>
      
      <div className="space-y-3">
        {anomalies.map((anomaly, index) => {
          const config = getSeverityConfig(anomaly.severity);
          
          return (
            <div 
              key={index} 
              className="flex items-start gap-4 p-4 rounded-lg border backdrop-blur-sm transition-all hover:bg-white/5"
              style={{
                backgroundColor: config.bgColor,
                borderColor: config.borderColor
              }}
            >
              <div 
                className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                style={{
                  backgroundColor: config.bgColor,
                  border: `1px solid ${config.borderColor}`
                }}
              >
                <iconify-icon icon={config.icon} style={{ color: config.color }} width="20"></iconify-icon>
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span 
                    className="text-[10px] uppercase tracking-widest font-semibold"
                    style={{ color: config.color }}
                  >
                    {anomaly.severity}
                  </span>
                </div>
                <p className="text-sm text-white/80 leading-relaxed">
                  {anomaly.message}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AlertsPanel;

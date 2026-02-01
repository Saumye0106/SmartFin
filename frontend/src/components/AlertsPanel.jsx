import './AlertsPanel.css';

const AlertsPanel = ({ anomalies }) => {
  if (!anomalies || anomalies.length === 0) return null;

  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'critical': return 'alert-critical';
      case 'high': return 'alert-high';
      case 'medium': return 'alert-medium';
      case 'low': return 'alert-low';
      default: return 'alert-low';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '⚡';
      case 'low': return 'ℹ️';
      default: return 'ℹ️';
    }
  };

  return (
    <div className="alerts-panel-container">
      <h2 className="section-title">🔔 Risk Alerts & Anomalies</h2>
      
      <div className="alerts-list">
        {anomalies.map((anomaly, index) => (
          <div key={index} className={`alert-card ${getSeverityClass(anomaly.severity)}`}>
            <div className="alert-icon">{getSeverityIcon(anomaly.severity)}</div>
            <div className="alert-content">
              <div className="alert-severity">{anomaly.severity.toUpperCase()}</div>
              <div className="alert-message">{anomaly.message}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsPanel;

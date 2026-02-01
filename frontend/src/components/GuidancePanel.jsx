import './GuidancePanel.css';

const GuidancePanel = ({ guidance }) => {
  if (!guidance) return null;

  const { strengths, warnings, recommendations } = guidance;

  return (
    <div className="guidance-panel-container">
      <h2 className="section-title">💡 Personalized Guidance</h2>
      
      <div className="guidance-grid">
        {strengths && strengths.length > 0 && (
          <div className="guidance-section">
            <h3 className="guidance-heading strengths-heading">✅ Strengths</h3>
            <div className="guidance-list">
              {strengths.map((item, index) => (
                <div key={index} className="guidance-item strengths-item">
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}

        {warnings && warnings.length > 0 && (
          <div className="guidance-section">
            <h3 className="guidance-heading warnings-heading">⚠️ Warnings</h3>
            <div className="guidance-list">
              {warnings.map((item, index) => (
                <div key={index} className="guidance-item warnings-item">
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}

        {recommendations && recommendations.length > 0 && (
          <div className="guidance-section">
            <h3 className="guidance-heading recommendations-heading">🎯 Recommendations</h3>
            <div className="guidance-list">
              {recommendations.map((item, index) => (
                <div key={index} className="guidance-item recommendations-item">
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GuidancePanel;

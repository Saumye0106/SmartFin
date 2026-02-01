import './InvestmentAdvice.css';

const InvestmentAdvice = ({ investments }) => {
  if (!investments) return null;

  return (
    <div className="investment-advice-container">
      <h2 className="section-title">💼 Investment Recommendations</h2>
      
      <div className="investment-content">
        <div className={`eligibility-badge ${investments.eligible ? 'eligible' : 'not-eligible'}`}>
          {investments.eligible ? '✅ Ready to Invest' : '⚠️ Not Ready Yet'}
        </div>

        <p className="investment-message">{investments.message}</p>

        {investments.suggestions && investments.suggestions.length > 0 && (
          <div className="suggestions-section">
            <h3 className="suggestions-title">Recommended Investments:</h3>
            <div className="suggestions-grid">
              {investments.suggestions.map((suggestion, index) => (
                <div key={index} className="suggestion-card">
                  <div className="suggestion-header">
                    <span className="suggestion-type">{suggestion.type}</span>
                    {suggestion.risk_level && (
                      <span className={`risk-badge risk-${suggestion.risk_level.toLowerCase()}`}>
                        {suggestion.risk_level}
                      </span>
                    )}
                  </div>
                  <div className="suggestion-details">
                    {suggestion.allocation && (
                      <div className="allocation">
                        <span className="allocation-label">Suggested Amount:</span>
                        <span className="allocation-value">₹{suggestion.allocation.toLocaleString()}</span>
                      </div>
                    )}
                    {suggestion.description && (
                      <p className="suggestion-description">{suggestion.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {investments.advice && (
          <div className="advice-box">
            <strong>💡 Pro Tip:</strong> {investments.advice}
          </div>
        )}
      </div>
    </div>
  );
};

export default InvestmentAdvice;

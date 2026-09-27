import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './PortfolioOptimizer.css';

// ── Color palette for asset classes ─────────────────────────────────────────
const ASSET_COLORS = {
  'Large-Cap Equity': '#7c3aed',
  'Mid-Cap Equity': '#a855f7',
  'Short-Term Debt': '#3b82f6',
  'Gold': '#f59e0b',
  'FD / Cash': '#10b981',
};

const CAT_COLORS = {
  'Equity': '#7c3aed',
  'Debt': '#3b82f6',
  'Gold': '#f59e0b',
  'FD / Cash': '#10b981',
};

const RISK_LABELS = {
  1: 'Ultra Conservative', 2: 'Conservative', 3: 'Conservative',
  4: 'Moderate', 5: 'Moderate', 6: 'Moderate',
  7: 'Aggressive', 8: 'Aggressive', 9: 'Very Aggressive', 10: 'Ultra Aggressive',
};

const RISK_CLASS = (r) =>
  r <= 3 ? 'conservative' : r <= 6 ? 'moderate' : 'aggressive';

const ADJUSTMENT_LABELS = {
  high_emi_reduced_equity: '🏦 High EMI — equity reduced',
  moderate_emi_reduced_midcap: '📉 Moderate EMI — mid-cap trimmed',
  multiple_loans_liquidity_buffer: '💧 Multiple loans — liquidity added',
  low_savings_rate_conservative_shift: '⚠️ Low savings — conservative shift',
};

function getLabel(key) {
  // Handle dynamic keys like "short_term_goal_5mo_shifted_debt"
  if (key.startsWith('short_term_goal'))
    return `🎯 Short-term goal — shifted to debt`;
  if (key.startsWith('medium_term_goal'))
    return `🎯 Medium-term goal — debt tilt`;
  return ADJUSTMENT_LABELS[key] || key.replaceAll('_', ' ');
}

// ── DonutChart (pure SVG, no library needed) ─────────────────────────────────
function DonutChart({ data, size = 180, centerLabel, centerValue }) {
  const radius = size * 0.38;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * radius;
  let cumulativePct = 0;

  const slices = data.map(({ label, pct, color }) => {
    const dash = (pct / 100) * circumference;
    const offset = circumference - cumulativePct * circumference / 100;
    cumulativePct += pct;
    return { label, pct, color, dash, offset };
  });

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
        {slices.map(({ label, pct, color, dash, offset }) => (
          <circle
            key={label}
            cx={cx} cy={cy}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={size * 0.12}
            strokeDasharray={`${dash} ${circumference}`}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dasharray 0.8s cubic-bezier(0.4,0,0.2,1)' }}
          />
        ))}
      </svg>
      <div className="donut-center-text">
        <span className="return-val">{centerValue}</span>
        <span className="return-label">{centerLabel}</span>
      </div>
    </div>
  );
}

// ── FrontierChart (pure SVG scatter) ─────────────────────────────────────────
function FrontierChart({ points, special }) {
  if (!points || points.length === 0) return null;

  const W = 500, H = 220, PAD = 40;
  const risks = points.map(p => p.risk);
  const returns = points.map(p => p.return);
  const minR = Math.min(...risks), maxR = Math.max(...risks);
  const minM = Math.min(...returns), maxM = Math.max(...returns);

  const sx = (r) => PAD + ((r - minR) / (maxR - minR + 1e-9)) * (W - 2 * PAD);
  const sy = (m) => H - PAD - ((m - minM) / (maxM - minM + 1e-9)) * (H - 2 * PAD);

  const pathD = points.map((p, i) =>
    `${i === 0 ? 'M' : 'L'}${sx(p.risk).toFixed(1)},${sy(p.return).toFixed(1)}`
  ).join(' ');

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: '100%' }}>
      <defs>
        <linearGradient id="frontierGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#34d399" />
          <stop offset="50%" stopColor="#f59e0b" />
          <stop offset="100%" stopColor="#ef4444" />
        </linearGradient>
      </defs>

      {/* Axes */}
      <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD}
        stroke="rgba(255,255,255,0.1)" strokeWidth={1} />
      <line x1={PAD} y1={PAD} x2={PAD} y2={H - PAD}
        stroke="rgba(255,255,255,0.1)" strokeWidth={1} />

      {/* Axis labels */}
      <text x={W / 2} y={H - 4} fill="rgba(255,255,255,0.35)" fontSize="10" textAnchor="middle">
        Risk (Annual Volatility)
      </text>
      <text x={10} y={H / 2} fill="rgba(255,255,255,0.35)" fontSize="10"
        textAnchor="middle" transform={`rotate(-90, 10, ${H / 2})`}>
        Return
      </text>

      {/* Frontier line */}
      <path d={pathD} fill="none" stroke="url(#frontierGrad)" strokeWidth={2.5}
        style={{ opacity: 0.85 }} />

      {/* Frontier dots */}
      {points.filter((_, i) => i % 5 === 0).map((p, i) => (
        <circle key={i} cx={sx(p.risk)} cy={sy(p.return)} r={3}
          fill="rgba(255,255,255,0.2)" stroke="rgba(255,255,255,0.4)" strokeWidth={1} />
      ))}

      {/* Special portfolios */}
      {special && Object.entries(special).map(([key, sp]) => (
        <g key={key}>
          <circle cx={sx(sp.risk)} cy={sy(sp.return)} r={7}
            fill={key === 'gmv' ? '#34d399' : '#f59e0b'}
            stroke="#fff" strokeWidth={2} />
          <text x={sx(sp.risk) + 10} y={sy(sp.return) + 4}
            fill="rgba(255,255,255,0.7)" fontSize="9.5">
            {sp.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function PortfolioOptimizer() {
  const navigate = useNavigate();
  const [riskScore, setRiskScore] = useState(5);
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [portfolio, setPortfolio] = useState(null);
  const [frontier, setFrontier] = useState(null);
  const [modelMeta, setModelMeta] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loadingFrontier, setLoadingFrontier] = useState(false);

  // Load model info on mount
  useEffect(() => {
    api.get('/api/portfolio/model-info')
      .then(r => setModelMeta(r.data?.metadata || null))
      .catch(() => { });
  }, []);

  const handleOptimize = async () => {
    if (!amount || isNaN(amount) || Number(amount) <= 0) {
      setError('Please enter a valid investment amount.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/api/portfolio/optimize', {
        risk_score: riskScore,
        investable_amount: Number(amount),
      });
      if (res.data.success) {
        setPortfolio(res.data);
        setActiveTab('overview');
        // Also fetch frontier
        loadFrontier();
      } else {
        setError(res.data.error || 'Optimization failed.');
      }
    } catch (e) {
      setError(e.message || 'Network error. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const loadFrontier = async () => {
    setLoadingFrontier(true);
    try {
      const res = await api.get('/api/portfolio/frontier');
      if (res.data.success) setFrontier(res.data);
    } catch (_) { }
    setLoadingFrontier(false);
  };

  // ── Derived data ──────────────────────────────────────────────────────
  const allocs = portfolio?.portfolio?.allocations || [];
  const catWeights = portfolio?.portfolio?.category_weights || {};
  const projections = portfolio?.portfolio?.projected_returns || {};
  const applied = portfolio?.portfolio?.applied_adjustments || [];
  const expRet = portfolio?.portfolio?.expected_return_pct || 0;
  const riskPct = portfolio?.portfolio?.risk_pct || 0;
  const sharpe = portfolio?.portfolio?.sharpe_ratio || 0;

  const donutData = Object.entries(catWeights).map(([cat, pct]) => ({
    label: cat, pct, color: CAT_COLORS[cat] || '#888',
  }));

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div className="portfolio-page">
      <button
        onClick={() => navigate('/dashboard')}
        style={{
          background: 'rgba(255,255,255,0.06)',
          border: '1px solid rgba(255,255,255,0.1)',
          color: 'rgba(255,255,255,0.6)',
          borderRadius: '0.625rem',
          padding: '0.4rem 0.9rem',
          cursor: 'pointer',
          fontSize: '0.8rem',
          marginBottom: '1.25rem',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
        }}
      >
        ← Back
      </button>

      <div className="portfolio-header">
        <h1>📊 Portfolio Optimizer</h1>
        <p>
          Markowitz Mean-Variance Optimization + XGBoost Return Prediction —
          personalized to your risk profile, goals & loans.
        </p>
      </div>

      <div className="portfolio-grid">
        {/* ── Left: Input Panel ─────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* Input Card */}
          <div className="portfolio-card">
            <h2>⚙️ Configure Portfolio</h2>

            <div className="input-field-group">
              <label>Monthly Investable Amount (₹)</label>
              <input
                id="portfolio-amount"
                type="number"
                placeholder="e.g. 25000"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                min="100"
              />
            </div>

            <div className="risk-slider-wrap">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                <label style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Risk Tolerance
                </label>
                <span style={{ fontSize: '0.8rem', color: '#a78bfa', fontWeight: 700 }}>
                  {riskScore}/10
                </span>
              </div>
              <div className="risk-slider-labels">
                <span>Conservative</span>
                <span>Moderate</span>
                <span>Aggressive</span>
              </div>
              <input
                id="portfolio-risk-slider"
                type="range"
                min={1} max={10} step={1}
                value={riskScore}
                onChange={e => setRiskScore(Number(e.target.value))}
                className="risk-slider"
              />
              <div>
                <span className={`risk-badge ${RISK_CLASS(riskScore)}`}>
                  {riskScore <= 3 ? '🛡️' : riskScore <= 6 ? '⚖️' : '🚀'} {RISK_LABELS[riskScore]}
                </span>
              </div>
            </div>

            <div style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.35)', marginBottom: '1rem', lineHeight: 1.5 }}>
              Your risk profile, active loans and financial goals will be used to
              automatically personalize the allocation.
            </div>

            {error && (
              <div style={{
                background: 'rgba(239,68,68,0.12)',
                border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: '0.75rem',
                padding: '0.75rem',
                color: '#fca5a5',
                fontSize: '0.82rem',
                marginBottom: '0.75rem',
              }}>
                ⚠️ {error}
              </div>
            )}

            <button
              id="portfolio-optimize-btn"
              className="optimize-btn"
              onClick={handleOptimize}
              disabled={loading}
            >
              {loading
                ? <><iconify-icon icon="svg-spinners:ring-resize" width="18"></iconify-icon> Optimizing...</>
                : <><iconify-icon icon="solar:chart-2-linear" width="18"></iconify-icon> Optimize Portfolio</>
              }
            </button>
          </div>

          {/* Model Info Card */}
          <div className="portfolio-card">
            <h2>🤖 ML Model Info</h2>
            {modelMeta ? (
              <>
                <div className="model-info-grid">
                  <div className="model-metric">
                    <div className="mm-label">Algorithm</div>
                    <div className="mm-value">{modelMeta.algorithm}</div>
                  </div>
                  <div className="model-metric">
                    <div className="mm-label">Avg R²</div>
                    <div className="mm-value">{(modelMeta.overall_r2 * 100).toFixed(1)}%</div>
                  </div>
                  <div className="model-metric">
                    <div className="mm-label">Assets Modeled</div>
                    <div className="mm-value">{modelMeta.n_assets}</div>
                  </div>
                  <div className="model-metric">
                    <div className="mm-label">CV Strategy</div>
                    <div className="mm-value" style={{ fontSize: '0.8rem' }}>{modelMeta.cv_strategy?.split('(')[0]}</div>
                  </div>
                </div>

                {modelMeta.top_features?.length > 0 && (
                  <>
                    <div style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.4)', marginBottom: '0.75rem', marginTop: '0.5rem' }}>
                      TOP PREDICTIVE FEATURES
                    </div>
                    {modelMeta.top_features.slice(0, 5).map(({ feature, importance }) => (
                      <div key={feature} className="feature-bar-item">
                        <div className="feature-bar-label" title={feature}>
                          {feature.replace(/_/g, ' ')}
                        </div>
                        <div className="feature-bar-track">
                          <div
                            className="feature-bar-fill"
                            style={{ width: `${(importance * 100).toFixed(1)}%` }}
                          />
                        </div>
                        <div className="feature-bar-pct">
                          {(importance * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </>
            ) : (
              <div style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.85rem' }}>
                Model not trained yet. Run <code>python portfolio_optimizer/train_model.py</code> in the backend.
              </div>
            )}
          </div>
        </div>

        {/* ── Right: Results ────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {!portfolio ? (
            <div className="portfolio-card" style={{ minHeight: 400 }}>
              <div className="portfolio-empty">
                <div className="empty-icon">📊</div>
                <h3>Your optimized portfolio will appear here</h3>
                <p>
                  Set your investable amount and risk score, then click
                  "Optimize Portfolio" to get your personalized ML-powered allocation.
                </p>
              </div>
            </div>
          ) : (
            <>
              {/* Stats row */}
              <div className="portfolio-stats-row">
                <div className="stat-chip">
                  <span className="chip-label">Expected Return</span>
                  <span className="chip-value" style={{ color: '#34d399' }}>
                    {expRet.toFixed(1)}% / yr
                  </span>
                </div>
                <div className="stat-chip">
                  <span className="chip-label">Volatility</span>
                  <span className="chip-value" style={{ color: '#f59e0b' }}>
                    {riskPct.toFixed(1)}%
                  </span>
                </div>
                <div className="stat-chip">
                  <span className="chip-label">Sharpe Ratio</span>
                  <span className="chip-value" style={{ color: '#a78bfa' }}>
                    {sharpe.toFixed(2)}
                  </span>
                </div>
                <div className="stat-chip">
                  <span className="chip-label">Engine</span>
                  <span className="chip-value" style={{ fontSize: '0.85rem' }}>
                    {portfolio.engine === 'ml_predicted' ? '🤖 ML' : '📈 Historical'}
                  </span>
                </div>
              </div>

              {/* Personalization chips */}
              {applied.length > 0 && (
                <div style={{ marginTop: '-0.5rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    PERSONALIZATION APPLIED
                  </div>
                  <div className="personalization-chips">
                    {applied.map(a => (
                      <span key={a} className="personalization-chip">✓ {getLabel(a)}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Tabs */}
              <div className="portfolio-tabs">
                {['overview', 'breakdown', 'frontier', 'whatif'].map(t => (
                  <button
                    key={t}
                    className={`tab-btn ${activeTab === t ? 'active' : ''}`}
                    onClick={() => {
                      setActiveTab(t);
                      if (t === 'frontier' && !frontier) loadFrontier();
                    }}
                  >
                    {t === 'overview' ? '🍩 Overview' : t === 'breakdown' ? '📋 Breakdown' : t === 'frontier' ? '📈 Frontier' : '🔀 What-If'}
                  </button>
                ))}
              </div>

              {/* ── Overview Tab ──── */}
              {activeTab === 'overview' && (
                <>
                  <div className="portfolio-card">
                    <h2>🍩 Asset Allocation</h2>
                    <div className="allocation-donut-wrap">
                      <div className="donut-svg-wrap">
                        <DonutChart
                          data={donutData}
                          size={180}
                          centerValue={`${expRet.toFixed(1)}%`}
                          centerLabel="Exp. Return"
                        />
                      </div>
                      <div className="allocation-legend">
                        {donutData.map(({ label, pct, color }) => (
                          <div key={label} className="legend-item">
                            <div className="legend-dot" style={{ background: color }} />
                            <span className="legend-item-label">{label}</span>
                            <span className="legend-item-pct">{pct.toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="portfolio-card">
                    <h2>📅 Projected Returns</h2>
                    <div className="projections-grid">
                      {[['1yr', '1 Year'], ['3yr', '3 Years'], ['5yr', '5 Years'], ['10yr', '10 Years']].map(([key, label]) => (
                        projections[key] != null && (
                          <div key={key} className="projection-box">
                            <div className="proj-horizon">{label}</div>
                            <div className="proj-return">+{(projections[key] * 100).toFixed(1)}%</div>
                            <div className="proj-label">
                              ₹{((1 + projections[key]) * Number(amount) / 1000).toFixed(0)}k
                            </div>
                          </div>
                        )
                      ))}
                    </div>
                    <div style={{ marginTop: '0.75rem', fontSize: '0.72rem', color: 'rgba(255,255,255,0.3)' }}>
                      * Projections assume constant monthly investment of ₹{Number(amount).toLocaleString('en-IN')} and
                      a fixed return of {expRet.toFixed(1)}% p.a. Actual returns may vary.
                    </div>
                  </div>
                </>
              )}

              {/* ── Breakdown Tab ── */}
              {activeTab === 'breakdown' && (
                <div className="portfolio-card">
                  <h2>📋 Asset Breakdown</h2>
                  <table className="asset-table">
                    <thead>
                      <tr>
                        <th>Asset Class</th>
                        <th>Category</th>
                        <th>Allocation</th>
                        <th className="weight-bar-cell">Weight</th>
                        <th>Amount (₹)</th>
                        <th>Exp. Return</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allocs.sort((a, b) => b.weight - a.weight).map(alloc => (
                        <tr key={alloc.asset}>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <div style={{
                                width: 8, height: 8, borderRadius: '50%',
                                background: ASSET_COLORS[alloc.display_name] || '#888',
                                flexShrink: 0,
                              }} />
                              {alloc.display_name}
                            </div>
                          </td>
                          <td style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.78rem' }}>
                            {alloc.category}
                          </td>
                          <td style={{ fontWeight: 600 }}>{alloc.weight_pct.toFixed(1)}%</td>
                          <td className="weight-bar-cell">
                            <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 99, height: 6, overflow: 'hidden' }}>
                              <div
                                className="asset-weight-bar"
                                style={{
                                  width: `${alloc.weight_pct}%`,
                                  background: ASSET_COLORS[alloc.display_name] || '#7c3aed',
                                }}
                              />
                            </div>
                          </td>
                          <td>₹{(alloc.amount_inr || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                          <td style={{ color: '#34d399' }}>
                            {(alloc.expected_return_annual * 100).toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* ── Frontier Tab ─── */}
              {activeTab === 'frontier' && (
                <div className="portfolio-card">
                  <h2>📈 Efficient Frontier</h2>
                  <p style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.4)', marginBottom: '1.25rem' }}>
                    The efficient frontier shows all optimal portfolios — no other allocation
                    gives higher return for the same risk level. Your portfolio (Risk {riskScore}/10) is
                    on this curve.
                  </p>
                  <div className="frontier-chart-wrap">
                    {loadingFrontier ? (
                      <div className="portfolio-loading">
                        <iconify-icon icon="svg-spinners:ring-resize" width="36"></iconify-icon>
                        <span>Computing frontier...</span>
                      </div>
                    ) : frontier ? (
                      <FrontierChart
                        points={frontier.frontier}
                        special={frontier.special_portfolios}
                      />
                    ) : (
                      <div className="portfolio-empty">
                        <p>Frontier data unavailable</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ── What-If Tab ──── */}
              {activeTab === 'whatif' && (
                <WhatIfPanel amount={Number(amount)} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── What-If Sub-Panel ──────────────────────────────────────────────────────
function WhatIfPanel({ amount }) {
  const [scenarios, setScenarios] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/api/portfolio/whatif', {
        investable_amount: amount,
        scenarios: [
          { name: 'Conservative', risk_score: 3 },
          { name: 'Moderate', risk_score: 5 },
          { name: 'Aggressive', risk_score: 8 },
        ],
      });
      if (res.data.success) setScenarios(res.data.scenarios);
      else setError(res.data.error);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, []);

  if (loading) return (
    <div className="portfolio-card">
      <div className="portfolio-loading">
        <iconify-icon icon="svg-spinners:ring-resize" width="36"></iconify-icon>
        <span>Running scenarios...</span>
      </div>
    </div>
  );

  if (error) return (
    <div className="portfolio-card">
      <div style={{ color: '#fca5a5', fontSize: '0.85rem' }}>⚠️ {error}</div>
    </div>
  );

  if (!scenarios) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {scenarios.map(sc => {
        const p = sc.portfolio;
        const cats = p.category_weights || {};
        const ret = p.expected_return_pct || 0;
        const risk = p.risk_pct || 0;
        const sharpe = p.sharpe_ratio || 0;

        return (
          <div key={sc.name} className="portfolio-card">
            <h2>
              {sc.name === 'Conservative' ? '🛡️' : sc.name === 'Moderate' ? '⚖️' : '🚀'} {sc.name}
              <span style={{ marginLeft: 'auto', fontSize: '0.78rem', color: 'rgba(255,255,255,0.4)', fontWeight: 400 }}>
                Risk Score {sc.risk_score}/10
              </span>
            </h2>

            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <div className="stat-chip">
                <span className="chip-label">Return</span>
                <span className="chip-value" style={{ color: '#34d399', fontSize: '0.95rem' }}>{ret.toFixed(1)}%</span>
              </div>
              <div className="stat-chip">
                <span className="chip-label">Risk</span>
                <span className="chip-value" style={{ color: '#f59e0b', fontSize: '0.95rem' }}>{risk.toFixed(1)}%</span>
              </div>
              <div className="stat-chip">
                <span className="chip-label">Sharpe</span>
                <span className="chip-value" style={{ color: '#a78bfa', fontSize: '0.95rem' }}>{sharpe.toFixed(2)}</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {Object.entries(cats).map(([cat, pct]) => (
                <div key={cat} style={{
                  background: `${CAT_COLORS[cat] || '#888'}22`,
                  border: `1px solid ${CAT_COLORS[cat] || '#888'}44`,
                  borderRadius: '0.5rem',
                  padding: '0.3rem 0.7rem',
                  fontSize: '0.78rem',
                  color: CAT_COLORS[cat] || '#ccc',
                  fontWeight: 600,
                }}>
                  {cat}: {pct.toFixed(1)}%
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

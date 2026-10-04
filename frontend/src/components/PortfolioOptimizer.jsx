import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Sidebar from './Sidebar';
import SmartFinFooter from './SmartFinFooter';
import './PortfolioOptimizer.css';

// ── Color palette for asset classes ─────────────────────────────────────────
const ASSET_COLORS = {
  'Large-Cap Equity': '#f97316',
  'Mid-Cap Equity': '#fb923c',
  'Small-Cap Equity': '#fdba74',
  'International Equity (Nasdaq 100)': '#fb7185',
  'Short-Term Debt': '#38bdf8',
  'Gold': '#facc15',
  'Silver': '#94a3b8',
  'REIT (Real Estate)': '#2dd4bf',
  'FD / Cash': '#a3e635',
  'Fixed Deposit': '#a3e635',
};

const CAT_COLORS = {
  'Equity': '#f97316',
  'Debt': '#38bdf8',
  'Precious Metals': '#facc15',
  'Real Estate': '#2dd4bf',
  'Gold': '#facc15',
  'FD / Cash': '#a3e635',
};

const RISK_LABELS = {
  1: 'Ultra Conservative', 2: 'Conservative', 3: 'Conservative',
  4: 'Moderate', 5: 'Moderate', 6: 'Moderate',
  7: 'Aggressive', 8: 'Aggressive', 9: 'Very Aggressive', 10: 'Ultra Aggressive',
};

const RISK_CLASS = (r) =>
  r <= 3 ? 'conservative' : r <= 6 ? 'moderate' : 'aggressive';

const ADJUSTMENT_LABELS = {
  high_emi_reduced_equity: 'High EMI — equity reduced',
  moderate_emi_reduced_midcap: 'Moderate EMI — mid-cap trimmed',
  multiple_loans_liquidity_buffer: 'Multiple loans — liquidity added',
  low_savings_rate_conservative_shift: 'Low savings — conservative shift',
};

function getLabel(key) {
  // Handle dynamic keys like "short_term_goal_5mo_shifted_debt"
  if (key.startsWith('short_term_goal'))
    return `Short-term goal — shifted to debt`;
  if (key.startsWith('medium_term_goal'))
    return `Medium-term goal — debt tilt`;
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
    const offset = -(cumulativePct / 100) * circumference;
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
            strokeDasharray={`${dash} ${circumference - dash}`}
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
          <stop offset="0%" stopColor="#fde68a" />
          <stop offset="50%" stopColor="#f59e0b" />
          <stop offset="100%" stopColor="#ea580c" />
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
            fill={key === 'gmv' ? '#fde68a' : '#f97316'}
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
  const [dataSource, setDataSource] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loadingFrontier, setLoadingFrontier] = useState(false);

  // Load model info on mount
  useEffect(() => {
    api.get('/api/portfolio/model-info')
      .then(r => {
        setModelMeta(r.data?.metadata || null);
        setDataSource(r.data?.data_source || null);
      })
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

  const donutData = Object.entries(catWeights)
    .map(([cat, pct]) => ({ label: cat, pct, color: CAT_COLORS[cat] || '#888' }))
    .sort((a, b) => b.pct - a.pct);

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div className="portfolio-page min-h-screen bg-[#030303] text-white flex flex-col">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-amber-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-orange-500/15 rounded-full blur-[100px] mix-blend-screen"></div>
      </div>

      {/* Sidebar */}
      <Sidebar />

      {/* Navigation Header */}
      <nav className="fixed top-0 left-0 w-full z-50">
        <div className="absolute inset-0 bg-black/50 backdrop-blur-md border-b border-white/5"></div>
        <div className="max-w-7xl mx-auto px-6 h-16 relative flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-3 group transition-all hover:opacity-80"
          >
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-amber-500/50 transition-colors">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-amber-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">PORTFOLIO</span>
          </button>

          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium"
          >
            <iconify-icon icon="solar:arrow-left-linear" width="16"></iconify-icon>
            <span className="hidden md:inline">Back to Dashboard</span>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-16 px-6 ml-20 flex-1">
        <div className="max-w-7xl mx-auto">
      {/* Header */}
      <section className="mb-12">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
          <span className="text-xs text-white/50 font-medium tracking-widest uppercase">Asset Allocation</span>
        </div>
        <h1 className="font-display text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
          Portfolio <span className="bg-gradient-to-r from-amber-300 to-orange-500 bg-clip-text text-transparent">Optimizer</span>
        </h1>
        <p className="text-white/50 max-w-2xl">
          Mean-variance optimization on real Indian market data, adjusted for your risk level, loans and goals.
        </p>
      </section>

      <div className="portfolio-grid">
        {/* ── Left: Input Panel ─────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* Input Card */}
          <div className="portfolio-card">
            <h2><iconify-icon icon="solar:tuning-2-linear" width="20" className="text-amber-400"></iconify-icon> Configure Portfolio</h2>

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
                <span style={{ fontSize: '0.8rem', color: '#fbbf24', fontWeight: 700 }}>
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
                  {RISK_LABELS[riskScore]}
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
                {error}
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
            <h2><iconify-icon icon="solar:cpu-bolt-linear" width="20" className="text-amber-400"></iconify-icon> Data and Model</h2>
            {dataSource && (
              <div
                style={{
                  fontSize: '0.78rem',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  marginBottom: '0.9rem',
                  background: dataSource.type === 'real_historical' ? 'rgba(255,255,255,0.04)' : 'rgba(239,68,68,0.12)',
                  border: `1px solid ${dataSource.type === 'real_historical' ? 'rgba(251,191,36,0.25)' : 'rgba(239,68,68,0.35)'}`,
                  color: dataSource.type === 'real_historical' ? 'rgba(255,255,255,0.65)' : '#fca5a5',
                }}
              >
                {dataSource.type === 'real_historical' ? (
                  <>Real market data from {Object.keys(dataSource.per_asset_range || {}).length} sources
                    (NSE indices &amp; ETFs, liquid-fund NAV, COMEX silver × USD/INR), {(() => {
                      const yrs = Object.values(dataSource.per_asset_range || {}).map(r => r.months / 12);
                      return yrs.length ? `${Math.min(...yrs).toFixed(0)}–${Math.max(...yrs).toFixed(0)} years` : '';
                    })()} of history per asset. Expected returns are shrunk toward a risk-based prior;
                    {' '}risk is estimated from weekly returns. Fixed Deposit is assumption-based (no market series).</>
                ) : (
                  <>Running on synthetic (simulated) data — not real market history. Run
                    {' '}<code>fetch_real_data.py</code> on the backend to switch to real data.</>
                )}
              </div>
            )}
            {modelMeta ? (
              <>
                <div className="model-info-grid">
                  <div className="model-metric">
                    <div className="mm-label">Algorithm</div>
                    <div className="mm-value">{modelMeta.algorithm}</div>
                  </div>
                  <div className="model-metric">
                    <div className="mm-label">Avg R²</div>
                    <div className="mm-value">
                      {modelMeta.overall_r2 != null ? `${(modelMeta.overall_r2 * 100).toFixed(1)}%` : 'n/a'}
                    </div>
                  </div>
                  <div className="model-metric">
                    <div className="mm-label">Assets Trained</div>
                    <div className="mm-value">
                      {(modelMeta.trained_assets?.length ?? modelMeta.n_assets)} / {modelMeta.n_assets}
                    </div>
                  </div>
                  <div className="model-metric">
                    <div className="mm-label">CV Strategy</div>
                    <div className="mm-value" style={{ fontSize: '0.8rem' }}>{modelMeta.cv_strategy?.split('(')[0]}</div>
                  </div>
                </div>

                {modelMeta.blend && (
                  <div style={{ fontSize: '0.76rem', color: 'rgba(255,255,255,0.55)', marginBottom: '0.6rem' }}>
                    ML influence on expected returns: {(modelMeta.blend.avg_ml_weight * 100).toFixed(0)}%
                    {modelMeta.blend.avg_ml_weight === 0 && (
                      <> — no model beats its asset's historical average out-of-sample (R² ≤ 0), so allocations use real historical returns</>
                    )}
                  </div>
                )}

                {(() => {
                  const m = modelMeta.per_asset_metrics || {};
                  const names = (status) => (modelMeta.skipped_assets || [])
                    .filter(a => m[a]?.status === status).map(a => a.replace(/_/g, ' ')).join(', ');
                  const thin = names('insufficient_data');
                  const fixed = names('constant_target');
                  return (thin || fixed) && (
                    <div style={{ fontSize: '0.76rem', color: 'rgba(255,255,255,0.45)', marginBottom: '0.75rem' }}>
                      {thin && <div>Not trained (not enough real history yet, using historical average): {thin}</div>}
                      {fixed && <div>Not trained (fixed assumed rate, nothing to predict): {fixed}</div>}
                    </div>
                  );
                })()}

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
                <div className="empty-icon"><iconify-icon icon="solar:pie-chart-2-bold-duotone" width="56" className="text-amber-400"></iconify-icon></div>
                <h3>Your optimized portfolio will appear here</h3>
                <p>
                  Set your investable amount and risk score, then click
                  "Optimize Portfolio" to get your personalized allocation.
                </p>
              </div>
            </div>
          ) : (
            <>
              {/* Stats row */}
              <div className="portfolio-stats-row">
                <div className="stat-chip">
                  <span className="chip-label">Expected Return</span>
                  <span className="chip-value" style={{ color: '#fde68a' }}>
                    {expRet.toFixed(1)}% / yr
                  </span>
                </div>
                <div className="stat-chip">
                  <span className="chip-label">Volatility</span>
                  <span className="chip-value" style={{ color: '#fb7185' }}>
                    {riskPct.toFixed(1)}%
                  </span>
                </div>
                <div className="stat-chip">
                  <span className="chip-label">Sharpe Ratio</span>
                  <span className="chip-value" style={{ color: '#fbbf24' }}>
                    {sharpe.toFixed(2)}
                  </span>
                </div>
                <div className="stat-chip">
                  <span className="chip-label">Engine</span>
                  <span className="chip-value" style={{ fontSize: '0.85rem' }}>
                    {(() => {
                      if (portfolio.engine !== 'ml_predicted') return 'Historical';
                      const w = portfolio.model_metadata?.blend?.avg_ml_weight ?? 0;
                      return w > 0 ? `ML blend (${(w * 100).toFixed(0)}%)` : 'Historical avg';
                    })()}
                  </span>
                </div>
                <div className="stat-chip">
                  <span className="chip-label">Data</span>
                  <span className="chip-value" style={{ fontSize: '0.85rem' }}>
                    {portfolio.data_source?.type === 'real_historical' ? 'Real market data' : 'Synthetic'}
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
                    {t === 'overview' ? 'Overview' : t === 'breakdown' ? 'Breakdown' : t === 'frontier' ? 'Frontier' : 'What-If'}
                  </button>
                ))}
              </div>

              {/* ── Overview Tab ──── */}
              {activeTab === 'overview' && (
                <>
                  <div className="portfolio-card">
                    <h2><iconify-icon icon="solar:pie-chart-2-linear" width="20" className="text-amber-400"></iconify-icon> Asset Allocation</h2>
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
                    <h2><iconify-icon icon="solar:calendar-linear" width="20" className="text-amber-400"></iconify-icon> Projected Returns</h2>
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
                  <h2><iconify-icon icon="solar:list-linear" width="20" className="text-amber-400"></iconify-icon> Asset Breakdown</h2>
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
                                  background: ASSET_COLORS[alloc.display_name] || '#f59e0b',
                                }}
                              />
                            </div>
                          </td>
                          <td>₹{(alloc.amount_inr || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                          <td style={{ color: '#fde68a' }}>
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
                  <h2><iconify-icon icon="solar:graph-up-linear" width="20" className="text-amber-400"></iconify-icon> Efficient Frontier</h2>
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
      </main>

      <SmartFinFooter iconClass="text-amber-400" statusDotClass="bg-amber-400" />
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
      <div style={{ color: '#fca5a5', fontSize: '0.85rem' }}>{error}</div>
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
              {sc.name}
              <span style={{ marginLeft: 'auto', fontSize: '0.78rem', color: 'rgba(255,255,255,0.4)', fontWeight: 400 }}>
                Risk Score {sc.risk_score}/10
              </span>
            </h2>

            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <div className="stat-chip">
                <span className="chip-label">Return</span>
                <span className="chip-value" style={{ color: '#fde68a', fontSize: '0.95rem' }}>{ret.toFixed(1)}%</span>
              </div>
              <div className="stat-chip">
                <span className="chip-label">Risk</span>
                <span className="chip-value" style={{ color: '#fb7185', fontSize: '0.95rem' }}>{risk.toFixed(1)}%</span>
              </div>
              <div className="stat-chip">
                <span className="chip-label">Sharpe</span>
                <span className="chip-value" style={{ color: '#fbbf24', fontSize: '0.95rem' }}>{sharpe.toFixed(2)}</span>
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

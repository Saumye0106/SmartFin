import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './NudgeEngine.css';

const SEV_CLASS = { high: 'severity-high', medium: 'severity-medium', low: 'severity-low' };
const BADGE_CLASS = { high: 'badge-high', medium: 'badge-medium', low: 'badge-low', blue: 'badge-blue' };

function NudgeCard({ nudge }) {
  const isBlue = nudge.color === 'blue';
  return (
    <div className={`nudge-item ${isBlue ? 'nudge-item-blue' : SEV_CLASS[nudge.severity] || 'severity-low'}`}>
      <div className="nudge-item-header">
        <span className="nudge-emoji">{nudge.emoji}</span>
        <div style={{ flex: 1 }}>
          {nudge.category && (
            <div className="nudge-category-tag">{nudge.category}</div>
          )}
          <p className="nudge-title">{nudge.title}</p>
        </div>
        <span className={`nudge-label-badge ${isBlue ? 'badge-blue' : BADGE_CLASS[nudge.severity] || 'badge-low'}`}>
          {nudge.label}
        </span>
      </div>
      <p className="nudge-message">{nudge.message}</p>
      {nudge.action && (
        <div className="nudge-action">💡 {nudge.action}</div>
      )}
    </div>
  );
}

function TimelineChart({ history }) {
  if (!history || history.length === 0) return (
    <div className="nudge-empty">
      <div className="empty-icon">📅</div>
      <p>No timeline data yet</p>
    </div>
  );

  const recent = history.slice(-12); // Last 12 weeks

  return (
    <div className="timeline-chart">
      {recent.map((row) => (
        <div key={row.week} className="timeline-row">
          <div className="timeline-week-label">
            {new Date(row.week).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
          </div>
          <div className="timeline-bar-track">
            <div
              className={`timeline-bar-fill sev-${row.severity}`}
              style={{ width: `${(row.anomaly_score * 100).toFixed(0)}%` }}
            />
          </div>
          <div className="timeline-score-label">{(row.anomaly_score * 100).toFixed(0)}%</div>
        </div>
      ))}
      <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
        {[['sev-low', 'Normal'], ['sev-medium', 'Watch'], ['sev-high', 'Alert']].map(([cls, label]) => (
          <div key={cls} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', color: 'rgba(255,255,255,0.4)' }}>
            <div style={{ width: 24, height: 6, borderRadius: 99 }} className={`timeline-bar-fill ${cls}`} />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}

function BudgetBustMeter({ probability }) {
  if (probability == null) return (
    <div style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.82rem' }}>
      Not enough data for budget prediction yet.
    </div>
  );

  const pct = Math.round(probability * 100);
  const color = pct >= 65 ? '#ef4444' : pct >= 40 ? '#f59e0b' : '#10b981';

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
        <span style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.6)' }}>
          Chance of exceeding budget this month
        </span>
        <span style={{ fontSize: '1.1rem', fontWeight: 700, color }}>
          {pct}%
        </span>
      </div>
      <div className="budget-bust-bar">
        <div
          className="budget-bust-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.3)', marginTop: '0.3rem' }}>
        Based on Random Forest classifier trained on your first-7-days spending trajectory
      </div>
    </div>
  );
}

export default function NudgeEngine() {
  const navigate = useNavigate();
  const [nudges, setNudges]           = useState(null);
  const [history, setHistory]         = useState(null);
  const [patterns, setPatterns]       = useState(null);
  const [dataQuality, setDataQuality] = useState(null);
  const [bbProb, setBbProb]           = useState(null);
  const [modelInfo, setModelInfo]     = useState(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);
  const [activeTab, setActiveTab]     = useState('nudges');

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      try {
        const [nudgesRes, historyRes, patternsRes] = await Promise.all([
          api.get('/api/nudges/'),
          api.get('/api/nudges/history'),
          api.get('/api/nudges/patterns'),
        ]);

        if (nudgesRes.data.success) {
          setNudges(nudgesRes.data.nudges);
          setDataQuality(nudgesRes.data.data_quality);
          setBbProb(nudgesRes.data.budget_bust_probability);
          setModelInfo(nudgesRes.data.model_info);
        }
        if (historyRes.data.success) setHistory(historyRes.data.history);
        if (patternsRes.data.success) setPatterns(patternsRes.data.patterns);
      } catch (e) {
        setError(e.message || 'Could not load nudge data. Is the backend running?');
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) return (
    <div className="nudge-page">
      <div className="nudge-loading">
        <iconify-icon icon="svg-spinners:ring-resize" width="44"></iconify-icon>
        <p>Analyzing your spending patterns...</p>
      </div>
    </div>
  );

  return (
    <div className="nudge-page">
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

      <div className="nudge-header">
        <h1>🧠 Behavioral Nudge Engine</h1>
        <p>
          Isolation Forest anomaly detection on your personal spending patterns —
          identifies unusual weeks and recurring behavioral triggers before they bust your budget.
        </p>
      </div>

      {error && (
        <div style={{
          background: 'rgba(239,68,68,0.1)',
          border: '1px solid rgba(239,68,68,0.25)',
          borderRadius: '0.875rem',
          padding: '1rem',
          color: '#fca5a5',
          marginBottom: '1.5rem',
          fontSize: '0.85rem',
        }}>
          ⚠️ {error}
        </div>
      )}

      <div className="nudge-grid">
        {/* ── Left: Main content ─────────────────────────────────────── */}
        <div>
          {/* Tabs */}
          <div className="portfolio-tabs" style={{ marginBottom: '1.25rem' }}>
            {['nudges', 'timeline', 'patterns'].map(t => (
              <button
                key={t}
                className={`tab-btn ${activeTab === t ? 'active' : ''}`}
                onClick={() => setActiveTab(t)}
                style={{
                  padding: '0.5rem 1.1rem',
                  borderRadius: '0.625rem',
                  border: '1px solid rgba(255,255,255,0.08)',
                  background: activeTab === t ? 'rgba(99,102,241,0.25)' : 'transparent',
                  color: activeTab === t ? '#c4b5fd' : 'rgba(255,255,255,0.55)',
                  borderColor: activeTab === t ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.08)',
                  fontWeight: activeTab === t ? 600 : 400,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {t === 'nudges' ? '🔔 Nudges' : t === 'timeline' ? '📅 Timeline' : '📊 Patterns'}
              </button>
            ))}
          </div>

          {/* ── Nudges Tab ──────────── */}
          {activeTab === 'nudges' && (
            <div className="nudge-card">
              <h2>🔔 Your Spending Nudges</h2>
              {nudges && nudges.length > 0 ? (
                <div className="nudge-list">
                  {nudges.map(n => <NudgeCard key={n.id} nudge={n} />)}
                </div>
              ) : (
                <div className="nudge-empty">
                  <div className="empty-icon">✅</div>
                  <p>No nudges right now — your spending looks normal!</p>
                </div>
              )}

              {/* Budget Bust Meter */}
              {bbProb != null && (
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.875rem', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <div style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.4)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    BUDGET RISK METER
                  </div>
                  <BudgetBustMeter probability={bbProb} />
                </div>
              )}
            </div>
          )}

          {/* ── Timeline Tab ─────────── */}
          {activeTab === 'timeline' && (
            <div className="nudge-card">
              <h2>📅 Weekly Anomaly Timeline</h2>
              <p style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.4)', marginBottom: '1.25rem' }}>
                Your personal anomaly score for each week — higher means your spending
                was more unusual compared to your own baseline (not a global average).
              </p>
              <TimelineChart history={history} />
            </div>
          )}

          {/* ── Patterns Tab ─────────── */}
          {activeTab === 'patterns' && (
            <div className="nudge-card">
              <h2>📊 Recurring Patterns</h2>
              <p style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.4)', marginBottom: '1.25rem' }}>
                Systematic behavioral patterns detected in your spending history.
                These repeat predictably — and are the hardest to break without awareness.
              </p>
              {patterns && patterns.length > 0 ? (
                <div className="pattern-list">
                  {patterns.map(p => (
                    <div key={p.category} className="pattern-item">
                      <div className="pattern-cat">{p.display_category}</div>
                      <div className="pattern-desc">{p.description}</div>
                      <div className="pattern-ratio">
                        Week 1: {p.avg_ratio_week1}x avg · Other weeks: {p.avg_ratio_other}x avg
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="nudge-empty">
                  <div className="empty-icon">📈</div>
                  <p>No recurring patterns detected yet. Log more expenses to enable pattern analysis.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Right: Model Info Sidebar ──────────────────────────────── */}
        <div>
          {/* Data Quality */}
          <div className="nudge-card">
            <h2>📦 Data Quality</h2>
            <div className="model-info-sidebar">
              <div className="model-info-row">
                <span className="model-info-key">Weeks of data</span>
                <span className="model-info-val">{dataQuality?.weeks_of_data ?? '—'}</span>
              </div>
              <div className="model-info-row">
                <span className="model-info-key">Status</span>
                <span className="model-info-val" style={{
                  color: dataQuality?.sufficient ? '#34d399' : '#f59e0b'
                }}>
                  {dataQuality?.sufficient ? 'Active' : 'Needs more data'}
                </span>
              </div>
              {dataQuality?.date_range?.start && (
                <>
                  <div className="model-info-row">
                    <span className="model-info-key">From</span>
                    <span className="model-info-val" style={{ fontSize: '0.8rem' }}>
                      {new Date(dataQuality.date_range.start).toLocaleDateString('en-IN')}
                    </span>
                  </div>
                  <div className="model-info-row">
                    <span className="model-info-key">To</span>
                    <span className="model-info-val" style={{ fontSize: '0.8rem' }}>
                      {new Date(dataQuality.date_range.end).toLocaleDateString('en-IN')}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ML Model Info */}
          <div className="nudge-card">
            <h2>🤖 Model Info</h2>
            <div className="model-info-sidebar">
              <div className="model-info-row">
                <span className="model-info-key">Algorithm</span>
                <span className="model-info-val">{modelInfo?.algorithm || 'Isolation Forest'}</span>
              </div>
              <div className="model-info-row">
                <span className="model-info-key">Type</span>
                <span className="model-info-val">Unsupervised</span>
              </div>
              <div className="model-info-row">
                <span className="model-info-key">Contamination</span>
                <span className="model-info-val">{modelInfo?.contamination ? `${(modelInfo.contamination * 100).toFixed(0)}%` : '15%'}</span>
              </div>
              <div className="model-info-row">
                <span className="model-info-key">Personalized</span>
                <span className="model-info-val" style={{ color: '#34d399' }}>✓ Per-user</span>
              </div>
              <div className="model-info-row">
                <span className="model-info-key">Labels needed</span>
                <span className="model-info-val" style={{ color: '#34d399' }}>None</span>
              </div>
            </div>
            <div style={{
              marginTop: '1rem',
              padding: '0.75rem',
              background: 'rgba(99,102,241,0.08)',
              borderRadius: '0.75rem',
              fontSize: '0.78rem',
              color: 'rgba(255,255,255,0.5)',
              lineHeight: 1.6,
            }}>
              Isolation Forest is an unsupervised anomaly detection algorithm.
              It "isolates" anomalies by partitioning feature space — outliers
              require fewer splits to isolate. No labeled training data needed.
            </div>
          </div>

          {/* Feature explanation */}
          <div className="nudge-card">
            <h2>📐 Features Used</h2>
            {[
              ['Weekly spend per category', 'Normalized by income'],
              ['Rolling 4-week average', 'Per category baseline'],
              ['Ratio vs rolling avg', 'Key anomaly signal'],
              ['Lag features (1–2 weeks)', 'Temporal context'],
              ['Week-of-month', 'Salary-day effect'],
            ].map(([feat, desc]) => (
              <div key={feat} style={{
                display: 'flex',
                flexDirection: 'column',
                padding: '0.5rem 0',
                borderBottom: '1px solid rgba(255,255,255,0.04)',
              }}>
                <span style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>
                  {feat}
                </span>
                <span style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)' }}>{desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';

const pct = (v) => `${(v * 100).toFixed(v < 0.1 ? 1 : 0)}%`;

const formatDriverValue = (d) => {
  if (d.value === null || d.value === undefined) return 'not provided';
  if (d.feature === 'debt_ratio') return `${Math.round(d.value * 100)}% of income`;
  if (d.feature === 'utilization') return `${Math.round(d.value * 100)}% of limit`;
  return String(Math.round(d.value));
};

const DRIVER_STYLE = {
  'raises risk': { color: '#f97316', icon: 'solar:arrow-up-linear' },
  'lowers risk': { color: '#10b981', icon: 'solar:arrow-down-linear' },
  neutral: { color: 'rgba(255,255,255,0.4)', icon: 'solar:minus-circle-linear' },
};

const ScoreDisplay = ({ score, classification, risk, modelInfo }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    if (score) {
      let current = 0;
      const increment = score / 50;
      const timer = setInterval(() => {
        current += increment;
        if (current >= score) {
          setAnimatedScore(score);
          clearInterval(timer);
        } else {
          setAnimatedScore(Math.round(current));
        }
      }, 20);

      return () => clearInterval(timer);
    }
  }, [score]);

  if (!classification) return null;

  if (score === null || score === undefined) {
    return (
      <div className="flex flex-col items-center text-center">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
            <iconify-icon icon="solar:chart-2-linear" className="text-white/50 text-xl"></iconify-icon>
          </div>
          <div className="text-left">
            <h2 className="text-xl font-bold text-white">Financial Health Score</h2>
            <p className="text-xs text-white/50">How you rank against real borrowers your age</p>
          </div>
        </div>
        <div className="text-2xl font-semibold text-white/80 mb-2">Not enough data to score you yet</div>
        <p className="text-white/60 max-w-xl text-sm leading-relaxed mb-5">
          {risk?.confidence_note || classification.description} A score now would only reflect your age.
        </p>
        {risk?.missing?.length > 0 && (
          <ul className="w-full max-w-xl space-y-2 text-left">
            {risk.missing.map((m) => (
              <li key={m.input} className="rounded-lg border border-white/10 bg-black/30 px-4 py-3 text-sm text-white/75">{m.hint}</li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  const circumference = 2 * Math.PI * 90;
  const progress = (animatedScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:chart-2-linear" className="text-cyan-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Financial Health Score</h2>
          <p className="text-xs text-white/50">How you rank against real borrowers your age</p>
        </div>
      </div>
      
      <div className="relative w-64 h-64 mb-8">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 200 200">
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke="rgba(255, 255, 255, 0.05)"
            strokeWidth="12"
          />
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke={classification.color}
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
            style={{ filter: `drop-shadow(0 0 8px ${classification.color}40)` }}
          />
        </svg>
        
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-6xl font-bold font-display tracking-tight" style={{ color: classification.color }}>
            {animatedScore}
          </div>
          <div className="text-white/40 text-sm font-mono">/ 100</div>
        </div>
      </div>

      <div 
        className="inline-flex items-center gap-3 px-6 py-3 rounded-full border backdrop-blur-sm mb-4"
        style={{ 
          backgroundColor: `${classification.color}10`,
          borderColor: `${classification.color}30`,
          color: classification.color 
        }}
      >
        <span className="text-2xl">{classification.emoji}</span>
        <span className="font-semibold text-lg">{classification.category}</span>
      </div>

      <p className="text-center text-white/60 max-w-md text-sm leading-relaxed">
        {classification.description}
      </p>

      {risk && (
        <div className="w-full max-w-2xl mt-8 space-y-4">
          {risk.confidence === 'limited' && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
              {risk.confidence_note}
              {risk.missing?.length > 0 && (
                <ul className="list-disc pl-5 mt-2 space-y-1 text-amber-100/80">
                  {risk.missing.map((m) => <li key={m.input}>{m.hint}</li>)}
                </ul>
              )}
            </div>
          )}
          <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/70">
            Estimated chance of falling 90+ days behind on a payment in the next 2 years:{' '}
            <span className="font-semibold text-white">{pct(risk.risk_probability)}</span>
            <span className="text-white/40"> (average borrower: {pct(risk.average_risk)})</span>
          </div>

          <div>
            <div className="text-[10px] uppercase tracking-widest text-white/40 font-medium mb-2">What is driving your score</div>
            <div className="space-y-2">
              {risk.drivers.map((d) => {
                const style = DRIVER_STYLE[d.direction] || DRIVER_STYLE.neutral;
                return (
                  <div key={d.feature} className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/30 px-4 py-2 text-sm">
                    <div className="min-w-0">
                      <div className="text-white/80">{d.label}</div>
                      <div className="text-xs text-white/40">
                        {formatDriverValue(d)}{!d.actionable && " · can't be changed"}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0 text-xs font-medium" style={{ color: style.color }}>
                      <iconify-icon icon={style.icon} width="14"></iconify-icon>
                      {d.direction}
                    </div>
                  </div>
                );
              })}
            </div>
            {risk.history_source === 'request_only' && (
              <p className="text-xs text-white/40 mt-2">
                Late and missed payments are taken as zero unless you enter them or record loan payments in SmartFin.
              </p>
            )}
          </div>

          {modelInfo && (
            <p className="text-xs text-white/35 leading-relaxed">
              {modelInfo.model_type}, trained on {modelInfo.trained_on}. Cross-validated AUC {modelInfo.auc?.toFixed(3)} (logistic
              baseline {modelInfo.baseline_auc?.toFixed(3)}); {modelInfo.auc_without_card_data?.toFixed(3)} without credit-card data.
              {' '}{modelInfo.caveats?.[0]}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default ScoreDisplay;

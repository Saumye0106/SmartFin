import { useEffect, useState } from 'react';
import api from '../services/api';

const formatINR = (v) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(v || 0));

const KIND_STYLE = {
  income: 'text-emerald-300 border-emerald-500/30',
  rent: 'text-orange-300 border-orange-500/30',
  emi: 'text-red-300 border-red-500/30',
  investment: 'text-sky-300 border-sky-500/30',
  insurance: 'text-violet-300 border-violet-500/30',
  bill: 'text-white/70 border-white/20',
};

export default function RecurringPayments({ refreshKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getRecurring().then(setData).catch((e) => setError(e.message));
  }, [refreshKey]);

  if (error) return null;
  if (!data || data.months_of_history === 0) return null;

  const active = data.recurring.filter((r) => r.active);
  const stopped = data.recurring.filter((r) => !r.active);

  return (
    <section className="rounded-2xl border border-white/10 bg-black/30 p-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-2 mb-4">
        <div>
          <h2 className="text-xl font-semibold">Recurring payments</h2>
          <p className="text-xs text-white/50 mt-1">
            Detected from {data.months_of_history} month{data.months_of_history > 1 ? 's' : ''} of imported statements
            {data.as_of ? ` (up to ${data.as_of})` : ''}.
          </p>
        </div>
        <div className="flex gap-4 text-sm">
          <div><span className="text-white/50">Income </span><span className="text-emerald-300 font-medium">{formatINR(data.totals.income_monthly)}/mo</span></div>
          <div><span className="text-white/50">Fixed costs </span><span className="text-orange-300 font-medium">{formatINR(data.totals.fixed_outflow_monthly)}/mo</span></div>
          <div><span className="text-white/50">Investing </span><span className="text-sky-300 font-medium">{formatINR(data.totals.investments_monthly)}/mo</span></div>
        </div>
      </div>

      {data.months_of_history < 3 && data.recurring.length === 0 ? (
        <p className="text-sm text-white/50">
          Import at least 3 months of statements to detect rent, subscriptions, EMIs, SIPs and salary automatically.
        </p>
      ) : active.length === 0 ? (
        <p className="text-sm text-white/50">No recurring payments found yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {active.map((r) => (
            <div key={`${r.merchant}-${r.direction}-${r.typical_amount}`} className="rounded-xl border border-white/10 bg-black/30 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="font-medium">{r.merchant}</div>
                <span className={`text-[10px] uppercase tracking-wider border rounded px-1.5 py-0.5 ${KIND_STYLE[r.kind] || KIND_STYLE.bill}`}>
                  {r.kind}
                </span>
              </div>
              <div className={`text-lg mt-1 ${r.direction === 'credit' ? 'text-emerald-300' : 'text-white'}`}>
                {r.amount_type === 'variable' ? '~' : ''}{formatINR(r.typical_amount)}
                <span className="text-xs text-white/40"> / {r.cadence === 'monthly' && r.interval_days < 29 ? `${r.interval_days} days` : r.cadence.replace('ly', '')}</span>
              </div>
              <div className="text-xs text-white/45 mt-1">
                Next ~{r.next_expected} · seen {r.occurrences}×{r.amount_type === 'variable' ? ' · amount varies' : ''}
              </div>
            </div>
          ))}
        </div>
      )}

      {stopped.length > 0 && (
        <p className="text-xs text-white/40 mt-3">
          Looks stopped: {stopped.map((r) => `${r.merchant} (last ${r.last_date})`).join(', ')}
        </p>
      )}
    </section>
  );
}

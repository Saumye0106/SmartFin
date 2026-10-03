import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import api from '../services/api';

const formatINR = (v) =>
  v === null || v === undefined ? '–'
    : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(v));

const IMPORT_AS = {
  loan: { label: 'Loan + payments', className: 'text-emerald-300 border-emerald-500/30' },
  card: { label: 'Card details + history', className: 'text-sky-300 border-sky-500/30' },
  history_only: { label: 'Payment history only', className: 'text-white/60 border-white/20' },
};
const NEED_LABEL = { sanctioned: 'amount', opened: 'opening date', emi: 'EMI', tenure_months: 'tenure', interest_rate: 'interest rate' };

// What the server will decide for a row, mirrored here so the badge updates as the user fills fields in.
const resolve = (r) => {
  if (r.kind === 'card') return { importAs: 'card', needs: [] };
  if (!r.is_open) return { importAs: 'history_only', needs: [] };
  const has = (v) => v !== null && v !== undefined && v !== '';
  const canCalcEmi = Number(r.sanctioned) > 0 && Number(r.tenure_months) > 0 && has(r.interest_rate);
  const needs = [];
  if (!(Number(r.sanctioned) > 0)) needs.push('sanctioned');
  if (!(Number(r.emi) > 0) && !canCalcEmi) needs.push('emi');
  if (!(Number(r.tenure_months) > 0)) needs.push('tenure_months');
  if (!r.opened) needs.push('opened');
  if (!has(r.interest_rate)) needs.push('interest_rate');
  return { importAs: needs.length ? 'history_only' : 'loan', needs };
};

export default function CreditReportImport({ open, onClose, onImported }) {
  const [file, setFile] = useState(null);
  const [password, setPassword] = useState('');
  const [needsPassword, setNeedsPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);
  const [rows, setRows] = useState([]);
  const [result, setResult] = useState(null);
  const [past, setPast] = useState([]);
  const [pendingUndo, setPendingUndo] = useState(null);

  const loadPast = () => api.listCreditReports().then((d) => setPast(d.imports || [])).catch(() => {});
  useEffect(() => { if (open) loadPast(); }, [open]);

  const reset = () => {
    setFile(null); setPassword(''); setNeedsPassword(false); setError(null);
    setPreview(null); setRows([]); setResult(null); setPendingUndo(null);
  };
  const close = () => { reset(); onClose(); };

  const handlePreview = async (e) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true); setError(null);
    try {
      const data = await api.previewCreditReport(file, password);
      setPreview(data);
      setRows(data.rows);
      setNeedsPassword(false);
    } catch (err) {
      setNeedsPassword(err.passwordRequired);
      setError(err.message);
    } finally {
      setBusy(false);
      setPassword('');
    }
  };

  const update = (hash, field, value) =>
    setRows((prev) => prev.map((r) => (r.account_hash === hash ? { ...r, [field]: value } : r)));

  const included = rows.filter((r) => r.include);

  const handleConfirm = async () => {
    setBusy(true); setError(null);
    try {
      // The server recalculates everything; blanks go as null.
      const payload = rows.map((r) => ({
        ...r,
        emi: r.emi === '' ? null : r.emi,
        tenure_months: r.tenure_months === '' ? null : r.tenure_months,
        interest_rate: r.interest_rate === '' ? null : r.interest_rate,
      }));
      const res = await api.confirmCreditReport(payload, preview.bureau, preview.score);
      setResult(res);
      loadPast();
      onImported?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleUndo = async (batchId) => {
    setBusy(true); setError(null);
    try {
      await api.undoCreditReport(batchId);
      setPendingUndo(null);
      if (result?.batch_id === batchId) reset();
      await loadPast();
      onImported?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (!open) return null;

  const numberInput = (r, field, placeholder, width = 'w-24') => (
    <input
      type="number"
      min="0"
      step="any"
      value={r[field] ?? ''}
      placeholder={placeholder}
      aria-label={`${NEED_LABEL[field]} for ${r.lender}`}
      onChange={(e) => update(r.account_hash, field, e.target.value)}
      className={`${width} bg-black/40 border border-white/20 rounded-lg px-2 py-1 text-sm`}
    />
  );

  // Rendered on <body>: inside the page it sits in a stacking context below the site footer, which then covers the buttons.
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 text-white" role="dialog" aria-modal="true">
      <div className="w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col rounded-2xl border border-white/10 bg-[#0b0b0f]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div>
            <h2 className="text-xl font-semibold">Import credit report</h2>
            <p className="text-xs text-white/50 mt-1">
              A CIBIL, Experian, Equifax or CRIF report PDF. It fills in your loans, their payment history and your card details.
              The file is read once and not stored.
            </p>
          </div>
          <button onClick={close} className="text-white/50 hover:text-white text-2xl leading-none" aria-label="Close">×</button>
        </div>

        <div className="overflow-y-auto px-6 py-5 space-y-5">
          {error && <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</div>}

          {!preview && (
            <>
              <form onSubmit={handlePreview} className="space-y-4">
                <input
                  type="file"
                  accept=".pdf,.txt"
                  onChange={(e) => { setFile(e.target.files?.[0] || null); setError(null); setNeedsPassword(false); }}
                  className="block w-full text-sm text-white/70 file:mr-4 file:rounded-lg file:border-0 file:bg-purple-500 file:px-4 file:py-2 file:text-white file:font-medium"
                />
                {needsPassword && (
                  <div>
                    <label className="text-xs text-white/50" htmlFor="credit-report-password">PDF password</label>
                    <input
                      id="credit-report-password"
                      type="password"
                      autoComplete="off"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="mt-1 w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
                      placeholder="Often part of your name + date of birth"
                    />
                    <p className="text-xs text-white/40 mt-1">Used only to open this file; never saved.</p>
                  </div>
                )}
                <button type="submit" disabled={!file || busy} className="rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 px-5 py-2.5 font-medium disabled:opacity-50">
                  {busy ? 'Reading…' : 'Preview accounts'}
                </button>
              </form>

              {past.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-white/80 mb-2">Past credit report imports</h3>
                  <ul className="space-y-2">
                    {past.map((b) => (
                      <li key={b.batch_id} className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm">
                        <div>
                          {b.bureau || 'Credit report'} · {b.accounts} accounts{b.score ? ` · score ${b.score}` : ''}
                          <span className="text-white/40"> · imported {String(b.imported_at).slice(0, 10)}</span>
                        </div>
                        {pendingUndo === b.batch_id ? (
                          <div className="flex gap-2 shrink-0">
                            <button type="button" disabled={busy} onClick={() => handleUndo(b.batch_id)} className="rounded-lg bg-red-500/80 hover:bg-red-500 px-3 py-1.5 text-xs font-medium disabled:opacity-50">Yes, remove it</button>
                            <button type="button" disabled={busy} onClick={() => setPendingUndo(null)} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs">Cancel</button>
                          </div>
                        ) : (
                          <button type="button" disabled={busy} onClick={() => setPendingUndo(b.batch_id)} className="shrink-0 rounded-lg border border-red-400/40 text-red-300 px-3 py-1.5 text-xs">Undo import</button>
                        )}
                      </li>
                    ))}
                  </ul>
                  <p className="text-xs text-white/40 mt-2">Undo removes the accounts that import added, with the loans and payments it created.</p>
                </div>
              )}
            </>
          )}

          {preview && !result && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                  <div className="text-xs text-white/50">Report</div>
                  <div className="font-medium mt-1">{preview.bureau || 'Unknown bureau'}{preview.score ? ` · score ${preview.score}` : ''}</div>
                </div>
                <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                  <div className="text-xs text-white/50">Accounts</div>
                  <div className="font-medium mt-1">{preview.summary.open_loans} open loans · {preview.summary.closed_loans} closed · {preview.summary.cards} cards</div>
                </div>
                <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                  <div className="text-xs text-white/50">Last {preview.summary.history_window_months} months</div>
                  <div className="font-medium mt-1">
                    <span className={preview.summary.late_24m ? 'text-orange-300' : ''}>{preview.summary.late_24m} late</span>
                    {' · '}
                    <span className={preview.summary.missed_24m ? 'text-red-300' : ''}>{preview.summary.missed_24m} missed (90+ days)</span>
                  </div>
                </div>
                <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                  <div className="text-xs text-white/50">Cards: used / limit</div>
                  <div className="font-medium mt-1">
                    {preview.summary.card_limit ? `${formatINR(preview.summary.card_balance)} / ${formatINR(preview.summary.card_limit)}` : 'No open card'}
                  </div>
                </div>
              </div>

              <p className="text-xs text-white/50">
                Check each account. An open loan becomes a SmartFin loan only when its EMI, tenure and interest rate are known;
                fill in any the report leaves out. Late means 30 to 89 days past due, missed means 90 or more.
              </p>

              <div className="rounded-xl border border-white/10 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-white/5 text-xs text-white/50">
                    <tr>
                      <th className="px-3 py-2 text-left w-8"></th>
                      <th className="px-3 py-2 text-left">Account</th>
                      <th className="px-3 py-2 text-right">Amount / balance</th>
                      <th className="px-3 py-2 text-left">EMI</th>
                      <th className="px-3 py-2 text-left">Tenure (mo)</th>
                      <th className="px-3 py-2 text-left">Rate %</th>
                      <th className="px-3 py-2 text-left">History</th>
                      <th className="px-3 py-2 text-left">Imported as</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => {
                      const { importAs, needs } = resolve(r);
                      const badge = IMPORT_AS[importAs];
                      const editable = r.kind === 'loan' && r.is_open;
                      return (
                        <tr key={r.account_hash} className={`border-t border-white/5 align-top ${r.include ? '' : 'opacity-40'}`}>
                          <td className="px-3 py-3">
                            <input type="checkbox" checked={r.include} onChange={() => update(r.account_hash, 'include', !r.include)} aria-label={`Include ${r.lender}`} className="w-4 h-4 rounded border border-white/30 bg-white/5" />
                          </td>
                          <td className="px-3 py-3">
                            <div className="font-medium">{r.lender}</div>
                            <div className="text-xs text-white/45">
                              {r.account_type}{r.account_number ? ` · ${r.account_number}` : ''}
                              {' · '}{r.is_open ? `opened ${r.opened || '?'}` : `closed ${r.closed}`}
                              {r.already_imported && <span className="text-amber-300"> · already imported, will be updated</span>}
                            </div>
                            {editable && (
                              <select value={r.loan_type} onChange={(e) => update(r.account_hash, 'loan_type', e.target.value)} aria-label={`Loan type for ${r.lender}`} className="mt-1 bg-black/40 border border-white/20 rounded-lg px-2 py-1 text-xs capitalize">
                                {preview.loan_types.map((t) => <option key={t} value={t}>{t}</option>)}
                              </select>
                            )}
                          </td>
                          <td className="px-3 py-3 text-right whitespace-nowrap">
                            <div>{formatINR(r.sanctioned)}</div>
                            <div className="text-xs text-white/45">{formatINR(r.balance)} left</div>
                          </td>
                          <td className="px-3 py-3">{editable ? numberInput(r, 'emi', 'calculated') : formatINR(r.emi)}{r.emi_calculated && <div className="text-[10px] text-white/40">calculated</div>}</td>
                          <td className="px-3 py-3">{editable ? numberInput(r, 'tenure_months', 'months', 'w-20') : (r.tenure_months ?? '–')}</td>
                          <td className="px-3 py-3">{editable ? numberInput(r, 'interest_rate', '%', 'w-20') : (r.interest_rate ?? '–')}</td>
                          <td className="px-3 py-3 whitespace-nowrap">
                            <div>{r.months_reported} months</div>
                            <div className="text-xs">
                              <span className={r.late_24m ? 'text-orange-300' : 'text-white/45'}>{r.late_24m} late</span>
                              {' · '}
                              <span className={r.missed_24m ? 'text-red-300' : 'text-white/45'}>{r.missed_24m} missed</span>
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <span className={`inline-block rounded-full border px-2 py-0.5 text-xs ${badge.className}`}>{badge.label}</span>
                            {needs.length > 0 && (
                              <div className="text-[11px] text-amber-300 mt-1">Add {needs.map((n) => NEED_LABEL[n]).join(', ')} to import it as a loan</div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {result && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-5 space-y-2">
              <div className="text-lg font-semibold text-emerald-300">
                Imported {result.accounts_added + result.accounts_updated} accounts
              </div>
              <div className="text-sm text-white/70">
                {result.loans_created} loans created · {result.payments_recorded} payments recorded · {result.history_months} months of payment history
                {result.accounts_updated > 0 && ` · ${result.accounts_updated} existing accounts updated`}
                {result.history_only > 0 && ` · ${result.history_only} kept as history only`}
              </div>
              {result.card_limit && (
                <div className="text-sm text-white/70">Card details saved: {formatINR(result.card_balance)} used of {formatINR(result.card_limit)}.</div>
              )}
              <div className="text-xs text-white/45">Your financial health score now uses this payment history.</div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/10">
          {preview && !result && (
            <>
              <button onClick={reset} disabled={busy} className="rounded-lg border border-white/20 px-4 py-2 text-sm">Choose another file</button>
              <button onClick={handleConfirm} disabled={busy || included.length === 0} className="rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 px-5 py-2 font-medium disabled:opacity-50">
                {busy ? 'Importing…' : `Import ${included.length} accounts`}
              </button>
            </>
          )}
          {result && (
            <>
              <button onClick={() => handleUndo(result.batch_id)} disabled={busy} className="rounded-lg border border-red-400/40 text-red-300 px-4 py-2 text-sm">Undo this import</button>
              <button onClick={close} className="rounded-lg bg-gradient-to-r from-purple-500 to-blue-500 px-5 py-2 font-medium">Done</button>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}

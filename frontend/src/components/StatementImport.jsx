import { useMemo, useState } from 'react';
import api from '../services/api';

const formatINR = (v) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(Number(v || 0));

const SOURCE_LABEL = { user_rule: 'your rule', keyword: 'auto', default: 'unsure' };

export default function StatementImport({ open, onClose, onImported }) {
  const [file, setFile] = useState(null);
  const [password, setPassword] = useState('');
  const [needsPassword, setNeedsPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);
  const [rows, setRows] = useState([]);
  const [result, setResult] = useState(null);
  const [showDuplicates, setShowDuplicates] = useState(false);

  const reset = () => {
    setFile(null); setPassword(''); setNeedsPassword(false); setError(null);
    setPreview(null); setRows([]); setResult(null); setShowDuplicates(false);
  };
  const close = () => { reset(); onClose(); };

  const handlePreview = async (e) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true); setError(null);
    try {
      const data = await api.previewStatement(file, password);
      setPreview(data);
      // Send every row back (duplicates too) so the server's duplicate hashes match the preview.
      setRows(data.rows.map((r) => ({ ...r, include: true })));
      setNeedsPassword(false);
    } catch (err) {
      setNeedsPassword(err.passwordRequired);
      setError(err.message);
    } finally {
      setBusy(false);
      setPassword('');
    }
  };

  // Changing one row's category applies to every new row from the same merchant.
  const setCategory = (merchant, category) =>
    setRows((prev) => prev.map((r) => (r.merchant === merchant && !r.duplicate ? { ...r, category } : r)));
  const toggle = (hash) =>
    setRows((prev) => prev.map((r) => (r.txn_hash === hash ? { ...r, include: !r.include } : r)));

  const visible = useMemo(() => rows.filter((r) => showDuplicates || !r.duplicate), [rows, showDuplicates]);
  const included = rows.filter((r) => r.include && !r.duplicate);
  const includedDebit = included.filter((r) => r.direction === 'debit').reduce((s, r) => s + r.amount, 0);

  const handleConfirm = async () => {
    setBusy(true); setError(null);
    try {
      const res = await api.confirmStatementImport(rows);
      setResult(res);
      onImported?.(preview.summary.period.end.slice(0, 7));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleUndo = async () => {
    setBusy(true); setError(null);
    try {
      await api.undoStatementImport(result.batch_id);
      onImported?.(preview.summary.period.end.slice(0, 7));
      reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col rounded-2xl border border-white/10 bg-[#0b0b0f]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div>
            <h2 className="text-xl font-semibold">Import bank statement</h2>
            <p className="text-xs text-white/50 mt-1">CSV, Excel or PDF from your bank or UPI app. The file is read once and not stored.</p>
          </div>
          <button onClick={close} className="text-white/50 hover:text-white text-2xl leading-none" aria-label="Close">×</button>
        </div>

        <div className="overflow-y-auto px-6 py-5 space-y-5">
          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</div>
          )}

          {!preview && (
            <form onSubmit={handlePreview} className="space-y-4">
              <input
                type="file"
                accept=".csv,.xls,.xlsx,.pdf"
                onChange={(e) => { setFile(e.target.files?.[0] || null); setError(null); setNeedsPassword(false); }}
                className="block w-full text-sm text-white/70 file:mr-4 file:rounded-lg file:border-0 file:bg-emerald-500 file:px-4 file:py-2 file:text-black file:font-medium"
              />
              {needsPassword && (
                <div>
                  <label className="text-xs text-white/50">PDF password</label>
                  <input
                    type="password"
                    autoComplete="off"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="mt-1 w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
                    placeholder="Often your name + date of birth, e.g. SAUM0101"
                  />
                  <p className="text-xs text-white/40 mt-1">Used only to open this file; never saved.</p>
                </div>
              )}
              <button
                type="submit"
                disabled={!file || busy}
                className="rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 px-5 py-2.5 font-medium text-black disabled:opacity-50"
              >
                {busy ? 'Reading…' : 'Preview transactions'}
              </button>
            </form>
          )}

          {preview && !result && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                  <div className="text-xs text-white/50">Period</div>
                  <div className="font-medium mt-1">{preview.summary.period.start} → {preview.summary.period.end}</div>
                </div>
                <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                  <div className="text-xs text-white/50">New / already imported</div>
                  <div className="font-medium mt-1">{preview.summary.new_count} / {preview.summary.duplicate_count}</div>
                </div>
                <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                  <div className="text-xs text-white/50">Money out (selected)</div>
                  <div className="font-medium mt-1 text-orange-300">{formatINR(includedDebit)}</div>
                </div>
                <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                  <div className="text-xs text-white/50">Money in</div>
                  <div className="font-medium mt-1 text-emerald-300">{formatINR(preview.summary.total_credit)}</div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-white/50">
                <span>Check the categories. Changing one row updates every row from that merchant, and SmartFin remembers it next time.</span>
                {preview.summary.duplicate_count > 0 && (
                  <label className="flex items-center gap-2 shrink-0 ml-4">
                    <input type="checkbox" checked={showDuplicates} onChange={() => setShowDuplicates((v) => !v)} className="w-4 h-4 rounded border border-white/30 bg-white/5 disabled:opacity-30" />
                    Show already imported
                  </label>
                )}
              </div>

              <div className="rounded-xl border border-white/10 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-white/5 text-xs text-white/50">
                    <tr>
                      <th className="px-3 py-2 text-left w-8"></th>
                      <th className="px-3 py-2 text-left">Date</th>
                      <th className="px-3 py-2 text-left">Merchant</th>
                      <th className="px-3 py-2 text-right">Amount</th>
                      <th className="px-3 py-2 text-left">Category</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((r) => (
                      <tr key={r.txn_hash} className={`border-t border-white/5 ${r.duplicate || !r.include ? 'opacity-40' : ''}`}>
                        <td className="px-3 py-2">
                          <input type="checkbox" checked={r.include && !r.duplicate} disabled={r.duplicate} onChange={() => toggle(r.txn_hash)} aria-label="Include transaction" className="w-4 h-4 rounded border border-white/30 bg-white/5 disabled:opacity-30" />
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-white/70">{r.date}</td>
                        <td className="px-3 py-2" title={r.description}>
                          <div>{r.merchant}</div>
                          <div className="text-xs text-white/35 truncate max-w-xs">{r.duplicate ? 'already imported' : r.description}</div>
                        </td>
                        <td className={`px-3 py-2 text-right whitespace-nowrap ${r.direction === 'debit' ? 'text-orange-300' : 'text-emerald-300'}`}>
                          {r.direction === 'debit' ? '−' : '+'}{formatINR(r.amount)}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-2">
                            <select
                              value={r.category}
                              disabled={r.duplicate}
                              onChange={(e) => setCategory(r.merchant, e.target.value)}
                              className="bg-black/40 border border-white/20 rounded-lg px-2 py-1 text-sm capitalize"
                            >
                              {preview.categories.map((c) => <option key={c} value={c}>{c}</option>)}
                            </select>
                            {!r.duplicate && r.category === r.suggested_category && (
                              <span className={`text-[10px] ${r.category_source === 'default' ? 'text-amber-300' : 'text-white/35'}`}>
                                {SOURCE_LABEL[r.category_source]}
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-white/40">
                “income” and “transfer” rows are kept for your history but aren't counted as spending.
              </p>
            </>
          )}

          {result && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-5 space-y-2">
              <div className="text-lg font-semibold text-emerald-300">Imported {result.imported} transactions</div>
              <div className="text-sm text-white/70">
                {result.expenses_created} added to your budget as expenses
                {result.skipped_duplicates > 0 && ` · ${result.skipped_duplicates} already imported, skipped`}
                {result.excluded > 0 && ` · ${result.excluded} excluded`}
                {result.rules_learned > 0 && ` · learned ${result.rules_learned} category rule${result.rules_learned > 1 ? 's' : ''}`}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/10">
          {preview && !result && (
            <>
              <button onClick={reset} disabled={busy} className="rounded-lg border border-white/20 px-4 py-2 text-sm">Choose another file</button>
              <button
                onClick={handleConfirm}
                disabled={busy || included.length === 0}
                className="rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 px-5 py-2 font-medium text-black disabled:opacity-50"
              >
                {busy ? 'Importing…' : `Import ${included.length} transactions`}
              </button>
            </>
          )}
          {result && (
            <>
              <button onClick={handleUndo} disabled={busy} className="rounded-lg border border-red-400/40 text-red-300 px-4 py-2 text-sm">Undo this import</button>
              <button onClick={close} className="rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 px-5 py-2 font-medium text-black">Done</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

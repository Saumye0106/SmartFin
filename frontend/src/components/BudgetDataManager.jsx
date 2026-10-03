import { useEffect, useState } from 'react';
import api from '../services/api';

const formatINR = (v) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(v || 0));

const CONFIRM_WORD = 'DELETE';

// Lets a user remove their own budget history: undo any past import, clear one month, or clear everything.
export default function BudgetDataManager({ month, refreshKey, onChanged }) {
  const [open, setOpen] = useState(false);
  const [overview, setOverview] = useState(null);
  const [batches, setBatches] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [pending, setPending] = useState(null); // { type: 'batch' | 'month', id } awaiting a second click
  const [confirmText, setConfirmText] = useState('');

  const load = async () => {
    try {
      const [o, b] = await Promise.all([api.getBudgetDataOverview(), api.listImportBatches()]);
      setOverview(o);
      setBatches(b.batches || []);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (open) load();
  }, [open, refreshKey]);

  const run = async (action, describe) => {
    setBusy(true); setError(null); setMessage(null);
    try {
      const res = await action();
      setMessage(describe(res));
      setPending(null); setConfirmText('');
      await load();
      onChanged?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const undoBatch = (b) => run(
    () => api.undoStatementImport(b.batch_id),
    (r) => `Import removed: ${r.transactions_removed} transactions and ${r.expenses_removed} expenses.`);
  const deleteMonth = () => run(
    () => api.deleteBudgetMonth(month),
    (r) => `${month} cleared: ${r.expenses_removed} expenses and ${r.transactions_removed} imported transactions removed.`);
  const deleteAll = () => run(
    () => api.deleteAllBudgetData(),
    (r) => `All budget history deleted: ${r.expenses_removed} expenses, ${r.transactions_removed} imported transactions, ${r.budgets_removed} monthly budgets.`);

  const isPending = (type, id) => pending?.type === type && pending?.id === id;
  const nothingStored = overview && overview.expenses === 0 && overview.budgets === 0 && overview.transactions === 0;

  return (
    <section className="rounded-2xl border border-white/10 bg-black/30 p-6">
      <button type="button" onClick={() => setOpen((v) => !v)} className="w-full flex items-center justify-between text-left">
        <div>
          <h2 className="text-xl font-semibold">Manage data</h2>
          <p className="text-xs text-white/50 mt-1">Undo an import, clear a month, or delete your budget history.</p>
        </div>
        <span className="text-white/50 text-sm">{open ? 'Hide' : 'Show'}</span>
      </button>

      {open && (
        <div className="mt-5 space-y-6">
          {error && <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</div>}
          {message && <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">{message}</div>}

          {overview && (
            <p className="text-sm text-white/60">
              {nothingStored ? 'Nothing is stored for your account.' : (
                <>Stored for your account: {overview.expenses} expenses
                  {overview.first_expense_date ? ` (${overview.first_expense_date} to ${overview.last_expense_date})` : ''},
                  {' '}{overview.budgets} monthly budgets, {overview.transactions} imported transactions,
                  {' '}{overview.category_rules} learned category rules.</>
              )}
            </p>
          )}

          <div>
            <h3 className="text-sm font-medium text-white/80 mb-2">Past imports</h3>
            {batches.length === 0 ? (
              <p className="text-xs text-white/40">No imported statements.</p>
            ) : (
              <ul className="space-y-2">
                {batches.map((b) => (
                  <li key={b.batch_id} className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm">
                    <div>
                      <div>{b.period_start} to {b.period_end}</div>
                      <div className="text-xs text-white/40">
                        {b.transactions} transactions, {b.expenses} added as expenses · out {formatINR(b.total_debit)} · in {formatINR(b.total_credit)}
                        {b.imported_at ? ` · imported ${String(b.imported_at).slice(0, 10)}` : ''}
                      </div>
                    </div>
                    {isPending('batch', b.batch_id) ? (
                      <div className="flex gap-2 shrink-0">
                        <button type="button" disabled={busy} onClick={() => undoBatch(b)} className="rounded-lg bg-red-500/80 hover:bg-red-500 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50">
                          {busy ? 'Removing…' : 'Yes, remove it'}
                        </button>
                        <button type="button" disabled={busy} onClick={() => setPending(null)} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs">Cancel</button>
                      </div>
                    ) : (
                      <button type="button" disabled={busy} onClick={() => setPending({ type: 'batch', id: b.batch_id })} className="shrink-0 rounded-lg border border-red-400/40 text-red-300 px-3 py-1.5 text-xs">
                        Undo import
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-xl border border-white/10 bg-black/30 px-4 py-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div className="text-sm">
              <div>Delete {month}</div>
              <div className="text-xs text-white/40">Removes that month's expenses, imported transactions, income and planned budget.</div>
            </div>
            {isPending('month', month) ? (
              <div className="flex gap-2 shrink-0">
                <button type="button" disabled={busy} onClick={deleteMonth} className="rounded-lg bg-red-500/80 hover:bg-red-500 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50">
                  {busy ? 'Deleting…' : `Yes, delete ${month}`}
                </button>
                <button type="button" disabled={busy} onClick={() => setPending(null)} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs">Cancel</button>
              </div>
            ) : (
              <button type="button" disabled={busy} onClick={() => setPending({ type: 'month', id: month })} className="shrink-0 rounded-lg border border-red-400/40 text-red-300 px-3 py-1.5 text-xs">
                Delete this month
              </button>
            )}
          </div>

          <div className="rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-4 space-y-3">
            <div className="text-sm">
              <div className="text-red-300 font-medium">Delete all budget history</div>
              <div className="text-xs text-white/50 mt-1">
                Removes every expense, monthly budget, imported transaction and learned category rule for your account.
                Loans, goals and your profile are not touched. This cannot be undone.
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder={`Type ${CONFIRM_WORD} to confirm`}
                aria-label={`Type ${CONFIRM_WORD} to confirm`}
                className="flex-1 bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
              />
              <button
                type="button"
                disabled={busy || confirmText !== CONFIRM_WORD || nothingStored}
                onClick={deleteAll}
                className="rounded-lg bg-red-500/80 hover:bg-red-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {busy ? 'Deleting…' : 'Delete everything'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

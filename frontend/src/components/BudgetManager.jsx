import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import api from '../services/api';

const CATEGORY_OPTIONS = [
  'rent',
  'food',
  'travel',
  'shopping',
  'emi',
  'utilities',
  'healthcare',
  'education',
  'insurance',
  'other'
];

const formatINR = (value) =>
  `Rs. ${Number(value || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  })}`;

const currentMonth = () => new Date().toISOString().slice(0, 7);
const todayDate = () => new Date().toISOString().slice(0, 10);

function BudgetManager() {
  const navigate = useNavigate();

  const [month, setMonth] = useState(currentMonth());
  const [summary, setSummary] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingBudget, setSavingBudget] = useState(false);
  const [savingExpense, setSavingExpense] = useState(false);
  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [error, setError] = useState(null);
  const [editingExpenseId, setEditingExpenseId] = useState(null);
  const [editExpenseForm, setEditExpenseForm] = useState({
    expense_date: '',
    category: 'other',
    amount: '',
    note: ''
  });

  const [budgetForm, setBudgetForm] = useState({
    monthly_income: '',
    planned_savings: '',
    category_budgets: Object.fromEntries(CATEGORY_OPTIONS.map((c) => [c, '']))
  });

  const [expenseForm, setExpenseForm] = useState({
    expense_date: todayDate(),
    category: 'food',
    amount: '',
    note: ''
  });

  const guidanceList = useMemo(() => {
    if (!analysisResult?.guidance) return [];
    if (Array.isArray(analysisResult.guidance)) return analysisResult.guidance;
    if (Array.isArray(analysisResult.guidance.immediate_actions)) {
      return analysisResult.guidance.immediate_actions;
    }
    if (Array.isArray(analysisResult.guidance.actions)) {
      return analysisResult.guidance.actions;
    }
    return [];
  }, [analysisResult]);

  const categoryComparison = useMemo(() => {
    const rows = summary?.category_comparison || [];
    return [...rows]
      .filter((row) => Number(row.actual || 0) > 0 || Number(row.planned || 0) > 0)
      .sort((a, b) => Number(b.actual || 0) - Number(a.actual || 0));
  }, [summary]);

  const fetchMonthData = async (selectedMonth) => {
    try {
      setLoading(true);
      setError(null);
      setAnalysisResult(null);

      const [summaryResponse, expensesResponse] = await Promise.all([
        api.getBudgetSummary(selectedMonth),
        api.getExpenses({ month: selectedMonth, limit: 500 })
      ]);

      const nextSummary = summaryResponse.summary;
      setSummary(nextSummary);
      setExpenses(expensesResponse.expenses || []);

      const budget = nextSummary?.budget;
      const planned = nextSummary?.planned_categories || {};
      setBudgetForm({
        monthly_income: budget ? String(budget.monthly_income ?? '') : '',
        planned_savings: budget ? String(budget.planned_savings ?? '') : '',
        category_budgets: Object.fromEntries(
          CATEGORY_OPTIONS.map((category) => [
            category,
            planned[category] !== undefined ? String(planned[category]) : ''
          ])
        )
      });
    } catch (err) {
      setError(err.message || 'Failed to load budget data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonthData(month);
  }, [month]);

  const handleSaveBudget = async (e) => {
    e.preventDefault();
    try {
      setSavingBudget(true);
      setError(null);
      const categoryPayload = Object.fromEntries(
        CATEGORY_OPTIONS.map((category) => [
          category,
          Number(budgetForm.category_budgets[category] || 0)
        ])
      );

      const response = await api.upsertMonthlyBudget({
        month,
        monthly_income: Number(budgetForm.monthly_income || 0),
        planned_savings: Number(budgetForm.planned_savings || 0),
        category_budgets: categoryPayload
      });

      setSummary(response.summary);
    } catch (err) {
      setError(err.message || 'Failed to save monthly budget');
    } finally {
      setSavingBudget(false);
    }
  };

  const handleAddExpense = async (e) => {
    e.preventDefault();
    try {
      setSavingExpense(true);
      setError(null);
      await api.addExpense({
        expense_date: expenseForm.expense_date,
        category: expenseForm.category,
        amount: Number(expenseForm.amount || 0),
        note: expenseForm.note
      });
      setExpenseForm({ ...expenseForm, amount: '', note: '' });
      await fetchMonthData(month);
    } catch (err) {
      setError(err.message || 'Failed to add expense');
    } finally {
      setSavingExpense(false);
    }
  };

  const handleDeleteExpense = async (expenseId) => {
    if (!window.confirm('Delete this expense entry?')) return;
    try {
      setError(null);
      await api.deleteExpense(expenseId);
      await fetchMonthData(month);
    } catch (err) {
      setError(err.message || 'Failed to delete expense');
    }
  };

  const handleStartEditExpense = (expense) => {
    setEditingExpenseId(expense.id);
    setEditExpenseForm({
      expense_date: expense.expense_date,
      category: expense.category || 'other',
      amount: String(expense.amount || ''),
      note: expense.note || ''
    });
  };

  const handleCancelEditExpense = () => {
    setEditingExpenseId(null);
    setEditExpenseForm({
      expense_date: '',
      category: 'other',
      amount: '',
      note: ''
    });
  };

  const handleSaveExpenseEdit = async (expenseId) => {
    try {
      setError(null);
      await api.updateExpense(expenseId, {
        expense_date: editExpenseForm.expense_date,
        category: editExpenseForm.category,
        amount: Number(editExpenseForm.amount || 0),
        note: editExpenseForm.note
      });
      handleCancelEditExpense();
      await fetchMonthData(month);
    } catch (err) {
      setError(err.message || 'Failed to update expense');
    }
  };

  const handleAnalyzeFromBudget = async () => {
    try {
      setRunningAnalysis(true);
      setError(null);
      const response = await api.predictFromBudget(month);
      setAnalysisResult(response);
    } catch (err) {
      setError(err.message || 'Failed to analyze budget data');
    } finally {
      setRunningAnalysis(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030303] text-white">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] right-[10%] w-[600px] h-[600px] bg-emerald-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-orange-500/10 rounded-full blur-[100px] mix-blend-screen"></div>
      </div>

      <Sidebar />

      <nav className="fixed top-0 left-0 w-full z-50">
        <div className="absolute inset-0 bg-black/50 backdrop-blur-md border-b border-white/5"></div>
        <div className="max-w-7xl mx-auto px-6 h-16 relative flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-3 group transition-all hover:opacity-80"
          >
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-emerald-500/50 transition-colors">
              <iconify-icon icon="solar:wallet-money-linear" className="text-emerald-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">BUDGET MANAGER</span>
          </button>

          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium"
          >
            <iconify-icon icon="solar:arrow-left-linear" width="16"></iconify-icon>
            <span>Back to Dashboard</span>
          </button>
        </div>
      </nav>

      <div className="relative z-10 pt-24 pb-12 px-6 ml-20">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-emerald-400 to-orange-300 bg-clip-text text-transparent">
                Budget Tracker and Expense Manager
              </h1>
              <p className="text-white/60">Track monthly budgets, log expenses, and run analysis from real spending data.</p>
            </div>
            <div className="flex items-center gap-3">
              <label className="text-xs text-white/60">Month</label>
              <input
                type="month"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                className="bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
              />
            </div>
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-white/10 bg-black/30 p-4">
              <div className="text-xs text-white/50">Income</div>
              <div className="text-xl font-semibold mt-1">{formatINR(summary?.monthly_income)}</div>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/30 p-4">
              <div className="text-xs text-white/50">Total Spent</div>
              <div className="text-xl font-semibold mt-1">{formatINR(summary?.total_spent)}</div>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/30 p-4">
              <div className="text-xs text-white/50">Planned Savings</div>
              <div className="text-xl font-semibold mt-1">{formatINR(summary?.planned_savings)}</div>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/30 p-4">
              <div className="text-xs text-white/50">Auto Savings</div>
              <div className="text-xl font-semibold mt-1">{formatINR(summary?.auto_calculated_savings)}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <section className="rounded-2xl border border-white/10 bg-black/30 p-6">
              <h2 className="text-xl font-semibold mb-4">Monthly Budget</h2>
              <form onSubmit={handleSaveBudget} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-white/50">Monthly Income</label>
                    <input
                      type="number"
                      min="0"
                      value={budgetForm.monthly_income}
                      onChange={(e) => setBudgetForm((prev) => ({ ...prev, monthly_income: e.target.value }))}
                      className="mt-1 w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-white/50">Planned Savings</label>
                    <input
                      type="number"
                      min="0"
                      value={budgetForm.planned_savings}
                      onChange={(e) => setBudgetForm((prev) => ({ ...prev, planned_savings: e.target.value }))}
                      className="mt-1 w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium mb-2 text-white/80">Category Budgets</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {CATEGORY_OPTIONS.map((category) => (
                      <div key={category}>
                        <label className="text-xs text-white/50 capitalize">{category}</label>
                        <input
                          type="number"
                          min="0"
                          value={budgetForm.category_budgets[category]}
                          onChange={(e) =>
                            setBudgetForm((prev) => ({
                              ...prev,
                              category_budgets: {
                                ...prev.category_budgets,
                                [category]: e.target.value
                              }
                            }))
                          }
                          className="mt-1 w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={savingBudget}
                  className="w-full rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 py-2.5 font-medium text-black disabled:opacity-50"
                >
                  {savingBudget ? 'Saving...' : 'Save Monthly Budget'}
                </button>
              </form>
            </section>

            <section className="rounded-2xl border border-white/10 bg-black/30 p-6">
              <h2 className="text-xl font-semibold mb-4">Add Expense</h2>
              <form onSubmit={handleAddExpense} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-white/50">Date</label>
                    <input
                      type="date"
                      value={expenseForm.expense_date}
                      onChange={(e) => setExpenseForm((prev) => ({ ...prev, expense_date: e.target.value }))}
                      className="mt-1 w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-white/50">Category</label>
                    <select
                      value={expenseForm.category}
                      onChange={(e) => setExpenseForm((prev) => ({ ...prev, category: e.target.value }))}
                      className="mt-1 w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
                    >
                      {CATEGORY_OPTIONS.map((category) => (
                        <option key={category} value={category}>
                          {category}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-white/50">Amount</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={expenseForm.amount}
                    onChange={(e) => setExpenseForm((prev) => ({ ...prev, amount: e.target.value }))}
                    className="mt-1 w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-white/50">Note</label>
                  <input
                    type="text"
                    value={expenseForm.note}
                    onChange={(e) => setExpenseForm((prev) => ({ ...prev, note: e.target.value }))}
                    className="mt-1 w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm"
                    placeholder="Optional"
                  />
                </div>
                <button
                  type="submit"
                  disabled={savingExpense}
                  className="w-full rounded-lg bg-gradient-to-r from-orange-400 to-orange-500 py-2.5 font-medium text-black disabled:opacity-50"
                >
                  {savingExpense ? 'Adding...' : 'Add Expense'}
                </button>
              </form>
            </section>
          </div>

          <section className="rounded-2xl border border-white/10 bg-black/30 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Expense Entries</h2>
              <button
                onClick={handleAnalyzeFromBudget}
                disabled={runningAnalysis || loading}
                className="rounded-lg bg-white py-2 px-4 text-sm font-semibold text-black disabled:opacity-50"
              >
                {runningAnalysis ? 'Analyzing...' : 'Run Analyzer from This Month'}
              </button>
            </div>

            <div className="mb-5 rounded-xl border border-white/10 bg-black/20 p-4">
              <h3 className="text-sm font-semibold text-white mb-3">Category Spend vs Plan</h3>
              {categoryComparison.length === 0 ? (
                <p className="text-xs text-white/55">Add budget categories and expenses to visualize category-level performance.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                  {categoryComparison.slice(0, 6).map((row) => {
                    const planned = Number(row.planned || 0);
                    const actual = Number(row.actual || 0);
                    const ratio = planned > 0 ? (actual / planned) * 100 : 100;
                    const variance = Number(row.variance || actual - planned);
                    const isOver = variance > 0;
                    return (
                      <div key={row.category} className="rounded-lg border border-white/10 bg-black/30 p-3">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-xs capitalize text-white/75">{row.category}</p>
                          <p className={`text-xs font-semibold ${isOver ? 'text-red-300' : 'text-emerald-300'}`}>
                            {isOver ? '+' : ''}{formatINR(variance)}
                          </p>
                        </div>
                        <div className="text-[11px] text-white/60 flex items-center justify-between mb-2">
                          <span>Planned {formatINR(planned)}</span>
                          <span>Actual {formatINR(actual)}</span>
                        </div>
                        <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                          <div
                            className={`h-full ${isOver ? 'bg-red-400' : 'bg-emerald-400'}`}
                            style={{ width: `${Math.min(130, Math.max(8, ratio))}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {loading ? (
              <p className="text-white/60 text-sm">Loading data...</p>
            ) : expenses.length === 0 ? (
              <p className="text-white/60 text-sm">No expenses recorded for this month.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-white/50 border-b border-white/10">
                      <th className="py-2">Date</th>
                      <th className="py-2">Category</th>
                      <th className="py-2">Amount</th>
                      <th className="py-2">Note</th>
                      <th className="py-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expenses.map((expense) => (
                      <tr key={expense.id} className="border-b border-white/5">
                        {editingExpenseId === expense.id ? (
                          <>
                            <td className="py-2">
                              <input
                                type="date"
                                value={editExpenseForm.expense_date}
                                onChange={(e) => setEditExpenseForm((prev) => ({ ...prev, expense_date: e.target.value }))}
                                className="w-full bg-black/40 border border-white/20 rounded px-2 py-1 text-xs"
                              />
                            </td>
                            <td className="py-2">
                              <select
                                value={editExpenseForm.category}
                                onChange={(e) => setEditExpenseForm((prev) => ({ ...prev, category: e.target.value }))}
                                className="w-full bg-black/40 border border-white/20 rounded px-2 py-1 text-xs capitalize"
                              >
                                {CATEGORY_OPTIONS.map((category) => (
                                  <option key={category} value={category}>{category}</option>
                                ))}
                              </select>
                            </td>
                            <td className="py-2">
                              <input
                                type="number"
                                min="1"
                                value={editExpenseForm.amount}
                                onChange={(e) => setEditExpenseForm((prev) => ({ ...prev, amount: e.target.value }))}
                                className="w-full bg-black/40 border border-white/20 rounded px-2 py-1 text-xs"
                              />
                            </td>
                            <td className="py-2">
                              <input
                                type="text"
                                value={editExpenseForm.note}
                                onChange={(e) => setEditExpenseForm((prev) => ({ ...prev, note: e.target.value }))}
                                className="w-full bg-black/40 border border-white/20 rounded px-2 py-1 text-xs"
                              />
                            </td>
                            <td className="py-2 text-right space-x-2">
                              <button
                                onClick={() => handleSaveExpenseEdit(expense.id)}
                                className="text-xs text-emerald-300 hover:text-emerald-200"
                              >
                                Save
                              </button>
                              <button
                                onClick={handleCancelEditExpense}
                                className="text-xs text-white/70 hover:text-white"
                              >
                                Cancel
                              </button>
                            </td>
                          </>
                        ) : (
                          <>
                            <td className="py-2 text-white/80">{expense.expense_date}</td>
                            <td className="py-2 capitalize text-white/80">{expense.category}</td>
                            <td className="py-2 text-white/90">{formatINR(expense.amount)}</td>
                            <td className="py-2 text-white/60">{expense.note || '-'}</td>
                            <td className="py-2 text-right space-x-2">
                              <button
                                onClick={() => handleStartEditExpense(expense)}
                                className="text-xs text-amber-300 hover:text-amber-200"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDeleteExpense(expense.id)}
                                className="text-xs text-red-300 hover:text-red-200"
                              >
                                Delete
                              </button>
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {analysisResult && (
            <section className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-6 space-y-4">
              <div className="flex flex-wrap items-center gap-4">
                <div>
                  <p className="text-xs text-emerald-200/80 uppercase">Financial Health Score</p>
                  <p className="text-3xl font-bold">{analysisResult.score}</p>
                </div>
                <div className="text-sm text-emerald-100/90">
                  {analysisResult.classification?.category || 'Result'} for {analysisResult.month}
                </div>
              </div>
              {guidanceList.length > 0 && (
                <ul className="text-sm text-emerald-100/90 list-disc pl-5 space-y-1">
                  {guidanceList.slice(0, 4).map((item, idx) => (
                    <li key={idx}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
                  ))}
                </ul>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

export default BudgetManager;

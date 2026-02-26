import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './GoalsManager.css';

function GoalsManager() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [formData, setFormData] = useState({
    goal_type: 'long-term',
    target_amount: '',
    target_date: '',
    priority: 'medium',
    description: ''
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchGoals();
  }, []);

  const fetchGoals = async () => {
    try {
      setLoading(true);
      const data = await api.getGoals();
      setGoals(data.goals || []);
    } catch (err) {
      console.error('Error fetching goals:', err);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.target_amount || parseFloat(formData.target_amount) <= 0) {
      newErrors.target_amount = 'Target amount must be greater than 0';
    }

    if (!formData.target_date) {
      newErrors.target_date = 'Target date is required';
    } else {
      const targetDate = new Date(formData.target_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (targetDate <= today) {
        newErrors.target_date = 'Target date must be in the future';
      }
    }

    if (formData.description && formData.description.length > 500) {
      newErrors.description = 'Description must be 500 characters or less';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleCreateClick = () => {
    setFormData({
      goal_type: 'long-term',
      target_amount: '',
      target_date: '',
      priority: 'medium',
      description: ''
    });
    setEditingGoal(null);
    setShowCreateForm(true);
    setErrors({});
  };

  const handleEditClick = (goal) => {
    setFormData({
      goal_type: goal.goal_type,
      target_amount: goal.target_amount,
      target_date: goal.target_date,
      priority: goal.priority,
      description: goal.description || '',
      status: goal.status
    });
    setEditingGoal(goal);
    setShowCreateForm(true);
    setErrors({});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);

    try {
      const submitData = {
        goal_type: formData.goal_type,
        target_amount: parseFloat(formData.target_amount),
        target_date: formData.target_date,
        priority: formData.priority,
        description: formData.description || undefined
      };

      if (editingGoal) {
        submitData.status = formData.status;
        await api.updateGoal(editingGoal.id, submitData);
      } else {
        await api.createGoal(submitData);
      }

      setShowCreateForm(false);
      setEditingGoal(null);
      fetchGoals();
    } catch (err) {
      setErrors({ submit: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (goalId) => {
    if (!window.confirm('Are you sure you want to delete this goal?')) {
      return;
    }

    try {
      await api.deleteGoal(goalId);
      fetchGoals();
    } catch (err) {
      alert('Failed to delete goal: ' + err.message);
    }
  };

  const handleCancel = () => {
    setShowCreateForm(false);
    setEditingGoal(null);
    setErrors({});
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      active: '#3b82f6',
      completed: '#10b981',
      cancelled: '#6b7280'
    };
    return colors[status] || '#6b7280';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-[#030303] text-white">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-emerald-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-green-500/15 rounded-full blur-[100px] mix-blend-screen"></div>
      </div>

      {/* Navigation Header */}
      <nav className="fixed top-0 left-0 w-full z-50 transition-all duration-300">
        <div className="absolute inset-0 bg-black/50 backdrop-blur-md border-b border-white/5"></div>
        <div className="max-w-7xl mx-auto px-6 h-16 relative flex items-center justify-between">
          {/* Logo */}
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-3 group transition-all hover:opacity-80"
          >
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-emerald-500/50 transition-colors">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-emerald-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">GOALS</span>
          </button>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <div className="text-[10px] font-mono text-emerald-400 bg-emerald-950/20 px-3 py-1.5 rounded-full border border-emerald-500/20">
              {currentTime.toLocaleTimeString('en-US', { hour12: false })}
            </div>
            <button
              onClick={() => navigate('/profile')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium"
            >
              <iconify-icon icon="solar:arrow-left-linear" width="16"></iconify-icon>
              <span className="hidden md:inline">Back to Profile</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-16 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <section className="mb-12">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-xs text-white/50 font-medium tracking-widest uppercase">Goal Management</span>
            </div>
            <div className="flex items-start justify-between gap-6">
              <div>
                <h1 className="font-display text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
                  Financial <span className="text-gradient">Goals</span>
                </h1>
                <p className="text-white/50 max-w-2xl">
                  Track and manage your financial objectives with precision
                </p>
              </div>
              <button 
                onClick={handleCreateClick} 
                className="flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 border border-emerald-400/20 transition-all text-sm font-semibold shadow-lg shadow-emerald-900/30"
              >
                <iconify-icon icon="solar:add-circle-linear" width="20"></iconify-icon>
                Create Goal
              </button>
            </div>
          </section>

          {/* Loading State */}
          {loading && (
            <div className="glass-panel rounded-xl p-12 text-center mb-12">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6 relative">
                <iconify-icon icon="solar:spinner-solid" className="text-emerald-400 text-3xl animate-spin"></iconify-icon>
                <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping"></div>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Loading Goals</h3>
              <p className="text-white/50 text-sm">Fetching your financial objectives...</p>
            </div>
          )}

          {/* Create/Edit Form Modal */}
          {showCreateForm && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/70 backdrop-blur-sm animate-fade-in">
              <div className="glass-panel rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-fade-in-up">
                {/* Form Header */}
                <div className="sticky top-0 bg-[#0a0a0a]/95 backdrop-blur-md border-b border-white/10 p-6 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                      <iconify-icon icon="solar:target-linear" className="text-emerald-400 text-xl"></iconify-icon>
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-white">{editingGoal ? 'Edit Goal' : 'Create New Goal'}</h2>
                      <p className="text-xs text-white/50">Define your financial objective</p>
                    </div>
                  </div>
                  <button 
                    onClick={handleCancel} 
                    className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center transition-all"
                  >
                    <iconify-icon icon="solar:close-circle-linear" className="text-white/60 text-xl"></iconify-icon>
                  </button>
                </div>

                {/* Form Content */}
                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                  {errors.submit && (
                    <div className="p-4 rounded-lg bg-danger-950/30 border border-danger-500/30 flex items-start gap-3">
                      <iconify-icon icon="solar:danger-triangle-linear" className="text-danger-400 mt-0.5 shrink-0"></iconify-icon>
                      <div className="text-sm text-danger-400">{errors.submit}</div>
                    </div>
                  )}

                  {/* Goal Type */}
                  <div className="space-y-2 group">
                    <label htmlFor="goal_type" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-emerald-400">
                      Goal Type
                    </label>
                    <select
                      id="goal_type"
                      name="goal_type"
                      value={formData.goal_type}
                      onChange={handleChange}
                      className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all"
                    >
                      <option value="short-term">Short-term (&lt; 3 years)</option>
                      <option value="long-term">Long-term (&gt; 3 years)</option>
                    </select>
                  </div>

                  {/* Target Amount & Date */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2 group">
                      <label htmlFor="target_amount" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-emerald-400">
                        Target Amount
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          id="target_amount"
                          name="target_amount"
                          value={formData.target_amount}
                          onChange={handleChange}
                          className={`w-full bg-[#0a0a0a] border ${errors.target_amount ? 'border-danger-500/50' : 'border-white/10'} rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all`}
                          placeholder="50000"
                          step="0.01"
                          min="0.01"
                        />
                        <iconify-icon icon="solar:dollar-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-emerald-400 transition-colors text-lg"></iconify-icon>
                      </div>
                      {errors.target_amount && (
                        <p className="text-[11px] text-danger-400 font-medium pl-1">{errors.target_amount}</p>
                      )}
                    </div>

                    <div className="space-y-2 group">
                      <label htmlFor="target_date" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-emerald-400">
                        Target Date
                      </label>
                      <div className="relative">
                        <input
                          type="date"
                          id="target_date"
                          name="target_date"
                          value={formData.target_date}
                          onChange={handleChange}
                          className={`w-full bg-[#0a0a0a] border ${errors.target_date ? 'border-danger-500/50' : 'border-white/10'} rounded-lg px-4 py-2.5 pl-10 text-sm text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all`}
                        />
                        <iconify-icon icon="solar:calendar-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-emerald-400 transition-colors text-lg"></iconify-icon>
                      </div>
                      {errors.target_date && (
                        <p className="text-[11px] text-danger-400 font-medium pl-1">{errors.target_date}</p>
                      )}
                    </div>
                  </div>

                  {/* Priority */}
                  <div className="space-y-2 group">
                    <label htmlFor="priority" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-emerald-400">
                      Priority
                    </label>
                    <select
                      id="priority"
                      name="priority"
                      value={formData.priority}
                      onChange={handleChange}
                      className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>

                  {/* Status (Edit Only) */}
                  {editingGoal && (
                    <div className="space-y-2 group">
                      <label htmlFor="status" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-emerald-400">
                        Status
                      </label>
                      <select
                        id="status"
                        name="status"
                        value={formData.status}
                        onChange={handleChange}
                        className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all"
                      >
                        <option value="active">Active</option>
                        <option value="completed">Completed</option>
                        <option value="cancelled">Cancelled</option>
                      </select>
                    </div>
                  )}

                  {/* Description */}
                  <div className="space-y-2 group">
                    <label htmlFor="description" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-emerald-400">
                      Description (Optional)
                    </label>
                    <textarea
                      id="description"
                      name="description"
                      value={formData.description}
                      onChange={handleChange}
                      className={`w-full bg-[#0a0a0a] border ${errors.description ? 'border-danger-500/50' : 'border-white/10'} rounded-lg px-4 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all resize-none`}
                      placeholder="Describe your goal..."
                      rows="3"
                      maxLength="500"
                    />
                    {errors.description && (
                      <p className="text-[11px] text-danger-400 font-medium pl-1">{errors.description}</p>
                    )}
                    <p className="text-[11px] text-white/30 pl-1">{formData.description.length}/500 characters</p>
                  </div>

                  {/* Form Actions */}
                  <div className="flex gap-3 pt-4">
                    <button
                      type="button"
                      onClick={handleCancel}
                      disabled={submitting}
                      className="flex-1 px-6 py-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 border border-emerald-400/20 transition-all text-sm font-semibold shadow-lg shadow-emerald-900/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {submitting ? (
                        <>
                          <iconify-icon icon="solar:spinner-solid" className="animate-spin text-lg"></iconify-icon>
                          Saving...
                        </>
                      ) : (
                        <>
                          <iconify-icon icon="solar:check-circle-linear" width="18"></iconify-icon>
                          {editingGoal ? 'Update Goal' : 'Create Goal'}
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Goals Content */}
          {!loading && (
            <section>
              {goals.length === 0 ? (
                <div className="glass-panel rounded-xl p-12 text-center">
                  <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
                    <iconify-icon icon="solar:target-linear" className="text-emerald-400 text-4xl"></iconify-icon>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">No Goals Yet</h3>
                  <p className="text-white/50 mb-6 max-w-md mx-auto">
                    Create your first financial goal to start tracking your progress toward financial freedom
                  </p>
                  <button 
                    onClick={handleCreateClick} 
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 border border-emerald-400/20 transition-all text-sm font-semibold shadow-lg shadow-emerald-900/30"
                  >
                    <iconify-icon icon="solar:add-circle-linear" width="20"></iconify-icon>
                    Create Your First Goal
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {goals.map(goal => (
                    <div key={goal.id} className="glass-panel glass-panel-hover rounded-xl p-6 border border-white/10 flex flex-col">
                      {/* Card Header */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex flex-wrap gap-2">
                          <span 
                            className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider"
                            style={{ 
                              backgroundColor: `${getPriorityColor(goal.priority)}20`,
                              color: getPriorityColor(goal.priority),
                              border: `1px solid ${getPriorityColor(goal.priority)}40`
                            }}
                          >
                            {goal.priority}
                          </span>
                          <span 
                            className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider"
                            style={{ 
                              backgroundColor: `${getStatusBadge(goal.status)}20`,
                              color: getStatusBadge(goal.status),
                              border: `1px solid ${getStatusBadge(goal.status)}40`
                            }}
                          >
                            {goal.status}
                          </span>
                        </div>
                        <span className="text-[10px] text-white/40 uppercase tracking-wider font-medium">
                          {goal.goal_type}
                        </span>
                      </div>

                      {/* Card Body */}
                      <div className="flex-1 mb-4">
                        <div className="text-3xl font-bold text-white mb-2">
                          {formatCurrency(goal.target_amount)}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-white/50 mb-3">
                          <iconify-icon icon="solar:calendar-linear" width="16"></iconify-icon>
                          <span>Target: {formatDate(goal.target_date)}</span>
                        </div>
                        {goal.description && (
                          <p className="text-sm text-white/60 line-clamp-2">
                            {goal.description}
                          </p>
                        )}
                      </div>

                      {/* Card Actions */}
                      <div className="flex gap-2 pt-4 border-t border-white/5">
                        <button
                          onClick={() => handleEditClick(goal)}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-semibold"
                        >
                          <iconify-icon icon="solar:pen-linear" width="16"></iconify-icon>
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(goal.id)}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-danger-950/30 hover:bg-danger-950/50 border border-danger-500/30 hover:border-danger-500/50 transition-all text-xs font-semibold text-danger-400"
                        >
                          <iconify-icon icon="solar:trash-bin-trash-linear" width="16"></iconify-icon>
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-20 border-t border-white/10 bg-black/50 backdrop-blur-md py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-emerald-400 text-lg"></iconify-icon>
                <span className="font-display font-bold text-white">SmartFin</span>
                <span className="text-[10px] text-white/30 font-mono">v2.0.4</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                <span className="text-white/40">System Operational</span>
              </div>
            </div>
            <div className="text-xs text-white/30">
              Educational Use Only • College Project
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default GoalsManager;

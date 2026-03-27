import { useState } from 'react';

const RetirementInputForm = ({ onPlanCreated }) => {
  const userId = localStorage.getItem('userId') || 1;
  const [formData, setFormData] = useState({
    user_id: parseInt(userId),
    plan_name: '',
    current_age: 30,
    retirement_age: 65,
    current_salary: 500000,
    current_monthly_expenses: 30000,
    current_savings: 100000,
    inflation_rate: 0.06,
    investment_return_rate: 0.10,
    life_expectancy: 85,
    desired_retirement_lifestyle: null
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const monthlySalaryPreview = Number(formData.current_salary) > 0
    ? Number(formData.current_salary) / 12
    : 0;
  const autoMonthlySavings = Math.max(
    0,
    monthlySalaryPreview - (Number(formData.current_monthly_expenses) || 0)
  );

  const formatCompactCurrency = (value) => `₹${new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0
  }).format(value)}`;

  const handleChange = (e) => {
    const { name, value } = e.target;
    let newValue = value;
    
    if (name !== 'plan_name') {
      const parsed = parseFloat(value);
      newValue = isNaN(parsed) ? value : parsed;
    }
    
    setFormData(prev => {
      const updated = {
        ...prev,
        [name]: newValue
      };

      // Auto-fill savings from monthly salary minus monthly expenses
      // whenever salary or expenses changes.
      if (name === 'current_salary' || name === 'current_monthly_expenses') {
        const annualSalary = Number(name === 'current_salary' ? newValue : updated.current_salary) || 0;
        const monthlyExpenses = Number(name === 'current_monthly_expenses' ? newValue : updated.current_monthly_expenses) || 0;
        const monthlySalary = annualSalary / 12;
        updated.current_savings = Math.max(0, monthlySalary - monthlyExpenses);
      }

      return updated;
    });
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (formData.current_age < 18 || formData.current_age > 75) {
      newErrors.current_age = 'Age must be between 18 and 75';
    }

    if (formData.retirement_age <= formData.current_age || formData.retirement_age > 75) {
      newErrors.retirement_age = 'Retirement age must be greater than current age and <= 75';
    }

    if (formData.current_salary <= 0) {
      newErrors.current_salary = 'Salary must be positive';
    }

    if (formData.current_monthly_expenses <= 0) {
      newErrors.current_monthly_expenses = 'Monthly expenses must be positive';
    }

    if (formData.current_savings < 0) {
      newErrors.current_savings = 'Savings cannot be negative';
    }

    if (formData.inflation_rate < 0.02 || formData.inflation_rate > 0.15) {
      newErrors.inflation_rate = 'Inflation rate must be between 2% and 15%';
    }

    if (formData.investment_return_rate < 0.05 || formData.investment_return_rate > 0.30) {
      newErrors.investment_return_rate = 'Return rate must be between 5% and 30%';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Ensure all required numeric fields have valid values
    const sanitizedData = {
      ...formData,
      current_salary: formData.current_salary || 500000,
      current_monthly_expenses: formData.current_monthly_expenses || 30000,
      current_savings: formData.current_savings || 0,
      inflation_rate: formData.inflation_rate || 0.06,
      investment_return_rate: formData.investment_return_rate || 0.10,
      life_expectancy: formData.life_expectancy || 85
    };

    setLoading(true);
    try {
      onPlanCreated(sanitizedData);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:calculator-linear" className="text-purple-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Retirement Plan Details</h2>
          <p className="text-xs text-white/50">Enter your financial information to calculate your retirement plan</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Plan Name */}
        <div className="space-y-2 group">
          <label htmlFor="plan_name" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-purple-400">
            Plan Name
          </label>
          <div className="relative">
            <input
              type="text"
              id="plan_name"
              name="plan_name"
              value={formData.plan_name}
              onChange={handleChange}
              placeholder="e.g., My Retirement Plan"
              className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all"
            />
            <iconify-icon icon="solar:document-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-purple-400 transition-colors text-lg"></iconify-icon>
          </div>
        </div>

        {/* Age Section */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2 group">
            <label htmlFor="current_age" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-purple-400">
              Current Age
            </label>
            <div className="relative">
              <input
                type="number"
                id="current_age"
                name="current_age"
                value={formData.current_age}
                onChange={handleChange}
                min="18"
                max="75"
                className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 transition-all ${
                  errors.current_age ? 'border-danger-500/50 focus:border-danger-500/50 focus:ring-danger-500/50' : 'border-white/10 focus:border-purple-500/50 focus:ring-purple-500/50'
                }`}
              />
              <iconify-icon icon="solar:calendar-linear" className={`absolute left-3.5 top-3 transition-colors text-lg ${errors.current_age ? 'text-danger-400' : 'text-white/30 group-focus-within:text-purple-400'}`}></iconify-icon>
            </div>
            {errors.current_age && <p className="text-danger-400 text-xs mt-1">{errors.current_age}</p>}
          </div>

          <div className="space-y-2 group">
            <label htmlFor="retirement_age" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-purple-400">
              Retirement Age
            </label>
            <div className="relative">
              <input
                type="number"
                id="retirement_age"
                name="retirement_age"
                value={formData.retirement_age}
                onChange={handleChange}
                min="18"
                max="75"
                className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 transition-all ${
                  errors.retirement_age ? 'border-danger-500/50 focus:border-danger-500/50 focus:ring-danger-500/50' : 'border-white/10 focus:border-purple-500/50 focus:ring-purple-500/50'
                }`}
              />
              <iconify-icon icon="solar:calendar-linear" className={`absolute left-3.5 top-3 transition-colors text-lg ${errors.retirement_age ? 'text-danger-400' : 'text-white/30 group-focus-within:text-purple-400'}`}></iconify-icon>
            </div>
            {errors.retirement_age && <p className="text-danger-400 text-xs mt-1">{errors.retirement_age}</p>}
          </div>
        </div>

        {/* Salary and Expenses */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2 group">
            <label htmlFor="current_salary" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-purple-400">
              Annual Salary (₹)
            </label>
            <div className="relative">
              <input
                type="number"
                id="current_salary"
                name="current_salary"
                value={formData.current_salary}
                onChange={handleChange}
                min="0"
                className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 transition-all ${
                  errors.current_salary ? 'border-danger-500/50 focus:border-danger-500/50 focus:ring-danger-500/50' : 'border-white/10 focus:border-purple-500/50 focus:ring-purple-500/50'
                }`}
              />
              <iconify-icon icon="solar:wallet-linear" className={`absolute left-3.5 top-3 transition-colors text-lg ${errors.current_salary ? 'text-danger-400' : 'text-white/30 group-focus-within:text-purple-400'}`}></iconify-icon>
            </div>
            <p className="text-[11px] text-white/45 mt-1">
              Monthly salary preview: {formatCompactCurrency(monthlySalaryPreview)}
            </p>
            {errors.current_salary && <p className="text-danger-400 text-xs mt-1">{errors.current_salary}</p>}
          </div>

          <div className="space-y-2 group">
            <label htmlFor="current_monthly_expenses" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-purple-400">
              Monthly Expenses (₹)
            </label>
            <div className="relative">
              <input
                type="number"
                id="current_monthly_expenses"
                name="current_monthly_expenses"
                value={formData.current_monthly_expenses}
                onChange={handleChange}
                min="0"
                className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 transition-all ${
                  errors.current_monthly_expenses ? 'border-danger-500/50 focus:border-danger-500/50 focus:ring-danger-500/50' : 'border-white/10 focus:border-purple-500/50 focus:ring-purple-500/50'
                }`}
              />
              <iconify-icon icon="solar:wallet-money-linear" className={`absolute left-3.5 top-3 transition-colors text-lg ${errors.current_monthly_expenses ? 'text-danger-400' : 'text-white/30 group-focus-within:text-purple-400'}`}></iconify-icon>
            </div>
            <p className="text-[11px] text-white/45 mt-1">
              Auto monthly savings: {formatCompactCurrency(autoMonthlySavings)}
            </p>
            {errors.current_monthly_expenses && <p className="text-danger-400 text-xs mt-1">{errors.current_monthly_expenses}</p>}
          </div>
        </div>

        {/* Savings and Lifestyle */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2 group">
            <label htmlFor="current_savings" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-purple-400">
              Current Savings (₹)
            </label>
            <div className="relative">
              <input
                type="number"
                id="current_savings"
                name="current_savings"
                value={formData.current_savings}
                onChange={handleChange}
                min="0"
                className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 transition-all ${
                  errors.current_savings ? 'border-danger-500/50 focus:border-danger-500/50 focus:ring-danger-500/50' : 'border-white/10 focus:border-purple-500/50 focus:ring-purple-500/50'
                }`}
              />
              <iconify-icon icon="solar:piggy-bank-linear" className={`absolute left-3.5 top-3 transition-colors text-lg ${errors.current_savings ? 'text-danger-400' : 'text-white/30 group-focus-within:text-purple-400'}`}></iconify-icon>
            </div>
            <p className="text-[11px] text-white/45 mt-1">
              Auto-filled from monthly salary - monthly expenses.
            </p>
            {errors.current_savings && <p className="text-danger-400 text-xs mt-1">{errors.current_savings}</p>}
          </div>

          <div className="space-y-2 group">
            <label htmlFor="desired_retirement_lifestyle" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-purple-400">
              Desired Retirement Lifestyle (₹/month)
            </label>
            <div className="relative">
              <input
                type="number"
                id="desired_retirement_lifestyle"
                name="desired_retirement_lifestyle"
                value={formData.desired_retirement_lifestyle || ''}
                onChange={handleChange}
                min="0"
                placeholder="Leave blank to use current expenses"
                className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all"
              />
              <iconify-icon icon="solar:home-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-purple-400 transition-colors text-lg"></iconify-icon>
            </div>
          </div>
        </div>

        {/* Investment Parameters */}
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2 group">
            <label htmlFor="inflation_rate" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-green-400">
              Inflation Rate (%)
            </label>
            <div className="relative">
              <input
                type="number"
                id="inflation_rate"
                value={formData.inflation_rate * 100}
                onChange={(e) => setFormData(prev => ({ ...prev, inflation_rate: parseFloat(e.target.value) / 100 }))}
                min="2"
                max="15"
                step="0.1"
                placeholder="e.g., 6"
                className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 transition-all ${
                  errors.inflation_rate ? 'border-danger-500/50 focus:border-danger-500/50 focus:ring-danger-500/50' : 'border-white/10 focus:border-green-500/50 focus:ring-green-500/50'
                }`}
              />
              <iconify-icon icon="solar:chart-2-linear" className={`absolute left-3.5 top-3 transition-colors text-lg ${errors.inflation_rate ? 'text-danger-400' : 'text-white/30 group-focus-within:text-green-400'}`}></iconify-icon>
            </div>
            <p className="text-[10px] text-white/40 mt-1">Low: 2-4% | Standard: 5-6% | High: 7-8%</p>
            {errors.inflation_rate && <p className="text-danger-400 text-xs mt-1">{errors.inflation_rate}</p>}
          </div>

          <div className="space-y-2 group">
            <label htmlFor="investment_return_rate" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-green-400">
              Expected Return Rate (%)
            </label>
            <div className="relative">
              <input
                type="number"
                id="investment_return_rate"
                value={formData.investment_return_rate * 100}
                onChange={(e) => setFormData(prev => ({ ...prev, investment_return_rate: parseFloat(e.target.value) / 100 }))}
                min="5"
                max="30"
                step="0.1"
                placeholder="e.g., 10"
                className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 transition-all ${
                  errors.investment_return_rate ? 'border-danger-500/50 focus:border-danger-500/50 focus:ring-danger-500/50' : 'border-white/10 focus:border-green-500/50 focus:ring-green-500/50'
                }`}
              />
              <iconify-icon icon="solar:trending-up-linear" className={`absolute left-3.5 top-3 transition-colors text-lg ${errors.investment_return_rate ? 'text-danger-400' : 'text-white/30 group-focus-within:text-green-400'}`}></iconify-icon>
            </div>
            <p className="text-[10px] text-white/40 mt-1">Conservative: 5-7% | Moderate: 8-10% | Aggressive: 11-15%</p>
            {errors.investment_return_rate && <p className="text-danger-400 text-xs mt-1">{errors.investment_return_rate}</p>}
          </div>

          <div className="space-y-2 group">
            <label htmlFor="life_expectancy" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-green-400">
              Life Expectancy (years)
            </label>
            <div className="relative">
              <input
                type="number"
                id="life_expectancy"
                name="life_expectancy"
                value={formData.life_expectancy}
                onChange={handleChange}
                min="75"
                max="100"
                className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-green-500/50 focus:ring-1 focus:ring-green-500/50 transition-all"
              />
              <iconify-icon icon="solar:heart-linear" className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-green-400 transition-colors text-lg"></iconify-icon>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700 border border-purple-400/20 transition-all text-sm font-semibold shadow-lg shadow-purple-900/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <iconify-icon icon="solar:spinner-solid" className="animate-spin text-lg"></iconify-icon>
                Calculating...
              </>
            ) : (
              <>
                <iconify-icon icon="solar:calculator-linear" width="18"></iconify-icon>
                Calculate Retirement Plan
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default RetirementInputForm;

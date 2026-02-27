import { useState } from 'react';
import './LoanForm.css';

const LoanForm = ({ onSubmit, onCancel, loading, initialData = null }) => {
  const [formData, setFormData] = useState(initialData || {
    loan_type: 'personal',
    loan_amount: '',
    loan_tenure: '',
    monthly_emi: '',
    interest_rate: '',
    loan_start_date: '',
    loan_maturity_date: ''
  });

  const [errors, setErrors] = useState({});

  // Calculate EMI based on loan parameters
  const calculateEMI = (amount, tenure, rate) => {
    if (!amount || !tenure || rate === '') return '';
    
    const principal = Number(amount);
    const months = Number(tenure);
    const annualRate = Number(rate);
    
    if (principal <= 0 || months <= 0 || annualRate < 0) return '';
    
    if (annualRate === 0) {
      // Zero interest rate
      return (principal / months).toFixed(2);
    }
    
    const monthlyRate = annualRate / 100 / 12;
    const emi = (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) / 
                (Math.pow(1 + monthlyRate, months) - 1);
    
    return emi.toFixed(2);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    const newFormData = {
      ...formData,
      [name]: value
    };
    
    // Auto-calculate EMI when loan amount, tenure, or interest rate changes
    if (['loan_amount', 'loan_tenure', 'interest_rate'].includes(name)) {
      const calculatedEMI = calculateEMI(
        newFormData.loan_amount,
        newFormData.loan_tenure,
        newFormData.interest_rate
      );
      newFormData.monthly_emi = calculatedEMI;
    }
    
    setFormData(newFormData);
    
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Validate loan amount
    if (!formData.loan_amount || Number(formData.loan_amount) <= 0) {
      newErrors.loan_amount = 'Loan amount must be positive';
    }

    // Validate loan tenure
    if (!formData.loan_tenure || Number(formData.loan_tenure) <= 0) {
      newErrors.loan_tenure = 'Loan tenure must be positive';
    }

    // Validate interest rate
    const rate = Number(formData.interest_rate);
    if (!formData.interest_rate || rate < 0 || rate > 50) {
      newErrors.interest_rate = 'Interest rate must be between 0 and 50%';
    }

    // Validate monthly EMI
    if (!formData.monthly_emi || Number(formData.monthly_emi) <= 0) {
      newErrors.monthly_emi = 'Monthly EMI must be positive';
    }

    // Validate dates
    if (!formData.loan_start_date) {
      newErrors.loan_start_date = 'Start date is required';
    }

    if (!formData.loan_maturity_date) {
      newErrors.loan_maturity_date = 'Maturity date is required';
    }

    // Validate maturity date is after start date
    if (formData.loan_start_date && formData.loan_maturity_date) {
      const startDate = new Date(formData.loan_start_date);
      const maturityDate = new Date(formData.loan_maturity_date);
      
      if (maturityDate <= startDate) {
        newErrors.loan_maturity_date = 'Maturity date must be after start date';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Convert to proper types and format dates
    const data = {
      loan_type: formData.loan_type,
      loan_amount: Number(formData.loan_amount),
      loan_tenure: Number(formData.loan_tenure),
      monthly_emi: Number(formData.monthly_emi),
      interest_rate: Number(formData.interest_rate),
      loan_start_date: new Date(formData.loan_start_date).toISOString(),
      loan_maturity_date: new Date(formData.loan_maturity_date).toISOString()
    };
    
    onSubmit(data);
  };

  const loanTypes = [
    { value: 'personal', label: 'Personal Loan', icon: 'solar:user-circle-linear', color: 'cyan' },
    { value: 'home', label: 'Home Loan', icon: 'solar:home-2-linear', color: 'purple' },
    { value: 'auto', label: 'Auto Loan', icon: 'solar:bus-linear', color: 'blue' },
    { value: 'education', label: 'Education Loan', icon: 'solar:book-linear', color: 'green' }
  ];

  return (
    <form onSubmit={handleSubmit} className="loan-form space-y-6">
      {/* Loan Type Selection */}
      <div className="space-y-2">
        <label className="text-[10px] uppercase tracking-widest text-white/40 font-medium">
          Loan Type
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {loanTypes.map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, loan_type: type.value }))}
              className={`relative p-4 rounded-lg border transition-all ${
                formData.loan_type === type.value
                  ? `border-${type.color}-500 bg-${type.color}-500/10`
                  : 'border-white/10 bg-[#0a0a0a] hover:border-white/20'
              }`}
            >
              <iconify-icon 
                icon={type.icon} 
                width="24" 
                className={`mb-2 ${formData.loan_type === type.value ? `text-${type.color}-400` : 'text-white/40'}`}
              ></iconify-icon>
              <div className={`text-sm font-medium ${formData.loan_type === type.value ? 'text-white' : 'text-white/60'}`}>
                {type.label}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Form Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Loan Amount */}
        <div className="space-y-2">
          <label htmlFor="loan_amount" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
            <iconify-icon icon="solar:wallet-money-linear" width="14" className="text-cyan-400"></iconify-icon>
            Loan Amount
          </label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 text-sm font-mono">₹</span>
            <input
              type="number"
              id="loan_amount"
              name="loan_amount"
              value={formData.loan_amount}
              onChange={handleChange}
              placeholder="100000"
              min="0"
              step="1000"
              className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-3 pl-8 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 font-mono ${
                errors.loan_amount ? 'border-red-500/50' : 'border-white/10'
              }`}
            />
          </div>
          {errors.loan_amount && (
            <p className="text-xs text-red-400">{errors.loan_amount}</p>
          )}
        </div>

        {/* Loan Tenure */}
        <div className="space-y-2">
          <label htmlFor="loan_tenure" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
            <iconify-icon icon="solar:calendar-linear" width="14" className="text-purple-400"></iconify-icon>
            Loan Tenure (Months)
          </label>
          <input
            type="number"
            id="loan_tenure"
            name="loan_tenure"
            value={formData.loan_tenure}
            onChange={handleChange}
            placeholder="36"
            min="1"
            className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 font-mono ${
              errors.loan_tenure ? 'border-red-500/50' : 'border-white/10'
            }`}
          />
          {errors.loan_tenure && (
            <p className="text-xs text-red-400">{errors.loan_tenure}</p>
          )}
        </div>

        {/* Monthly EMI */}
        <div className="space-y-2">
          <label htmlFor="monthly_emi" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
            <iconify-icon icon="solar:card-linear" width="14" className="text-orange-400"></iconify-icon>
            Monthly EMI
            <span className="text-[8px] text-cyan-400 font-mono">(Auto-calculated)</span>
          </label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 text-sm font-mono">₹</span>
            <input
              type="number"
              id="monthly_emi"
              name="monthly_emi"
              value={formData.monthly_emi}
              readOnly
              placeholder="Auto-calculated"
              className="w-full bg-[#0a0a0a] border rounded-lg px-4 py-3 pl-8 text-sm text-white/60 placeholder-white/20 focus:outline-none border-white/10 transition-all duration-200 font-mono cursor-not-allowed opacity-75"
            />
          </div>
          {errors.monthly_emi && (
            <p className="text-xs text-red-400">{errors.monthly_emi}</p>
          )}
        </div>

        {/* Interest Rate */}
        <div className="space-y-2">
          <label htmlFor="interest_rate" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
            <iconify-icon icon="solar:chart-2-linear" width="14" className="text-green-400"></iconify-icon>
            Interest Rate (%)
          </label>
          <input
            type="number"
            id="interest_rate"
            name="interest_rate"
            value={formData.interest_rate}
            onChange={handleChange}
            placeholder="10.5"
            min="0"
            max="50"
            step="0.1"
            className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 font-mono ${
              errors.interest_rate ? 'border-red-500/50' : 'border-white/10'
            }`}
          />
          {errors.interest_rate && (
            <p className="text-xs text-red-400">{errors.interest_rate}</p>
          )}
        </div>

        {/* Loan Start Date */}
        <div className="space-y-2">
          <label htmlFor="loan_start_date" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
            <iconify-icon icon="solar:calendar-mark-linear" width="14" className="text-blue-400"></iconify-icon>
            Start Date
          </label>
          <input
            type="date"
            id="loan_start_date"
            name="loan_start_date"
            value={formData.loan_start_date}
            onChange={handleChange}
            className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 ${
              errors.loan_start_date ? 'border-red-500/50' : 'border-white/10'
            }`}
          />
          {errors.loan_start_date && (
            <p className="text-xs text-red-400">{errors.loan_start_date}</p>
          )}
        </div>

        {/* Loan Maturity Date */}
        <div className="space-y-2">
          <label htmlFor="loan_maturity_date" className="text-[10px] uppercase tracking-widest text-white/40 font-medium flex items-center gap-2">
            <iconify-icon icon="solar:calendar-mark-linear" width="14" className="text-pink-400"></iconify-icon>
            Maturity Date
          </label>
          <input
            type="date"
            id="loan_maturity_date"
            name="loan_maturity_date"
            value={formData.loan_maturity_date}
            onChange={handleChange}
            className={`w-full bg-[#0a0a0a] border rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 ${
              errors.loan_maturity_date ? 'border-red-500/50' : 'border-white/10'
            }`}
          />
          {errors.loan_maturity_date && (
            <p className="text-xs text-red-400">{errors.loan_maturity_date}</p>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3 pt-4">
        <button
          type="submit"
          disabled={loading}
          className="relative flex-1 group overflow-hidden rounded-lg bg-white py-3 transition-all hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span className="relative z-10 flex items-center justify-center gap-2 text-sm font-semibold text-black">
            {loading ? (
              <>
                <iconify-icon icon="svg-spinners:ring-resize" width="18"></iconify-icon>
                {initialData ? 'Updating...' : 'Creating...'}
              </>
            ) : (
              <>
                <iconify-icon icon="solar:check-circle-linear" width="18"></iconify-icon>
                {initialData ? 'Update Loan' : 'Create Loan'}
              </>
            )}
          </span>
        </button>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-6 py-3 rounded-lg border border-white/10 text-sm font-semibold text-white/60 hover:text-white hover:border-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mt-6">
        <div className="flex gap-3">
          <iconify-icon icon="solar:info-circle-linear" width="20" className="text-blue-400 flex-shrink-0 mt-0.5"></iconify-icon>
          <div className="text-sm text-blue-400/80">
            <p className="font-medium mb-1">EMI Calculation</p>
            <p className="text-xs text-blue-400/60">
              The monthly EMI is automatically calculated using the standard loan formula based on your loan amount, tenure, and interest rate. This ensures accuracy and compliance with banking standards.
            </p>
          </div>
        </div>
      </div>
    </form>
  );
};

export default LoanForm;
